# settings.py
import os

BOT_NAME = 'file_crawler'
SPIDER_MODULES = ['spiders']
NEWSPIDER_MODULE = 'spiders'

# Use Scrapy’s built-in FilesPipeline
ITEM_PIPELINES = {
    'scrapy.pipelines.files.FilesPipeline': 1,
}

# Absolute path to this settings.py’s folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Download into a “downloads” folder inside your project
FILES_STORE = os.path.join(BASE_DIR, "downloads")
# # Where to store downloaded files
# FILES_STORE = '/downloaded_files'

# Optional: tune concurrency & throttling
CONCURRENT_REQUESTS = 32
CONCURRENT_REQUESTS_PER_DOMAIN = 8
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.5
AUTOTHROTTLE_MAX_DELAY = 5
