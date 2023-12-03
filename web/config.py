import logging
import os.path
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).parent

STATIC = os.path.join(BASE_DIR, 'static')
MAPS_DIR = os.path.join(STATIC, 'sites_maps')

# SCRAPYD
SCRAPYD_HOST = os.environ.get('SCRAPYD_HOST', 'crawler')
SCRAPYD_PORT = int(os.environ.get('SCRAPYD_PORT', 6800))
SCRAPYD_URL = f'http://{SCRAPYD_HOST}:{SCRAPYD_PORT}/'
SCRAPYD_USERNAME = os.environ['SCRAPYD_USERNAME']
SCRAPYD_PWD = os.environ['SCRAPYD_PWD']

# SCRAPY-SPALSH
SCRAPY_SPLASH_HOST = os.environ.get('SCRAPY_SPLASH_HOST', 'localhost')
SCRAPY_SPLASH_PORT = int(os.environ.get('SCRAPY_SPLASH_PORT', 8050))


# GOOGLE
SCOPES = ('https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive')
GOOGLE_SPREADSHEET_RETRIES = int(os.environ.get('GOOGLE_SPREADSHEET_RETRIES', 1))
GOOGLE_MIN_BACKOFF_TIME = 30
GOOGLE_MAX_BACKOFF_TIME = 300  # 5 min
CREDENTIALS_JSON = os.path.join(STATIC, 'credentials.json')
SPREADSHEET_ID = '1B6ubDsstHlzdFxjSHsmWzp3sgl7nmZMgnl9hTFjjQss'

# Logging
LOG_LEVEL = logging.NOTSET
LOG_FORMAT = '[%(name)s/%(levelname)s]: %(message)s'  # it will look through celery
LOG_DIR = os.path.join(STATIC, 'logs')
if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)

# DATABASES
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'test_db')
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', '')
POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT', 5432))

# REDIS
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "pwdlocal")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0'

# TOKENS
API_KEYS = os.environ.get('API_KEYS', '').split(' ')
