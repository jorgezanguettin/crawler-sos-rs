import functions_framework
from sosriograndedosul.spiders.sosrs import SosrsSpider
from sosriograndedosul.spiders.ajuders import AjudeRSSpider
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


@functions_framework.http
def lambda_handler(request):
    settings = get_project_settings()

    process = CrawlerProcess(settings)
    process.crawl(SosrsSpider)
    process.crawl(AjudeRSSpider)
    process.start()

    return "Trigger Success"
