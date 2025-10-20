import sys
import os
from openai import OpenAI
import subprocess
import git
import re
import urllib.parse
import requests
import shutil
from pathlib import Path
from tool.prompt import prompt_generation
from tool.api_key_manager import APIKeyManager
from agent import model
from dotenv import load_dotenv
import argparse
from tool.run_spider import *
import time
load_dotenv()

serpapi_keys = os.getenv('SERP_API_KEY').split(",")
key_manager = APIKeyManager(serpapi_keys)

def determine_file_type(repo_link):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    with open("search_queries/prompts/file_type.txt", "r", encoding="utf-8") as file:
        content = file.read()
    messages = [
        {"role": "system", "content": content},
        {
            "role": "user",
            "content": repo_link
        }
    ]
    temperature = 0
    frequency_penalty = 0
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=temperature,
        frequency_penalty=frequency_penalty
    )
    file_types = completion.choices[0].message.content
    print("Founded valid input file types: " + file_types)
    return file_types.split(',')

def generate_links(file_type, n=10):
    print("Generating links with file type " + file_type)
    ret = set()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    with open("search_queries/prompts/link_gen.txt", "r", encoding="utf-8") as file:
        content = file.read()
    messages = [
        {"role": "system", "content": content},
        {
            "role": "user",
            "content": file_type
        }
    ]
    model = "gpt-4o"
    temperature = 1
    frequency_penalty = 1.5
    for i in range(n): 
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            frequency_penalty = frequency_penalty
        )
        messages.append(
            {"role": "user", "content": "continue"}
        )
        ret.add(completion.choices[0].message.content)
    print(str(len(ret)) + " distinct " + file_type + " links generated")
    return ret
# generate query in one prompt
def generate_query(file_type, query_number=10):
    ret = []
    corpus_model = model.LLM.setup( 
        ai_binary='',
        name= 'gpt-4.1',
    )
    with open("search_queries/prompts/queries_gen_prompt.txt", "r", encoding="utf-8") as file:
        prompt_to_query = file.read()
    prompt_to_query = prompt_to_query.replace('{QUERY_NUMBER}', str(query_number))
    prompt_to_query = prompt_to_query.replace('{FILE_TYPE}', file_type)

    prompt = prompt_generation(prompt_to_query)
    print("Generating queries for file type:", file_type)

    corpus_model.query_llm(prompt, response_dir=None, log=True)
    completion, content = corpus_model.query_llm(prompt, response_dir=None, log=True)
    corpus_source = content.replace('```', '')
    queries = re.findall(r"""<result>\s*'?"?(.*?)"?'?\s*(?:<\/result>|<result>)""", 
                            corpus_source, 
                            re.DOTALL)
    print(f"Generated {len(queries)} queries for file type {file_type}")
    return queries

def search_google(query, n):
    try:
        serpapi_key = key_manager.get_current_key()
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": serpapi_key,
            "num": n
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            if response.status_code in [403, 429]:
                print(f"Quota exceeded for key. Switching to next key.")
                serpapi_key = key_manager.get_next_key()
                if serpapi_key  is None:
                    raise Exception("No more API keys available.")
                print(f"Using new key")
                time.sleep(10)
                response = requests.get(url, params=params)
            response.raise_for_status()
        data = response.json()
        ret = [result["link"] for result in data.get("organic_results", [])]
        print(f"Got {len(ret)} urls from google search")
        return ret
    except requests.exceptions.RequestException as e:
        print(f"Search failed: {e}")
        return []

def sanitize_url(url):
    ret = urllib.parse.quote(url, safe='')
    ret = re.sub(r'/', '-', ret)
    return ret

def delete_directory(dir):
    if os.path.isdir(dir):
        if not os.listdir(dir):
            pass
        else:
            shutil.rmtree(dir)

def copy_files(file_type, src_dir, dst_dir):
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)

    for root, dirs, files in os.walk(src_dir):
        for filename in files:
            if filename.lower().endswith(file_type):
                src_path = os.path.join(root, filename)
                dst_path = os.path.join(dst_dir, filename)
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(dst_path):
                    dst_path = os.path.join(dst_dir, f"{base}_{counter}{ext}")
                    counter += 1
                shutil.copy2(src_path, dst_path)
                print(f"Copied: {src_path} -> {dst_path}")

def search_queries_main(output_dir, file_type, N_query=20, N_link=100, disable_checks=False):
    links_set = set()
    print("Generating queries for:", file_type)
    gen_queries = generate_query(file_type, N_query)
    print("Generated queries:", gen_queries)
    queries = [f"fuzzing seed {file_type} files",  f"sample {file_type} files"] + gen_queries
    file_type = "." + file_type
    total_links = []
    for query in queries:
        # print("Downloading files from query:", query)
        search_links = search_google(query, N_link)
        total_links += search_links

    # start running scrapy spider with all links collected
    run_scrapy(start_urls= total_links, file_type=file_type, download_dir= output_dir + "/" + file_type, disable_checks=disable_checks)

if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir")
    parser.add_argument("file_type") 
    parser.add_argument("-e", action='store_true', help="Disable extension and magic number checking")
    args = parser.parse_args()
    search_queries_main(args.output_dir, args.file_type, disable_checks=args.e)

