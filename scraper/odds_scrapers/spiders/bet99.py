import os.path
from datetime import timedelta
from pprint import pprint
from typing import Any

import scrapy
from scrapy.loader import ItemLoader

from odds_scrapers.settings import MAPS_DIR
from odds_scrapers.items import Bookmaker
from odds_scrapers.utils import load_json_file, get_response_json, get_url_times, get_category_by_id
from odds_scrapers.constants import BET99_EVENTS_LIST_URL, BET99_EVENT_URL, BET99_SUBCATEGORIES_URL, \
    BET99_EVENTS_TYPES_URL


class Bet99MapSpider(scrapy.Spider):
    name = 'bet99_map'
    custom_settings = {
        'LOG_LEVEL': 'INFO',
        'FEEDS': {
            os.path.join(MAPS_DIR, 'bet99_subcategories_to_parse.json'): {
                'overwrite': True,
                'format': 'json',
                'encoding': 'utf8'
            }
        }
    }
    BET99_MAP = load_json_file(os.path.join(MAPS_DIR, 'bet99_map.json'))
    TIME_FORMAT = '%Y-%m-%dT%H:%M:00.000Z'

    def start_requests(self):
        for category_data in self.BET99_MAP or []:
            start_time, end_time = get_url_times(self.TIME_FORMAT, timedelta(days=7))
            category_id = category_data.get('categoryID')
            assert isinstance(category_id, str) and category_id.isdigit()

            sport_id = category_data.get('Id')
            assert isinstance(sport_id, int)

            category_data['categoryTitle'] = get_category_by_id(category_id)
            yield scrapy.Request(
                url=BET99_SUBCATEGORIES_URL.format(sport_id=sport_id, start_time=start_time, end_time=end_time),
                callback=self.parse,
                meta=category_data
            )

    def parse(self, response, **kwargs):
        response_data = get_response_json(response, self.logger)
        if not response_data:
            return

        results = response_data.get('Result')
        if not results:
            self.logger.critical('Not found list with key Result in body of request! URL: ' + response.url)
            return

        category = response.meta['categoryTitle']
        sport_id = response.meta['Id']

        for result in results:
            subcategories_items = result.get('Items')

            if not subcategories_items:
                self.logger.debug(result.get('Name'))
                continue

            for subcategory_data in subcategories_items:
                yield from self.parse_subcategory_children(
                    sport_id=sport_id,
                    category=category,
                    subcategory_data=subcategory_data,
                    meta=response.meta
                )

    def parse_subcategory_children(self, sport_id: int, category: str, subcategory_data: dict[str, Any],
                                   meta: dict[str, Any]):
        subcategory_name = subcategory_data.get('Name')

        for subcategory_child in subcategory_data.get('Items') or []:
            match subcategory_child:
                case {
                    "ChampionshipIds": str(),
                    "Id": int() as child_id,
                    "Name": str() as child_name,
                    "EventCount": int() as event_count,
                    **other_fields
                } if event_count > 0:
                    start_time, end_time = get_url_times(self.TIME_FORMAT, timedelta(days=7))
                    self.logger.debug(
                        f'Found {category} -> {subcategory_name} -> {child_name}\nChild ID: {child_id}\n'
                        f'Events count: {event_count}...\nOther Fields: {other_fields}')

                    meta['champ_id'] = child_id
                    yield scrapy.Request(
                        url=BET99_EVENTS_TYPES_URL.format(
                            champ_ids=child_id,
                            sport_ids=sport_id,
                            start_time=start_time,
                            end_time=end_time
                        ),
                        callback=self.parse_events_by_type,
                        meta=meta
                    )
                case _:
                    self.logger.debug(subcategory_child)

    def parse_events_by_type(self, response):
        response_data = get_response_json(response, self.logger)
        if not response_data:
            return

        result = response_data.get("Result")
        if not result:
            self.logger.error('Not found Result! URL: %s' % response.url)
            return

        sport_id = response.meta['Id']
        champ_id = response.meta['champ_id']
        category = response.meta['categoryTitle']

        match result:
            case {
                "Match": bool() as is_type_match,
                "Outright": bool(),
                "SportTypeId": int()
            } if is_type_match is True:
                self.logger.info(
                    'Start parse events for category: %s sport_id: %s champ_id: %s' % (category, sport_id, champ_id)
                )
                return {
                    'category': category,
                    'champ_id': champ_id,
                    'sport_id': sport_id
                }
            case {
                "Match": bool() as is_type_match,
                "Outright": bool(),
                "SportTypeId": int()
            } if is_type_match is False:
                pass
                # for the future


