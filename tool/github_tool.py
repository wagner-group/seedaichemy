import requests
import base64
import yaml
import agent.model as model
from urllib.parse import urlparse
from tool.prompt import prompt_generation
from tool import project
import os
import re

MODEL_TYPE = 'gpt-4.1'
DEFAULT_TEMPLATE_DIR = 'search_features/prompts'
RAW_OUTPUT_EXT = '.rawoutput'


def fetch_github_file(repo_owner, repo_name, file_path, file_type, branch="master", token=None):
    """
    Fetches a file's content from a GitHub repository using the GitHub API.

    Args:
        repo_owner (str): GitHub username or organization name.
        repo_name (str): Repository name.
        file_path (str): Path to the file in the repository.
        branch (str, optional): Branch name. Defaults to "main".
        token (str, optional): GitHub personal access token (needed for private repos).

    Returns:
        str: The file's content as a string, or an error message if unsuccessful.
    """
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}?ref={branch}"
    headers = {"Authorization": f"token {token}"} if token else {}

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        file_data = response.json()
        if file_type == 'code':
            return base64.b64decode(file_data["content"]).decode("utf-8")  # Decode Base64 content
        elif file_type == 'yaml':
            # Parse YAML content
            encoded_content = file_data.get("content", "")
        
            # Decode Base64 content
            yaml_content = base64.b64decode(encoded_content).decode("utf-8")

            data = yaml.safe_load(yaml_content) or {}
            return data  # Return 'main_repo' field or empty string
    else:
        return f"Failed to fetch file: {response.status_code}, {response.text}"


def fetch_file_github_url(url, file_type='code', token=None):
    """
    Fetches a file's content from a GitHub repository using the GitHub API.

    Args:
        url (str): the url of code file
        token (str, optional): GitHub personal access token (needed for private repos).

    Returns:
        str: The file's content as a string, or an error message if unsuccessful.
    """
    try:
        parsed = urlparse(url)
        parts = parsed.path.strip("/").split("/")

        if "blob" not in parts:
            return "Invalid GitHub file URL (must include /blob/)."

        owner = parts[0]
        repo = parts[1]
        blob_index = parts.index("blob")
        branch = parts[blob_index + 1]
        file_path = "/".join(parts[blob_index + 2:])

        file = fetch_github_file(repo_owner=owner, repo_name=repo, file_path=file_path, branch=branch, file_type=file_type)
        return file
    except Exception as e:
        return f"Failed to parse URL: {e}"

def github_project_filetypes(project:project.Project, fuzzer_url, response_dir):
    query_model = model.LLM.setup( 
            ai_binary='',
            name= 'gpt-4.1',
        )
    fuzzer_file = fetch_file_github_url(url=fuzzer_url)

    with open(os.path.join(DEFAULT_TEMPLATE_DIR, 'github_file_type.txt'), 'r') as f:
            prompt_to_query = f.read()

    prompt_to_query = prompt_to_query.replace('{PROJECT_NAME}', project.project)
    prompt_to_query = prompt_to_query.replace('{PROJECT_REPOSITORY}',project.main_repo)
    prompt_to_query = prompt_to_query.replace('{HARNESS_SOURCE_CODE}',fuzzer_file)

    prompt = prompt_generation(prompt_to_query)
    query_model.query_llm(prompt=prompt, response_dir=response_dir)

    for file in os.listdir(response_dir):
        if not file.endswith(RAW_OUTPUT_EXT):
                continue
        search_query_path = os.path.join(response_dir, file)
        with open(search_query_path, 'r') as f:
            corpus_files_source = f.read()

        filetypes = re.findall(r"<result>\s*'?(.*?)'?\s*(?:<\/result>|<result>)", 
                            corpus_files_source, 
                            re.DOTALL)
    if len(filetypes) == 0:
         print('fail to find valid filetypes for the project')
         return filetypes
    return filetypes