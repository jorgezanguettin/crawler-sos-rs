from sosriograndedosul.spiders.ajuders import AjudeRSSpider
from scrapy.crawler import CrawlerProcess
from sosriograndedosul.pipelines import SosriograndedosulPipeline
from scrapy.utils.project import get_project_settings

settings = get_project_settings()
process = CrawlerProcess(settings)
process.crawl(AjudeRSSpider)
process.start()