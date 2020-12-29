from datetime import datetime

import time
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message


class TooManyRequestsRetryMiddleware(RetryMiddleware):
    def __init__(self, crawler):
        super(TooManyRequestsRetryMiddleware, self).__init__(crawler.settings)
        self.crawler = crawler
        self.last429Error = datetime.now()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response

        if response.status == 429:  # Too many requests
            secondsSinceLast429Error = (datetime.now() - self.last429Error).total_seconds()

            self.crawler.engine.pause()

            if secondsSinceLast429Error > 70:
                time.sleep(60)  # Sleep 60 seconds.
            else:
                time.sleep(60 * 60)  # Sleep 1 hour.

            self.crawler.engine.unpause()
            self.last429Error = datetime.now()

        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response

        return response