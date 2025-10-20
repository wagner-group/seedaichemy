import os
import requests
import time
import subprocess
import shutil
from dotenv import load_dotenv
from tool.utils import check_magic_num_file
from tool.api_key_manager import APIKeyManager

load_dotenv()

class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors."""
    pass

class GitHubAPI:
    BASE_URL = "https://api.github.com"
    
    def __init__(self, magic=False, disable_checks=False):
        # Load the token from environment variables.
        self.github_api_keys = os.getenv("GITHUB_API_KEY", "").split(",")
        self.token = self.github_api_keys[0].strip() if self.github_api_keys else None

        self.key_manager = APIKeyManager(self.github_api_keys)
        if not self.token:
            raise ValueError("GITHUB_TOKEN is not set in the environment variables.")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.magic = magic
        self.disable_checks = disable_checks
        
        # Check rate limit
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get("https://api.github.com/rate_limit", headers=headers)

        if response.status_code == 200:
            data = response.json()
            print(data)
            
            # Check general API limit
            general_used = data["rate"]["limit"] - data["rate"]["remaining"]
            print(f"General API requests in the past hour: {general_used}")
            print(f"General Remaining: {data['rate']['remaining']} out of {data['rate']['limit']}")
    
    def _make_request(self, url, params=None, stream=False):
        """
        Helper method to perform HTTP GET requests with error handling.
        """
        while True:
            try:
                response = requests.get(url, headers=self.headers, params=params, stream=stream)

                if response.status_code in [403, 429]:
                    print(f"Quota exceeded for key. Switching to next key.")
                    self.token = self.key_manager.get_next_key()
                    if self.token is None:
                        print("No more API keys available.")
                        continue
                    print(f"Using new key")
                    time.sleep(1)
                    response = self._make_request(url, stream=stream)

                if "rate limit exceeded" in response.text.lower():
                    print("[Rate Limit] Detected rate limit exceeded. Sleeping for 5 minutes...")
                    time.sleep(300)
                    continue

                response.raise_for_status()
                return response

            except requests.RequestException as e:
                raise GitHubAPIError(f"Error during request to {url} with params {params}: {e}") from e

    def search_repositories_graphql(self, keywords):
        """
        Search for repositories by keywords using the GitHub GraphQL API.
        :param keywords: String with keywords (e.g., "machine learning").
        :return: List of repository full names (owner/name).
        """
        url = "https://api.github.com/graphql"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v4+json"
        }
        query = """
        query($search_query: String!) {
          search(query: $search_query, type: REPOSITORY, first: 10) {
            nodes {
              ... on Repository {
                name
                owner { login }
                url
                defaultBranchRef {
                  name
                }
              }
            }
          }
        }
        """
        variables = {"search_query": keywords}
        response = requests.post(url, headers=headers, json={"query": query, "variables": variables})
        response.raise_for_status()
        data = response.json()
        if "errors" in data:
            raise GitHubAPIError(f"GraphQL error: {data['errors']}")
        repos = data["data"]["search"]["nodes"]
        return [f"{repo['owner']['login']}/{repo['name']}" for repo in repos]

    def extract_files(self, repo_full_name, file_extension, corpus_folder, temp_folder="temp_clones"):
        """
        Clone a repository, find files with specific extension, copy them to corpus, and delete the clone.
        
        :param repo_full_name: Full repo name in "username/repo" format.
        :param file_extension: File extension to search for (e.g., "pdf").
        :param corpus_folder: Folder to copy matching files to.
        :param temp_folder: Temporary folder for cloning repos.
        :return: Number of files found and copied.
        """
        owner, repo = repo_full_name.split("/")
        repo_url = f"https://github.com/{repo_full_name}.git"
        
        # Create temp directory for cloning
        os.makedirs(temp_folder, exist_ok=True)
        clone_path = os.path.join(temp_folder, repo)
        
        try:
            print(f"Cloning {repo_full_name}...")
            
            # Clone the repository
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, clone_path],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                print(f"Failed to clone {repo_full_name}: {result.stderr}")
                return 0
            
            print(f"Successfully cloned {repo_full_name}")
            
            # Find all files with the specified extension
            matching_files = []
            for root, dirs, files in os.walk(clone_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    if self.disable_checks:
                        # Always include all files without checking
                        matching_files.append(file_path)
                    else:
                        # Extension and magic number checking
                        if file.endswith(f".{file_extension}") or check_magic_num_file(file_path=file_path, file_extension=file_extension):
                            matching_files.append(file_path)
            
            print(f"Found {len(matching_files)} {file_extension} files in {repo_full_name}")
            
            # Copy matching files to corpus folder
            files_copied = 0
            for file_path in matching_files:
                try:
                    # Create relative path from clone root
                    relative_path = os.path.relpath(file_path, clone_path)
                    
                    # Create destination path in corpus
                    dest_path = os.path.join(corpus_folder, repo, relative_path)
                    dest_dir = os.path.dirname(dest_path)
                    os.makedirs(dest_dir, exist_ok=True)
                    
                    # Copy the file
                    shutil.copy2(file_path, dest_path)
                    files_copied += 1
                    print(f"Copied: {relative_path}")
                    
                except Exception as e:
                    print(f"Error copying {file_path}: {e}")
                    continue
            
            return files_copied
            
        except subprocess.TimeoutExpired:
            print(f"Timeout cloning {repo_full_name}")
            return 0
        except Exception as e:
            print(f"Error processing {repo_full_name}: {e}")
            return 0
        finally:
            # Clean up: remove the cloned repository
            if os.path.exists(clone_path):
                try:
                    shutil.rmtree(clone_path)
                    print(f"Cleaned up {clone_path}")
                except Exception as e:
                    print(f"Error cleaning up {clone_path}: {e}")

    def search_and_clone_repos(self, keywords, file_extension, corpus_folder, search_count=10):
        """
        Search for repositories and clone them to extract files with specific extension.
        
        :param keywords: Search keywords.
        :param file_extension: File extension to search for.
        :param corpus_folder: Folder to copy files to.
        :param search_count: Number of repositories to process per keyword.
        :return: Total number of files copied.
        """
        total_files_copied = 0
        processed_repos = set()
        
        try:
            # Search for repositories using GraphQL
            repos = self.search_repositories_graphql(keywords)
            
            for repo_name in repos[:search_count]:
                if repo_name in processed_repos:
                    continue
                processed_repos.add(repo_name)
                
                print(f"Processing repository: {repo_name}")
                files_copied = self.extract_files(
                    repo_name, 
                    file_extension, 
                    corpus_folder
                )
                total_files_copied += files_copied
                
                # Small delay to be nice to GitHub
                time.sleep(1)
            
            return total_files_copied
            
        except Exception as e:
            print(f"Error in search_and_clone_repos: {e}")
            return total_files_copied 