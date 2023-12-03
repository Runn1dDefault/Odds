import logging
import time
from datetime import datetime, timedelta

import numpy as np
import pytz
import pandas as pd
from celery.app import task
from psycopg2 import connect
from scrapyd_api import ScrapydAPI

from config import SCRAPYD_URL, SCRAPYD_USERNAME, SCRAPYD_PWD, LOG_LEVEL, LOG_FORMAT
from db.connections import db, DB_PARAMS
from db.models.event import BookmakerEvent, MatchesEvent, ExchangeEvent
from managers.constants import EXCHANGE_EVENTS_QUERY, BOOKMAKER_EVENTS_QUERY, RESULTS_WATCH_MINUTES, \
    BACK_WATCH_MINUTES, MATCHING_WAIT_SECONDS, TASKS_WAIT_MINUTES, FIELDS
from matching.types import Pair

from google_api.launchers import SpreadSheetWriter


class BaseSpidersLauncher:
    JOB_STATUS_LIMIT: int = 1
    SPIDERS_OVER_STATUSES = ('finished',)

    def __init__(self, project_name: str = 'default'):
        self.logger = logging.Logger(self.__class__.__name__)
        self.logger.setLevel(LOG_LEVEL)
        formatter = logging.Formatter(LOG_FORMAT)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        self.project_name = project_name
        self.scrapyd = ScrapydAPI(SCRAPYD_URL, auth=(SCRAPYD_USERNAME, SCRAPYD_PWD))

    def wait_spider(self, job_id: str):
        status = None

        while status not in self.SPIDERS_OVER_STATUSES:
            status = self.scrapyd.job_status(self.project_name, job_id)
            time.sleep(self.JOB_STATUS_LIMIT)

    def _waiting_for_spiders_finish(self) -> None:
        pass

    def _start_spiders(self) -> None:
        pass

    def run(self):
        self.logger.info('Starting spiders...')
        self._start_spiders()
        self.logger.info('Waiting spiders...')
        start_time = datetime.utcnow()
        self._waiting_for_spiders_finish()
        end_time = datetime.utcnow()
        return start_time, end_time


