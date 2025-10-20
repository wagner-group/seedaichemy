# spiders/filetype_spider.py
import scrapy
from urllib.parse import urlparse
from tool.scrapy_url_scraper.filescraper.items import FileTypeItem
from tool.utils import *

IMAGE_EXTS = { 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp' }

class FileTypeSpider(scrapy.Spider):
    name = "filetype_spider_with_filespipeline"

    def __init__(self, start_urls=None, file_type="", disable_checks=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Accept either a comma-separated string or a real Python list
        if isinstance(start_urls, str):
            self.start_urls = [u.strip() for u in start_urls.split(",") if u.strip()]
        elif isinstance(start_urls, list):
            self.start_urls = start_urls
        else:
            raise ValueError("Provide start_urls as a comma-sep string or a Python list")
        
        self.allowed_domains = list({urlparse(u).netloc for u in self.start_urls})

        self.file_type = file_type.lstrip(".").lower()
        self.disable_checks = disable_checks

    def parse(self, response):
        # 1) Check if this response is already the file you want:
        content_type = response.headers.get('Content-Type', b'').decode('utf-8').lower()
        # DISABLED: Extension and magic number checking
        is_target_ext = response.url.lower().endswith(f".{self.file_type}")
        is_magic = check_magic_num_response(content=response.body, file_extension=self.file_type)
        if is_target_ext or is_magic:
            # it's a direct file link — hand it off to FilesPipeline
            yield FileTypeItem(file_urls=[response.url])
            return  # don't try to parse it as HTML
        
        if self.disable_checks:
            # Always yield the file without checking
            yield FileTypeItem(file_urls=[response.url])
            return
        
        # 2) Otherwise treat it as HTML and look for links
        # examine all <a> links
        for href in response.css("a::attr(href)").getall():
            url = response.urljoin(href)
            # DISABLED: Extension and magic number checking
            if url.lower().endswith(f".{self.file_type}") or \
                check_magic_num_response(content=response.body, file_extension=self.file_type):
                # yield an Item for FilesPipeline to download
                yield FileTypeItem(file_urls=[url])
            else:
                # follow internal links
                parsed = urlparse(url)
                if parsed.netloc == self.allowed_domains[0]:
                    yield response.follow(url, callback=self.parse)
            
            if self.disable_checks:
                # Always yield the file without checking
                yield FileTypeItem(file_urls=[url])
                # follow internal links
                parsed = urlparse(url)
                if parsed.netloc == self.allowed_domains[0]:
                    yield response.follow(url, callback=self.parse)
            # # if the target file_type is an image, scan <img> tags

        if self.file_type in IMAGE_EXTS:
            self.logger.info("Scraping <img>")
            for src in response.css('img::attr(src)').getall():
                url = response.urljoin(src)
                # DISABLED: Extension and magic number checking
                if url.lower().endswith(f".{self.file_type}") or \
                    check_magic_num_response(content=response.body, file_extension=self.file_type):
                    # yield an Item for FilesPipeline to download
                    yield FileTypeItem(file_urls=[url])
                
                if self.disable_checks:
                    # Always yield the file without checking
                    yield FileTypeItem(file_urls=[url])