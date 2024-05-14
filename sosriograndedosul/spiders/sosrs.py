import scrapy


class SosrsSpider(scrapy.Spider):
    name = "sosrs"
    allowed_domains = ["sos-rs.com"]
    start_urls = ["https://sos-rs.com"]

    def parse(self, response):
        pass