class MultySpidersLauncher(BaseSpidersLauncher):
    def __init__(self, spiders: set[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spiders = spiders
        self._job_ids = {}

    def _waiting_for_spiders_finish(self) -> None:
        assert self._job_ids

        for job_id in self._job_ids.values():
            self.wait_spider(job_id)

    def _start_spiders(self):
        for spider in self.spiders:
            job_id = self.scrapyd.schedule(self.project_name, spider)
            self._job_ids[spider] = job_id


class PairSaverLauncher:
    def __init__(self, start_time: datetime, end_time: datetime, sheet_name: str, pair: Pair, matching_task: task):
        self.logger = logging.Logger(self.__class__.__name__)
        self.logger.setLevel(LOG_LEVEL)
        formatter = logging.Formatter(LOG_FORMAT)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        self.start_time, self.end_time = start_time, end_time
        self.pair = pair
        self.sheet_name = sheet_name
        self.matching_task = matching_task
        self.spread_sheet_saver = SpreadSheetWriter(fields=FIELDS)

    def run(self) -> None:
        self.logger.info("Scraping time is %s" % (str(self.end_time - self.start_time)))
        self.logger.info('Start matching scraped results...')

        with connect(**DB_PARAMS) as conn:
            exchange_query = EXCHANGE_EVENTS_QUERY % (self.start_time, self.end_time, self.pair.exchange.value)
            exc_df = pd.read_sql_query(exchange_query, conn).replace({np.nan: None})

            bookmaker_query = BOOKMAKER_EVENTS_QUERY % (self.start_time, self.end_time, self.pair.bookmaker.value)
            bm_df = pd.read_sql_query(bookmaker_query, conn).replace({np.nan: None})

        bm_events_json = bm_df.to_json(orient='records')
        # run matching tasks
        tasks = [self.matching_task.apply_async(args=(exc_event_data, bm_events_json))
                 for exc_event_data in exc_df.to_dict(orient='records')]

        self.write_results()
        self._all_tasks_waited(tasks)
        self._save_not_matched_events(self.start_time, self.end_time)
        self.logger.info('Over')

    def write_results(self, disposable: bool = False) -> None:
        last_sheet_row = 0
        first_writing = True
        match_events, handled_match_names = [], set()
        over_time = datetime.utcnow() + timedelta(minutes=RESULTS_WATCH_MINUTES if disposable is False else 1)

        while datetime.utcnow() < over_time:
            self.logger.info('search events for write to spreadsheet...')
            with db:
                for event in MatchesEvent.select().where(
                        (MatchesEvent.created_at >= datetime.utcnow() - timedelta(minutes=BACK_WATCH_MINUTES)) &
                        (MatchesEvent.exchange == self.pair.exchange.value) &
                        (MatchesEvent.bookmaker == self.pair.bookmaker.value)
                ).order_by(MatchesEvent.created_at.desc(), MatchesEvent.lay.asc(), MatchesEvent.odds.asc()):
                    if event.exchange_match_name in handled_match_names:
                        continue

                    teams = event.exchange_match_name.split(' vs ')
                    if len(teams) != 2:
                        self.logger.error('Unpacked match name %s ' % event.exchange_match_name)
                        continue

                    first_team, second_team = teams
                    matched_time = event.created_at.astimezone(pytz.timezone("Etc/GMT")).strftime('%Y-%m-%dT%H:%M:%S')

                    match = dict(
                        bet=event.bet,
                        first_team=first_team,
                        second_team=second_team,
                        matched_time=matched_time,
                        match_name=event.exchange_match_name,
                        category=event.category,
                        bookmaker=event.bookmaker,
                        odds=event.odds,
                        exchange=event.exchange,
                        lay=event.lay,
                        similarity_ft=event.similarity_by_first_teams,
                        similarity_st=event.similarity_by_second_teams,
                        total_similarity=event.total_similarity
                    )
                    match_events.append(match)
                    handled_match_names.add(event.exchange_match_name)

            if match_events:
                founded_events_count = len(match_events)
                self.logger.info('Saving founded events %s to spreadsheet...' % founded_events_count)

                if first_writing:
                    self.spread_sheet_saver.rewrite_to_sheet(sheet_name=self.sheet_name, data=match_events)
                    last_sheet_row = founded_events_count + 2
                    first_writing = False
                else:
                    spreadsheet_meta = self.spread_sheet_saver.gsp_client.get_sheet_meta(self.sheet_name)
                    spreadsheet_rows_count = spreadsheet_meta.get('gridProperties', {}).get('rowCount', 1000)

                    if last_sheet_row + founded_events_count >= spreadsheet_rows_count:
                        self.spread_sheet_saver.gsp_client.add_new_rows(sheet_name=self.sheet_name)

                    self.spread_sheet_saver.write_to_sheet(sheet_name=self.sheet_name, data=match_events,
                                                           a1_range=f'A{last_sheet_row}:Z')
                    last_sheet_row += founded_events_count

                self.logger.info('Successfully added events %s' % founded_events_count)
                match_events.clear()

            self.logger.info('waiting %s seconds...' % MATCHING_WAIT_SECONDS)
            time.sleep(MATCHING_WAIT_SECONDS)

    def _all_tasks_waited(self, tasks) -> bool:
        if not tasks:
            return False

        self.logger.info('Waiting all started tasks...')
        over_time = datetime.utcnow() + timedelta(minutes=TASKS_WAIT_MINUTES)

        waited = False
        start_time = time.time()
        # waiting all tasks completing
        while tasks:
            if datetime.utcnow() >= over_time:
                passed_time = time.time() - start_time
                self.logger.debug('Over time! %s seconds have passed' % passed_time)
                break

            for matching_task in tasks:
                if matching_task.state in ('SUCCESS', 'FAILURE', 'RETRY'):
                    tasks.remove(matching_task)

        if not tasks:
            waited = True

        self.logger.info('Over waiting tasks')
        return waited

    def _save_not_matched_events(self, start_time: datetime, end_time: datetime) -> None:
        self.logger.info('Start searching not matched events..')
        not_matched_data = []
        with db:
            exc_not_matches_query = ExchangeEvent.not_matches_query(
                exchange=str(self.pair.exchange.value),
                start_time=start_time,
                end_time=end_time,
            ).where(
                ExchangeEvent.match_name.not_in(MatchesEvent.select(MatchesEvent.exchange_match_name)
                                                .where((MatchesEvent.created_at >= start_time) &
                                                       (MatchesEvent.created_at <= end_time)))
            )
            bm_not_matches_query = BookmakerEvent.not_matches_query(
                bookmaker=str(self.pair.bookmaker.value),
                start_time=start_time,
                end_time=end_time
            ).where(
                BookmakerEvent.match_name.not_in(
                    MatchesEvent.select(MatchesEvent.bookmaker_match_name)
                    .where((MatchesEvent.created_at >= start_time) &
                           (MatchesEvent.created_at <= end_time))
                )
            )
            not_matched_data.extend(self._get_not_matches_list(exc_not_matches_query))
            not_matched_data.extend(self._get_not_matches_list(bm_not_matches_query))

        if not_matched_data:
            self.logger.info('Trying save not matched events %s...' % len(not_matched_data))
            self.spread_sheet_saver.rewrite_to_sheet(sheet_name='Not matched events', data=not_matched_data)

    @staticmethod
    def _get_not_matches_list(events) -> list[dict[str, str | datetime | float]]:
        send_matches = []
        not_matches = []

        for event in events:
            if event.match_name in send_matches:
                continue

            event_data = dict(
                first_team=event.first_team,
                secont_team=event.second_team,
                matched_time=datetime.utcnow(),
                match_name=event.match_name,
                category=event.category
            )
            if isinstance(event, ExchangeEvent):
                event_data |= dict(exchange=event.exchange, lay=event.lay)
            elif isinstance(event, BookmakerEvent):
                event_data |= dict(bookmaker=event.bookmaker, odds=event.odds)

            send_matches.append(event.match_name)
            not_matches.append(event_data)
        return not_matches
