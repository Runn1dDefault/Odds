import json
from datetime import datetime

import redis
from celery import Celery
from celery.schedules import crontab
from pandas import read_json

from config import REDIS_URL, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
from db.connections import db
from matching.matchers import SimilarityExchangeMatcher
from matching.types import Pair
from managers.launchers import PairSaverLauncher, MultySpidersLauncher


app = Celery('OddsTasks', broker=REDIS_URL, backend=REDIS_URL)
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=1, password=REDIS_PASSWORD)
MATCHES_SAVE_LIST_NAME = 'matched_events_to_save'


@app.task()
def saving_items_to_model_from_redis_list(redis_list, model_path: str) -> bool:
    data_json = redis_client.lrange(redis_list, 0, -1)
    if not data_json:
        print('Not found data for saving!')
        return False

    assert '.' in model_path

    package = model_path.split('.')
    model_name = package[-1]
    mod = __import__('.'.join(package[:-1]), fromlist=[model_name])
    model = getattr(mod, model_name)

    data_source = [model(**json.loads(event)) for event in data_json]
    with db.atomic():
        model.bulk_create(data_source)
        # model.insert_many(data_source).execute()

    redis_client.delete(redis_list)
    print('Saved to %s count: %s' % (model_name, len(data_source)))
    return True


@app.task()
def matching_exchange_event(exc_event_data: dict, bm_events_json: str):
    bm_events_df = read_json(bm_events_json)
    matcher = SimilarityExchangeMatcher(exchange_data=exc_event_data, bm_events_df=bm_events_df)
    matched_data = matcher.make_matching()
    if matched_data is None:
        return

    matched_bm_event = matched_data['bm_event_data']
    matches_event_json = json.dumps(dict(
        bet=exc_event_data['bet'],
        category=exc_event_data['category'],
        exchange=exc_event_data['exchange'],
        exchange_match_name=exc_event_data['match_name'],
        lay=exc_event_data['lay'],
        bookmaker=matched_bm_event['bookmaker'],
        bookmaker_match_name=matched_bm_event['match_name'],
        odds=matched_bm_event['odds'],
        similarity_by_first_teams=matched_data['similarity_by_first_teams'],
        similarity_by_second_teams=matched_data['similarity_by_second_teams']
    ))

    redis_client.rpush(MATCHES_SAVE_LIST_NAME, matches_event_json)


@app.task()
def pair_launch(sheet_name: str, exchange: str, bookmaker: str, save_from_redis: bool = False):
    pair = Pair(exchange=exchange, bookmaker=bookmaker)
    spiders_launcher = MultySpidersLauncher(spiders={exchange, bookmaker})

    start_time, end_time = spiders_launcher.run()

    if save_from_redis:
        for redis_list, model_path in {
            'bookmaker_events': 'db.models.event.BookmakerEvent',
            'exchange_events': 'db.models.event.ExchangeEvent'
        }.items():
            saving_items_to_model_from_redis_list(redis_list, model_path)

        end_time = datetime.utcnow()

    PairSaverLauncher(
        start_time=start_time,
        end_time=end_time,
        sheet_name=sheet_name,
        pair=pair,
        matching_task=matching_exchange_event
    ).run()


@app.task()
def update_spiders_maps(map_spiders: list[str]):
    MultySpidersLauncher(spiders=set(map_spiders)).run()


app.conf.beat_schedule = {
    'saving_matches_task': {
        'schedule': 3.0,
        'task': 'tasks.saving_items_to_model_from_redis_list',
        'args': (MATCHES_SAVE_LIST_NAME, 'db.models.event.MatchesEvent')
    },
    'spiders_maps_update_task': {
        'schedule': crontab(minute=0, hour='*/3'),
        'task': 'tasks.update_spiders_maps',
        'args': (['bet99_map'],)
    }
}

app.conf.timezone = 'UTC'
