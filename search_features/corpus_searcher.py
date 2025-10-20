from dotenv import load_dotenv
import os
import re
import time
import sys
from tool.prompt import prompt_generation
from tool.github_tool import fetch_file_github_url
from search_features.webscraper import *
import tool.project as project
import agent.model as model
from search_features.log_config import logger
load_dotenv()

RAW_OUTPUT_EXT = '.rawoutput'
DEFAULT_RESPONSE_DIR = 'search_features/response'
DEFAULT_CORPUS_DIR = 'search_features/corpus'
DEFAULT_TEMPLATE_DIR = 'search_features/prompts'

def corpus_searcher(file_type: str,
                    project:project.Project,
                    model_name:str,
                    fuzz_harness_url,
                    response_path = DEFAULT_RESPONSE_DIR,
                    query_number = 10,
                    magic=False
                    ):
    """
    Parameters
    ----------
    file_type : str
        The type of files to search for (e.g., 'pdf', 'png').

    project : project.Project
        An object containing metadata about the project, including its name and main repository.

    model_name : str
        The name of the LLM model used to generate search queries.

    fuzz_harness_url : str
        URL to the fuzz harness source code in a GitHub repository, which will be used to generate the search context.

    response_path : str, optional
        The base directory path where the model’s raw outputs and downloaded files will be saved.
        Defaults to `DEFAULT_RESPONSE_DIR`.

    query_number : int, optional
        The number of queries to generate using the model. Defaults to 10.
    
    magic: bool, optional(default=False)
        If True, use magic number in the donwloaded file to check file type, ignoring file extension

    Returns
    -------
    list of str
        A list of download links for files found via the generated search queries.
        If query generation fails, returns a string message indicating failure.
    """
    with open(os.path.join(DEFAULT_TEMPLATE_DIR, 'corpus_search_simple.txt'), 'r') as f:
        prompt_to_query = f.read()

    corpus_model = model.LLM.setup( 
        ai_binary='',
        name= model_name,
    )

    file_url = fuzz_harness_url
    fuzz_target_code = fetch_file_github_url(file_url)

    prompt_to_query = prompt_to_query.replace('{HARNESS_SOURCE_CODE}', fuzz_target_code) # type: ignore
    
    if not project.main_repo:
        # project_repository = oss_fuzz_checkout.get_project_repository(project.project)
        logger.warning("can't find main repo name of the project")
    else:
        project_repository = project.main_repo
    prompt_to_query = prompt_to_query.replace('{PROJECT_NAME}', project.project)
    prompt_to_query = prompt_to_query.replace('{PROJECT_REPOSITORY}', project_repository) # type: ignore
    prompt_to_query = prompt_to_query.replace('{QUERY_NUMBER}', str(query_number))
    prompt_to_query = prompt_to_query.replace('{FILE_TYPE}', file_type)
    
    response_dir = f'{os.path.join(response_path)}-corpus/{project.project}'
    os.makedirs(response_dir, exist_ok=True)
    # prompt_path = os.path.join(response_dir, 'prompt.txt')
    # prompt.save(prompt_path)

    prompt = prompt_generation(prompt_to_query)

    corpus_model.query_llm(prompt, response_dir)

    queries = []

    for file in os.listdir(response_dir):
        if not file.endswith(RAW_OUTPUT_EXT):
            continue
        search_query_path = os.path.join(response_dir, file)
        with open(search_query_path, 'r') as f:
            corpus_files_source = f.read()

        corpus_files_source = corpus_files_source.replace('```', '')
        queries = re.findall(r"<result>\s*'?(.*?)'?\s*(?:<\/result>|<result>)", 
                             corpus_files_source, 
                             re.DOTALL)
    
    if len(queries) == 0:
        return "failed to generate search query"
    
    links = []
    for dork in queries:
        dork = dork.strip("'")
        links.append(google_file_downloader(dork, response_dir, file_type, magic=magic))
        time.sleep(1)  # sleep for 1 second to stay under the rate limit
    return links


def file_features_generation(file_type:str, feature_number:int, model_name:str, response_path:str):
    """Parameters:
    ----------
    file_type : str
        The type of file to generate features for (e.g., 'pdf', 'docx').

    feature_number : int
        The number of features to request from the model.

    model_name : str
        The name of the LLM model used to generate the features.

    response_path : str
        The base directory path where the model's output will be saved.

    Returns:
    -------
    list of str
        A list of features extracted from the model's output.
    """
    file_model = model.LLM.setup( 
        ai_binary='',
        name= model_name,
    )
    with open(os.path.join(DEFAULT_TEMPLATE_DIR, 'file_features_prompt.txt'), 'r') as f:
        prompt_to_query = f.read()
    
    prompt_to_query = prompt_to_query.replace('{FEATURE_NUMBER}', str(feature_number))
    prompt_to_query = prompt_to_query.replace('{FILE_TYPE}', file_type)
    prompt = prompt_generation(prompt_to_query)

    response_dir = f'{os.path.join(response_path)}-features/{file_type}'
    os.makedirs(response_dir, exist_ok=True)

    file_model.query_llm(prompt, response_dir, log=True)

    features = []
    for file in os.listdir(response_dir):
        if not file.endswith(RAW_OUTPUT_EXT):
            continue
        search_query_path = os.path.join(response_dir, file)
        with open(search_query_path, 'r') as f:
            corpus_files_source = f.read()

        corpus_files_source = corpus_files_source.replace('```', '')
        features = re.findall(r"<result>\s*(.*?)\s*(?:<\/result>|<result>)", corpus_files_source, re.DOTALL)
    
    return features

