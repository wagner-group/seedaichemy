import sys
import os
import json
import logging
import shutil
import argparse

# Add parent directories to Python path to handle both module and direct execution
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agent import model
from tool.prompt import prompt_generation
from github_queries.github_search.github_client import GitHubAPI, GitHubAPIError

def query_llm_dummy(openai_client, file_extension):
    """
    Dummy function to return example search keywords.
    
    :param openai_client: Unused variable for parity.
    :param file_extension: Unused variable for parity.
    :return: List of example search keywords.
    """
    return [file_extension, f"{file_extension} corpus", f"{file_extension} testing"]

def query_llm_for_search_keywords(openai_client, file_extension):
    """
    Use the OpenAI API to generate a JSON array of search keywords.
    Each element should be a string representing a search query to find repositories
    that may contain files with the specified file_extension.
    
    :param openai_client: Instance of OpenAIClient.
    :param file_extension: File extension to search for.
    :return: A list of groups of search keywords (strings).
    """
    # prompt = (
    #     f"Please provide a JSON array of search keywords to search GitHub repositories "
    #     f"for files of type '{file_extension}'. Each element in the array should be a string "
    #     "representing a search query (e.g., \"machine learning computer vision\"). "
    #     "Return only the JSON array with no additional text."
    # )
    
    prompt = ( f"""
        Please provide a JSON array of search keywords to search GitHub repositories for files of type '{file_extension}'.  
        Each element in the array should be a string representing a search query (e.g., "machine learning computer vision"). 
        Return only the JSON array with no additional text.
        The purpose is to find as many '{file_extension}' as possible, to do fuzzing on a program. The type of queries should not be limited to a particular domain, but should be generic enough to find a wide variety of repositories.
        Give me 50 different search queries, where at least 10 should be related to fuzzing, corpus, testing, repo, and or dataset. Not need to include the word GitHub.
        Please have the output type be in a form of the following example:
        ["{file_extension}", "{file_extension} folder", "{file_extension} corpus", "related to {file_extension}", "{file_extension} libraries"]"""
    )
    
    try:
        prompt = prompt_generation(prompt)
        completion, response = openai_client.query_llm(prompt)
        search_keywords = json.loads(response)
        if not isinstance(search_keywords, list):
            raise ValueError("Expected a JSON array.")
        return search_keywords
    except Exception as e:
        logging.error(f"Error parsing search keywords from LLM response: {e}")
        # Fallback default keywords if LLM fails
        return [f"filetype:{file_extension}", f"{file_extension} archive", f"{file_extension} data", f"{file_extension} dataset",f"{file_extension} collection",f"{file_extension} examples",f"{file_extension} samples",f"{file_extension} documents",f"{file_extension} files",f"{file_extension} resources",f"{file_extension} library", f"{file_extension} repository", f"{file_extension} code", f"{file_extension} analysis", f"{file_extension} testing", f"{file_extension} fuzzing", f"{file_extension} utilities", f"{file_extension} scripts"]

def initialize_clients(magic=False, disable_checks=False):
    """
    Initialize the OpenAI and GitHub API clients.
    
    :return: Tuple containing instances of OpenAIClient and GitHubAPI.
    """
    try:
        # openai_client = OpenAIClient()
        openai_client = model.LLM.setup( 
            ai_binary='',
            name= 'gpt-4.1',
        )
    except model.OpenAIClientError as e:
        logging.error(f"Failed to initialize OpenAI client: {e}")
        sys.exit(1)

    # Initialize the GitHub API client.
    try:
        github_client = GitHubAPI(magic=magic, disable_checks=disable_checks)
    except (GitHubAPIError, Exception) as e:
        logging.error(f"Failed to initialize GitHub client: {e}")
        sys.exit(1)
    
    return openai_client, github_client

def process_repositories_with_clone(github_client, search_keywords, file_extension, corpus_folder, search_count, trial_name):
    """
    Process repositories using git clone approach to extract files with specific extension.
    This minimizes API calls by only using GraphQL for repository search.
    
    :param github_client: Instance of GitHubAPI.
    :param search_keywords: List of search keywords.
    :param file_extension: File extension to search for.
    :param corpus_folder: Folder to copy files to.
    :param search_count: Number of repositories to process per keyword.
    """
    total_files_copied = 0
    processed_repos = set()

    for keyword in search_keywords:
        logging.info(f"Processing search keyword: '{keyword}'")
        try:
            # Search for repositories using GraphQL (minimal API calls)
            repos = github_client.search_repositories_graphql(keyword)
            
            for repo_name in repos[:search_count]:
                if repo_name in processed_repos:
                    continue
                processed_repos.add(repo_name)
                
                print(f"Processing repository: {repo_name}")
                files_copied = github_client.extract_files(
                    repo_name, 
                    file_extension, 
                    corpus_folder,
                    f"temp_clones/{trial_name}/{file_extension}-repos"
                )
                total_files_copied += files_copied
                
                # Small delay to be nice to GitHub
                import time
                time.sleep(1)

        except GitHubAPIError as e:
            logging.error(f"Error during repository search for keyword '{keyword}': {e}")
            continue
    
    logging.info(f"Total files copied: {total_files_copied}")

def main():
    """
    Main function to execute the GitHub clone-based downloader script.
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="GitHub repository downloader for specific file types")
    parser.add_argument("file_extension", help="File extension to search for")
    parser.add_argument("corpus_folder", help="Folder to save downloaded files")
    parser.add_argument("trial_name", help="Name of the trial")
    parser.add_argument("-e", action='store_true', help="Disable extension and magic number checking")
    
    args = parser.parse_args()

    file_extension = args.file_extension
    corpus_folder = args.corpus_folder
    trial_name = args.trial_name
    disable_checks = args.e
    
    os.makedirs(corpus_folder, exist_ok=True)

    openai_client, github_client = initialize_clients(disable_checks=disable_checks)

    # fetch search keywords from LLM
    # Dummy function to return example search keywords
    # search_keywords = query_llm_dummy(openai_client, file_extension)
    search_keywords = query_llm_for_search_keywords(openai_client, file_extension)

    logging.info(f"Search keywords obtained: {search_keywords}")

    search_count = 10 # Number of repositories to process per keyword
    process_repositories_with_clone(github_client, search_keywords, file_extension, corpus_folder, search_count, trial_name)

if __name__ == "__main__":
    main() 