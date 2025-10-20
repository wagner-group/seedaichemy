import os
import sys
from tool.github_tool import fetch_github_file
from tool.prompt import prompt_generation
import agent.model as model
import re
import tool.project as project
from search_features import oss_fuzz_checkout
import json

REPO_OWNER = "google"
REPO_NAME = "oss-fuzz"
BRANCH = 'main'
DEFAULT_TEMPLATE_DIR = 'search_features/prompts'
DEFAULT_RESPONSE_DIR = 'response'
RAW_OUTPUT_EXT = '.rawoutput'

"""
take in github project name and output some seed corpus files for fuzz testing
params:
model_name: LLM model to use
project: Project object
fuzz_harness_file_path: the github path to the fuzz target file
fuzz_owner: the repo owner that contain fuzz_target
fuzz_repo_name: the repo that contains fuzz_target
response_path: the path to store output seed files

return: a list of string, each contain content for one seed files
"""
def corpus_generator(model_name:str, 
                     project:project.Project, 
                     fuzz_harness_file_path, 
                     fuzz_owner=REPO_OWNER,
                     fuzz_repo_name=REPO_NAME,
                     response_path = DEFAULT_RESPONSE_DIR):

    # Get the corpus generation template
    with open(
        os.path.join(DEFAULT_TEMPLATE_DIR,
                   'corpus_generation_via_python_script.txt'), 'r') as f:
        prompt_to_query = f.read()

    corpus_model = model.LLM.setup( 
        ai_binary='',
        name= model_name,
    )
    file_path = fuzz_harness_file_path
    fuzz_target_code = fetch_github_file(fuzz_owner, fuzz_repo_name, file_path, file_type='code', branch=BRANCH)

    # prompt_to_query = prompt_to_query.replace('{HARNESS_SOURCE_CODE}', fuzz_target_code)
    
    if not project.main_repo:
        project_repository = oss_fuzz_checkout.get_project_repository(project.project)
    else:
        project_repository = project.main_repo
    prompt_to_query = prompt_to_query.replace('{PROJECT_NAME}', project.project)
    prompt_to_query = prompt_to_query.replace('{PROJECT_REPOSITORY}',project_repository)
    
    response_dir = f'{os.path.join(response_path)}-corpus'
    print(response_dir)
    os.makedirs(response_dir, exist_ok=True)
    prompt_path = os.path.join(response_dir, 'prompt.txt')
    # prompt.save(prompt_path)

    prompt = prompt_generation(prompt_to_query)

    corpus_model.query_llm(prompt, response_dir)

    for file in os.listdir(response_dir):
        if not file.endswith(RAW_OUTPUT_EXT):
            continue
        corpus_generator_path = os.path.join(response_dir, file)
        with open(corpus_generator_path, 'r') as f:
            corpus_files_source = f.read()

        corpus_files_source = corpus_files_source.replace('```', '')
        matches = re.findall(r"<results>\s*(\{.*?\})\s*</results>", corpus_files_source, re.DOTALL)
        return matches
    return []

def generate_json_corpus(contents, response_dir):
    os.makedirs(response_dir, exist_ok=True)
    # Save each extracted JSON object to a separate file
    index = 0
    for c in contents:
        json_obj = json.loads(c)  # Convert string to dictionary
        file_name = f'json_seed_{index}'
        output_path = os.path.join(response_dir, f'{file_name}.json')
        with open(output_path, 'w+') as f:
            json.dump(json_obj["content"], f, indent=2)  # Save JSON content
        index +=1


# urllib3_project = project.Project('urllib3', 'python', '', [], 'dict/json')
# corpus_generator('gpt-3.5-turbo',urllib3_project, 'projects/urllib3/fuzz_requests.py')

ujson_project = project.Project.from_yaml(project.Project, 'search_features/projects/ujson/project.yaml')
f = corpus_generator('gpt-4.1',ujson_project, 
                 'search_features/projects/ujson/ujson_fuzzer.py')
generate_json_corpus(f, 'response-corpus/ujson')
