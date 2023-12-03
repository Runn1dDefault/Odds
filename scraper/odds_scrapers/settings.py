import os
from pathlib import Path


BOT_NAME = 'odds_scrapers'

SPIDER_MODULES = ['odds_scrapers.spiders']
NEWSPIDER_MODULE = 'odds_scrapers.spiders'

ROBOTSTXT_OBEY = False

DB_SETTINGS = {
   'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
   'PORT': int(os.environ.get('POSTGRES_PORT', 5432)),
   'DB_NAME': os.environ.get('POSTGRES_DB', 'postgres'),
   'USER': os.environ.get('POSTGRES_USER', 'postgres'),
   'PASSWORD': os.environ.get('POSTGRES_PASSWORD', '')
}

REDIS_SETTINGS = {
   'HOST': os.environ.get('REDIS_HOST', 'localhost'),
   'PORT': int(os.environ.get('REDIS_PORT', 6379)),
   'DB': 1,
   'PASSWORD': os.environ.get('REDIS_PASSWORD', '')
}

SCRAPY_SPLASH_HOST = os.environ.get('SCRAPY_SPLASH_HOST', 'localhost')
SCRAPY_SPLASH_PORT = int(os.environ.get('SCRAPY_SPLASH_PORT', 8050))

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
SPLASH_URL = f'http://{SCRAPY_SPLASH_HOST}:{SCRAPY_SPLASH_PORT}'

MAPS_DIR = os.path.join(Path(__file__).parent.parent, 'sites_maps')
