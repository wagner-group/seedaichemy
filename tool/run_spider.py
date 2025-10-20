import os
from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
from tool.scrapy_url_scraper.filescraper.spiders.filetype_spider import FileTypeSpider  # your spider module

def run_scrapy(start_urls: list, file_type: str, download_dir: str = "downloads", disable_checks: bool = False):
    # ensure download_dir is writable and exists
    download_dir = os.path.abspath(download_dir)
    os.makedirs(download_dir, exist_ok=True)

    # configure logging to show Scrapy INFO logs
    configure_logging({'LOG_LEVEL': 'INFO'})

    # inline Scrapy settings
    settings = {
        'BOT_NAME': 'standalone_crawler',
        'ROBOTSTXT_OBEY': True,               
        # pretend to be a real browser (many PDF servers block default UA)
        'USER_AGENT': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/115.0.0.0 Safari/537.36'
        ),

        'ITEM_PIPELINES': {
            'scrapy.pipelines.files.FilesPipeline': 1,
        },
        'FILES_STORE': download_dir,            # where to drop your files
        'HTTPERROR_ALLOW_ALL': True,            # let you see non-200 responses
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 2,
        'CONCURRENT_REQUESTS': 32,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 0.5,
        'AUTOTHROTTLE_MAX_DELAY': 5,
    }

    process = CrawlerProcess(settings)
    process.crawl(FileTypeSpider, start_urls = start_urls, file_type=file_type, disable_checks=disable_checks)
    process.start()  # blocks until finished

if __name__ == "__main__":
    run_scrapy(
        start_urls=["https://abc.xyz/investor/", 
                    "https://controller.berkeley.edu/accounting-and-controls/financial-reporting/uc-berkeley-financial-reports-unaudited"],
        file_type="pdf",
        download_dir="./my_downloads"
    )