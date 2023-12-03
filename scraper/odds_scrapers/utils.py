import json
import os
from datetime import datetime, timedelta
from json import JSONDecodeError
from logging import Logger

from odds_scrapers.settings import MAPS_DIR


def get_url_times(time_format: str, delta: timedelta) -> tuple[str, str]:
    today = datetime.utcnow()
    start_time = today.strftime(time_format).replace(':', '%3A')
    end_time = (today + delta).strftime(time_format).replace(':', '%3A')
    return start_time, end_time


def load_json_file(filepath: str) -> list[dict] | dict | None:
    if not os.path.exists(filepath):
        return

    with open(filepath) as json_file:
        try:
            data = json.load(json_file)
            return data
        except JSONDecodeError:
            return


def get_category_by_id(category_id: str) -> str:
    categories_data = load_json_file(os.path.join(MAPS_DIR, 'categories.json'))
    return categories_data.get(category_id)


def get_response_json(response, logger: Logger) -> list | dict:
    assert hasattr(response, 'json')

    try:
        response_data = response.json()
    except JSONDecodeError:
        logger.critical(
            'Request to URL %s not returned json!' % response.url
        )
    else:
        return response_data
