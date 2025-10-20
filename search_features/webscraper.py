import os
import requests
import datetime
import time
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from search_features.log_config import logger
from dotenv import load_dotenv
from tool.utils import *
from tool.run_spider import *
from tool.api_key_manager import APIKeyManager

# GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
# SEARCH_ENGINE_ID = os.environ['SEARCH_ENGINE_ID']
load_dotenv()
GOOGLE_API_KEYS = os.getenv("GOOGLE_API_KEY").split(",")
key_manager = APIKeyManager(GOOGLE_API_KEYS)

def google_file_downloader(query: str, 
                           save_dir:str, 
                           file_type: str, 
                           num_result = 10, 
                           mode='google',
                           magic = False):
    """
    Downloads files from Google Custom Search results based on a given query and file type.

    Args:
        query (str): The search query to find relevant files.
        save_dir (str): direcotry to save downloaded files
        file_type (str): The file extension/type to filter the search results (e.g., "pdf", "jpg").
        index (int): The index of the specific file to download (currently not used in implementation).

    Returns:
        list: A list of file URLs retrieved from the search results.

    Raises:
        requests.exceptions.RequestException: If there's an issue with the HTTP request.
        KeyError: If the expected "items" key is missing in the API response.

    Notes:
        - Uses Google Custom Search API to fetch relevant file links.
        - Downloads all files found in the search results.
        - Saves each file with a generated filename using `generate_file_name(file_type)`.
        - The `index` parameter is currently not utilized in the function.
    """
    try:
        google_api_key = key_manager.get_current_key()
        if mode == 'google':
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': google_api_key,
                'cx': os.environ['SEARCH_ENGINE_ID'],
                'q': query,
                'num': num_result
            }
        else:
            params = {
                "engine": "google",
                "q": query,
                "api_key": os.environ['SERP_API_KEY'],
                'num':num_result
            }
            search = GoogleSearch(params)
            results = search.get_dict()
            organic_results = results["organic_results"]
            links = [res["link"] for res in organic_results if "link" in res]
            return links
        response = requests.get(url, params=params)
        if response.status_code != 200:
            if response.status_code in [403, 429]:
                print(f"Quota exceeded for key. Switching to next key.")
                google_api_key = key_manager.get_next_key()
                if google_api_key is None:
                    print("No more API keys available.")
                print(f"Using new key")
                time.sleep(1)
                response = requests.get(url, params=params)
            response.raise_for_status()
        data = response.json()
        links = []
        file_type = file_type.lower().strip() # Sanitize file type
        for item in data.get("items", []):
            file_link = item['link']
            links.append(file_link)
        return links
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return []




