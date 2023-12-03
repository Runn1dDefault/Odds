from scrapy.exceptions import IgnoreRequest


class IgnoreUrlsMiddleware:
    def __init__(self, urls_to_ignore):
        self.urls_to_ignore = urls_to_ignore

    @classmethod
    def from_crawler(cls, crawler):
        return cls(urls_to_ignore=crawler.settings.getlist('URLS_TO_IGNORE'))

    def process_request(self, request, spider):
        if any(url in request.url for url in self.urls_to_ignore):
            spider.logger.info(f'Ignoring URL {request.url} based on ignore list')
            raise IgnoreRequest()
