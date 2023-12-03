import re

import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags


def convert_to_float(value: str | float):
    if isinstance(value, float):
        return value

    value = value.replace(',', '.')
    search_digits = re.findall(r'\d+\.\d+', value)
    if search_digits:
        return float(search_digits[0].replace(',', '.'))


class EventItem(scrapy.Item):
    first_team = scrapy.Field(
        input_processor=MapCompose(remove_tags),
        output_processor=TakeFirst(),
        serializer=str
    )
    second_team = scrapy.Field(
        input_processor=MapCompose(remove_tags),
        output_processor=TakeFirst(),
        serializer=str
    )
    match_name = scrapy.Field(
        input_processor=MapCompose(remove_tags),
        output_processor=Join(' vs '),
        serializer=str
    )
    category = scrapy.Field(
        input_processor=MapCompose(remove_tags),
        output_processor=TakeFirst(),
        serializer=str
    )
    url = scrapy.Field(
        input_processor=MapCompose(remove_tags),
        output_processor=TakeFirst(),
        serializer=str
    )
    created_at = scrapy.Field(
        input_processor=MapCompose(),
        output_processor=TakeFirst()
    )
    bet = scrapy.Field(
        input_processor=MapCompose(remove_tags),
        output_processor=TakeFirst(),
        serializer=str
    )


class Exchange(EventItem):
    exchange = scrapy.Field(
        output_processor=TakeFirst(),
        serializer=str
    )
    lay = scrapy.Field(
        input_processor=MapCompose(remove_tags, convert_to_float),
        output_processor=TakeFirst()
    )


class Bookmaker(EventItem):
    bookmaker = scrapy.Field(
        output_processor=TakeFirst(),
        serializer=str
    )
    odds = scrapy.Field(
        input_processor=MapCompose(remove_tags, convert_to_float),
        output_processor=TakeFirst()
    )
