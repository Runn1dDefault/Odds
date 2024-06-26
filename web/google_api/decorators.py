import time
import functools
from logging import getLogger
from random import randint

from googleapiclient.errors import HttpError
from httplib2 import ServerNotFoundError

from config import GOOGLE_MIN_BACKOFF_TIME, GOOGLE_MAX_BACKOFF_TIME


def retry_with_backoff(func):
    logger = getLogger('GoogleBackoff')

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal logger

        minimum_backoff_time = GOOGLE_MIN_BACKOFF_TIME
        pipe_err_count = 0

        while True:
            try:
                return func(*args, **kwargs)
            except (ConnectionResetError, ServerNotFoundError):
                time.sleep(5)
                continue
            except BrokenPipeError as bpe:
                time.sleep(5)
                pipe_err_count += 1
                if pipe_err_count == 2:
                    raise bpe
            except HttpError as http_error:
                if http_error.status_code != 429:
                    raise http_error

                if minimum_backoff_time > GOOGLE_MAX_BACKOFF_TIME:
                    raise http_error

                delay = minimum_backoff_time + randint(0, 1000) / 1000.0
                logger.warning('Error 429 backoff delay is ' + delay)
                time.sleep(delay)
                minimum_backoff_time *= 2

    return wrapper
