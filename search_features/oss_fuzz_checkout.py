import os
import yaml
import logging
from tool.github_tool import fetch_github_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

"""OSS_FUZZ_DIR: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'oss-fuzz')"""
OSS_FUZZ_DIR = 'google/oss-fuzz'

def get_project_repository(project: str) -> str:
    """Returns the |project| repository read from its project.yaml."""
    project_yaml_path = os.path.join('projects', project,
                                    'project.yaml')
    
    project_yaml = fetch_github_file(repo_owner='google',repo_name='oss-fuzz', file_path=project_yaml_path, file_type='yaml')
    return project_yaml.get('main_repo', '')
  
repo = get_project_repository('urllib3')
print(repo)