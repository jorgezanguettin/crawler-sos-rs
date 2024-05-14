import scrapy


class SosrsSpider(scrapy.Spider):
    name = "sosrs"
    domain = "https://api.sos-rs.com/"

    def start_requests(self):
        yield from self.request_api()

    def request_api(self, page=1):
        yield scrapy.Request(
            url=f"{self.domain}shelters?orderBy=updatedAt&order=desc&search=search%3D%26priority%3D&page={page}&perPage=50",
            callback=self.parse_request_api,
            meta={
                "page": page
            }
        )

    def parse_request_api(self, response):
        data = response.json()

        shelters = data["data"]["results"]

        for shelter in shelters:
            yield shelter

        """
        if shelters:
            yield from self.request_api(
                response.meta["page"] + 1
            )
        """
