import requests
import urllib.request
from tool.prompt import prompt_generation
import agent.model as model
from dotenv import load_dotenv
import re
import os
load_dotenv()
# Replace these with your actual credentials
GOOGLE_API_KEY =  os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')
SERP_API_KEY = os.getenv('SERP_API_KEY')

DEFAULT_TEMPLATE_DIR = './prompts'
RAW_OUTPUT_EXT = '.rawoutput'
query_model = model.LLM.setup( 
    ai_binary='',
    name= 'gpt-4o',
)

prompt = prompt_generation('test')
out = query_model.query_llm(prompt, response_dir=None, log=True)
print(out)

# if __name__ == "__main__":
#     test_query = "png dog"
#     # output = serp_search(test_query)
#     # print(output)
#     # out = google_search(test_query, GOOGLE_API_KEY, SEARCH_ENGINE_ID)