# use LLM to generate search query to search for file use specified features
def feature_specific_query_gen(features, 
                               file_type:str, 
                               query_number:int, 
                               model_name:str, 
                               response_path:str, 
                               response_corpus_path:str,
                               search=True,
                               magic=False):
    """
    Generates and executes LLM-based search queries for each feature and optionally downloads related files.

    Parameters:
    ----------
    features : list of str
        A list of feature keywords or phrases for which to generate queries.
    
    file_type : str
        The type of file to target in the query generation (e.g., 'pdf', 'docx').

    query_number : int
        The number of queries to generate per feature (used in the prompt template).

    model_name : str
        The name of the LLM model to use for generating the queries.

    response_path : str
        The base directory path where generated query outputs and search results will be saved.

    search : bool, optional (default=True)
        If True, performs a Google search for each generated query and downloads files using `google_file_downloader`.

    magic: bool, optional(default=False)
        If True, use magic number in the donwloaded file to check file type, ignoring file extension
    Returns:
    -------
    list of str
        A list of cleaned queries extracted from the LLM outputs.
    """
    query_model = model.LLM.setup( 
        ai_binary='',
        name= model_name,
    )
    
    queries_sum = []
    query_outputs = ''
    for fea in features:
        with open(os.path.join(DEFAULT_TEMPLATE_DIR, 'feature_search_2.0.txt'), 'r') as f:
            prompt_to_query = f.read()
        prompt_to_query = prompt_to_query.replace('{FEATURE}', fea)
        prompt_to_query = prompt_to_query.replace('{FILE_TYPE}', file_type)
        prompt_to_query = prompt_to_query.replace('{QUERY_NUMBER}', str(query_number))
        prompt = prompt_generation(prompt_to_query)
        completion, content = query_model.query_llm(prompt, response_dir=None, log=True)

        query_source = content.replace('```', '')
        feature_query = re.findall(r"<result>\s*(.*?)\s*(?:<\/result>|<result>)", query_source, re.DOTALL)
        queries_sum += feature_query
        query_outputs+= query_source

    response_dir = f'{os.path.join(response_path)}-features/{file_type}/queries'
    os.makedirs(response_dir, exist_ok=True)
    query_model._save_output(index=2, content=query_outputs, response_dir=response_dir)

    # search and download actaul corpus online
    if search:
        links = []
        for dork in queries_sum:
            dork = dork.strip("'")
            links += google_file_downloader(dork, response_dir, file_type, magic=magic)
            time.sleep(1)  # sleep for 1 second to stay under the rate limit
    # run scrapy
    run_scrapy(start_urls= links, file_type=file_type, download_dir=response_corpus_path)
    return queries_sum

# combine file-specific feature with various content topics to generate queries
def combine_feature_topics_query(feature_quries, topics):
    #TODO
    ...

if __name__ == "__main__":

    # ujson_project = project.Project.from_yaml(project.Project, project_name='ujson', project_path='projects/ujson/project.yaml')
    # ujson_url = 'https://api.github.com/repos/google/oss-fuzz/blob/master/projects/ujson/ujson_fuzzer.py?ref=master'
    # corpus_searcher('json',ujson_project, 'gpt-3.5-turbo', ujson_url)

    # grok_project = project.Project.from_yaml(project.Project, project_name='grok', project_path='projects/grok/project.yaml')
    # grok_url = 'https://api.github.com/repos/google/oss-fuzz/blob/master/projects/grok/project.yaml?ref=master'
    # corpus_searcher('jpg',grok_project, 'gpt-4o', grok_url)

    # mupdf_project = project.Project.from_yaml(project.Project, project_name='mupdf', project_path='projects/mupdf/project.yaml')
    # mupdf_fuzzer_url = 'https://api.github.com/repos/google/oss-fuzz/blob/master/projects/mupdf/pdf_fuzzer.cc?ref=master'
    # corpus_searcher('pdf', mupdf_project, "gpt-4o", mupdf_fuzzer_url, query_number=30)

    file_type = sys.argv[1]
    response_corpus_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_CORPUS_DIR
    fs = file_features_generation(file_type, 33, 'gpt-4.1', DEFAULT_RESPONSE_DIR)
    feature_specific_query_gen(fs, file_type, 3, 'gpt-4.1', response_path=DEFAULT_RESPONSE_DIR , 
    response_corpus_path=response_corpus_dir, search=True, magic=False)
