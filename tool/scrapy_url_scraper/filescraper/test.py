# run_spider.py

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from spiders.filetype_spider import FileTypeSpider

def run(start_url: str, file_type: str):
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(FileTypeSpider, start_url=start_url, file_type=file_type)
    process.start()

if __name__ == "__main__":
    run("https://abc.xyz/investor/", "pdf")
