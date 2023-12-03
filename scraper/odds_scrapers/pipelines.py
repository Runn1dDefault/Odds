import json
from datetime import datetime

import psycopg2
from redis.client import Redis
from scrapy import signals
from scrapy.exceptions import DropItem
from psycopg2 import sql


class DefaultValuesPipeline(object):
    def process_item(self, item, spider):
        item.setdefault('created_at', datetime.utcnow())
        return item


class RedisListPipeLine:
    def __init__(self, redis_settings):
        self.redis_settings = redis_settings
        self.redis_client = None

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls(crawler.settings.getdict("REDIS_SETTINGS"))
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        self.redis_client = Redis(
            host=self.redis_settings['HOST'],
            port=self.redis_settings['PORT'],
            db=self.redis_settings['DB'],
            password=self.redis_settings['PASSWORD']
        )

    def spider_closed(self, spider):
        self.redis_client.connection_pool.disconnect()

    def process_item(self, item, spider):
        redis_list = spider.custom_settings.get('REDIS_LIST')
        if isinstance(redis_list, str):
            data = dict(item)
            spider.logger.info(data)
            self.redis_client.rpush(redis_list, json.dumps(data))
            spider.logger.debug('Added event to redis list %s' % redis_list)
        return item


class PostgresPipeline:
    def __init__(self, db_settings):
        self.db_settings = db_settings
        self.connection = None
        self.cursor = None

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls(crawler.settings.getdict("DB_SETTINGS"))
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        self.connection = psycopg2.connect(
            host=self.db_settings["HOST"],
            port=self.db_settings["PORT"],
            dbname=self.db_settings["DB_NAME"],
            user=self.db_settings["USER"],
            password=self.db_settings["PASSWORD"],
        )
        self.cursor = self.connection.cursor()

    def spider_closed(self, spider):
        self.connection.close()

    def process_item(self, item, spider):
        if self.connection is None:
            return item

        assert spider.custom_settings.get('TABLE_NAME')
        try:
            insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(spider.custom_settings['TABLE_NAME']),
                sql.SQL(', ').join(map(sql.Identifier, item.keys())),
                sql.SQL(', ').join(sql.Placeholder() * len(item))
            )
            self.cursor.execute(insert_query, list(item.values()))
            self.connection.commit()
            return item
        except Exception as e:
            self.connection.rollback()
            raise DropItem(f"Failed to insert item into PostgreSQL: {e}")
