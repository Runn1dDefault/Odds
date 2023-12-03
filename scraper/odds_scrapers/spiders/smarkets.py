import os.path

from urllib.parse import urljoin

import scrapy
from scrapy.loader import ItemLoader
from scrapy_splash import SplashRequest

from odds_scrapers.settings import MAPS_DIR
from odds_scrapers.items import Exchange
from odds_scrapers.utils import load_json_file, get_category_by_id
from odds_scrapers.constants import SMARKETS_BASE_URL, SMARKETS_SUBCATEGORIES_XPATH, SMARKETS_PAGE_ADDITIONS_TABS, \
    SMARKETS_TEAM_XPATH, SMARKETS_EVENTS_XPATH, SMARKETS_CONTRACTS_XPATH, SMARKETS_LAY_XPATH


class SmarketsSpider(scrapy.Spider):
    name = 'smarkets'
    custom_settings = {
        'LOG_LEVEL': 'INFO',
        'REDIS_LIST': 'exchange_events',
        'ITEM_PIPELINES': {
            'odds_scrapers.pipelines.RedisListPipeLine': 301,
        },
        'DOWNLOAD_FAIL_ON_DATALOSS': False,
        'DOWNLOADER_MIDDLEWARES': {
            'odds_scrapers.middlewares.IgnoreUrlsMiddleware': 543,
            'scrapy_splash.SplashCookiesMiddleware': 723,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
        },
        'URLS_TO_IGNORE': [
            'https://smarkets.com/listing/sport/football/england-premier-league',
            'https://smarkets.com/listing/sport/football/outright',
            'premier-league'
        ],
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage'
    }
    SMARKETS_MAP = load_json_file(os.path.join(MAPS_DIR, 'smarkets_map.json'))
    events_count = 0

    def start_requests(self):
        for category_data in self.SMARKETS_MAP or []:
            category_id = category_data.get('categoryID')
            assert isinstance(category_id, str) and category_id.isdigit()

            url = category_data.get('categoryURL')
            assert isinstance(url, str) and SMARKETS_BASE_URL in url

            category_data['categoryTitle'] = get_category_by_id(category_id)
            yield SplashRequest(
                url=url,
                callback=self.parse,
                meta={
                    'category_data': category_data,
                    'args': {
                        'html': 1,
                        'wait': 0.15
                    }
                }
            )

    def parse(self, response, **kwargs):
        cookies = {'odds-format': 'decimal'}

        for subcategory_url_path in response.xpath(SMARKETS_SUBCATEGORIES_XPATH).getall():
            yield SplashRequest(
                url=urljoin(SMARKETS_BASE_URL, subcategory_url_path),
                callback=self.parse_items,
                meta=response.meta,
                # so that the value of the odds field is in decimal
                # and not the default in US dollars
                cookies=cookies,
                dont_filter=False  # !important
            )

        yield from self.parse_additional_tabs(response)

    def parse_items(self, response):
        category_data = response.meta['category_data']
        category = category_data['categoryTitle']
        events = response.xpath(SMARKETS_EVENTS_XPATH).getall()
        self.events_count += len(events)

        for event in events:
            event_selector = scrapy.Selector(text=event)
            contracts = event_selector.xpath(SMARKETS_CONTRACTS_XPATH).getall()
            teams = {}

            for contract in contracts:
                contract_selector = scrapy.Selector(text=contract)

                team = contract_selector.xpath(SMARKETS_TEAM_XPATH).get()
                if not team:
                    continue

                lay_value = contract_selector.xpath(SMARKETS_LAY_XPATH).get()
                teams[team] = lay_value if lay_value else None

            event_url = event_selector.xpath('//a[@class="overlay"]/@href').get()
            contracts = list(teams.keys())

            match len(contracts):
                case 2 if 'Draw' not in teams:
                    first_team, second_team = map(lambda x: x.strip(), contracts)
                case 3 if 'Draw' in teams:
                    first_team, draw, second_team = map(lambda x: x.strip(), contracts)
                    yield self._build_item(
                        bet=draw,
                        first_team=first_team,
                        second_team=second_team,
                        lay=teams[draw],
                        event_url=event_url,
                        category=category
                    )
                case _:
                    self.logger.error('Passed teams %s URL: %s' % (teams, event_url))
                    continue

            if first_team and second_team:
                yield self._build_item(
                    bet=first_team,
                    first_team=first_team,
                    second_team=second_team,
                    lay=teams[first_team],
                    event_url=event_url,
                    category=category
                )
                yield self._build_item(
                    bet=second_team,
                    first_team=second_team,
                    second_team=first_team,
                    lay=teams[second_team],
                    event_url=event_url,
                    category=category
                )

        # # in case they have nested categories
        # # it is very important that the check for duplicates is enabled in the parse method
        yield from self.parse(response)
        # # subcategory can contain subpages. Like: "POPULAR", "IN-PLAY", "UPCOMING", "OUTRIGHT"
        yield from self.parse_additional_tabs(response)

    def _build_item(self, bet: str, first_team: str, second_team: str, lay: str, event_url: str, category: str):
        item_loader = ItemLoader(item=Exchange())
        item_loader.add_value('bet', bet)
        item_loader.add_value('exchange', self.name)
        item_loader.add_value('lay', lay)
        item_loader.add_value('url', event_url)
        item_loader.add_value('category', category)
        item_loader.add_value('match_name', '%s vs %s' % (first_team, second_team))

        item_loader.add_value('first_team', first_team)
        item_loader.add_value('second_team', second_team)
        return item_loader.load_item()

    def parse_additional_tabs(self, response):
        tabs_urls = response.xpath(SMARKETS_PAGE_ADDITIONS_TABS).getall()

        for url_path in tabs_urls:
            yield SplashRequest(
                url=urljoin(SMARKETS_BASE_URL, url_path),
                callback=self.parse_items,
                meta=response.meta
            )
