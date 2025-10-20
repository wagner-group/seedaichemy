# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class FileTypeItem(scrapy.Item):
    # URLs of files to download
    file_urls = scrapy.Field()
    # information about downloaded files (filled by FilesPipeline)
    files = scrapy.Field()

class ImageTypeItem(scrapy.Item):
    # URLs of files to download
    image_urls = scrapy.Field()
    # information about downloaded files (filled by FilesPipeline)
    images = scrapy.Field()