class Bet99Spider(scrapy.Spider):
    name = 'bet99'
    custom_settings = {
        'LOG_LEVEL': 'INFO',
        'REDIS_LIST': 'bookmaker_events',
    }
    BET99_SUBCATEGORIES = load_json_file(os.path.join(MAPS_DIR, 'bet99_subcategories_to_parse.json'))
    TIME_FORMAT = '%Y-%m-%dT%H:%M:00.000Z'

    def start_requests(self):
        start_time, end_time = get_url_times(self.TIME_FORMAT, timedelta(days=7))

        for subcategories in self.BET99_SUBCATEGORIES or []:
            match subcategories:
                case {
                    'category': str() as category,
                    'sport_id': int() as sport_id,
                    'champ_id': int() as champ_id
                }:
                    yield scrapy.Request(
                        url=BET99_EVENTS_LIST_URL.format(
                            sport_ids=sport_id,
                            champ_ids=champ_id,
                            group='AllEvents',
                            outrights_display='none',
                            start_time=start_time,
                            end_time=end_time
                        ),
                        callback=self.parse,
                        meta={'categoryTitle': category, 'sport_id': sport_id, 'champ_id': champ_id}
                    )

    def parse(self, response, **kwargs):
        response_data = get_response_json(response, self.logger)
        if not response_data:
            self.logger.error('Not found response data! %s' % response.url)
            return

        result = response_data.get('Result')
        if not result:
            self.logger.error('Not found Result! URL: %s' % response.url)
            return

        category = response.meta['categoryTitle']

        for item in result.get('Items') or []:
            for event in item.get('Events') or []:
                match event:
                    case {
                        "Id": event_id,
                        "CategoryId": category_id,
                        "IsLiveEvent": False,
                        "Items": list() as event_fields,
                        "Name": str() as match_name,
                        "SportId": sport_id,
                        **other_event_fields
                    }:
                        self._event_fields_process(
                            fields=event_fields,
                            event_id=event_id,
                            sport_id=sport_id,
                            category=category,
                            category_id=category_id,
                            teams=match_name.split(' vs. ')
                        )

    def _event_fields_process(self, event_id, sport_id, category_id, category: str, teams: list[str],
                              fields: list[dict]):

        event_url = BET99_EVENT_URL.format(sport_id=sport_id, category_id=category_id, event_id=event_id)

        for field in fields:
            match field:
                case {
                    "Name": str() as name,
                    "Items": list() as lines,
                    "ColumnCount": int() as columns_count,
                    **other_data
                } if columns_count > 1 and name in ('Money Line', '1x2'):
                    for line in lines:
                        match line:
                            case {
                                "Name": str() as name,
                                "Price": float() | int() as odds,
                                **other_fields
                            } if name in teams or name.lower() == 'draw':
                                if teams[-1] == name:
                                    teams.reverse()

                                item_loader = ItemLoader(item=Bookmaker())
                                item_loader.add_value('bet', name)
                                item_loader.add_value('bookmaker', self.name)
                                item_loader.add_value('category', category)
                                item_loader.add_value('url', event_url)
                                item_loader.add_value('match_name', teams)
                                first_team, second_team = teams[0].strip(), teams[1].strip()
                                item_loader.add_value('first_team', first_team)
                                item_loader.add_value('second_team', second_team)
                                item_loader.add_value('odds', str(odds))
                                pprint(item_loader.load_item())

