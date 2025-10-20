import os
import yaml

"""referencing https://github.com/google/oss-fuzz-gen/blob/main/experiment/benchmark.py"""
REPO_OWNER = "google"
REPO_NAME = "oss-fuzz"
BRANCH = 'main'
DEFAULT_TEMPLATE_DIR = 'prompts'
DEFAULT_RESPONSE_DIR = 'response'

class Project:
    """Represent a single project"""
    def __init__(self, project:str, 
                 language:str, 
                 return_type:str,  
                 params: list[dict[str, str]],
                 input_type:str,
                 main_repo='',
                 use_context=False,
                 fuzz_harness_path=''):
        self.project = project
        self.language = language
        self.return_type = return_type
        self.params = params
        self.input_type = input_type
        self.use_context = use_context
        self.fuzz_harness_path = fuzz_harness_path
        self.main_repo = main_repo
    
    def from_yaml(cls, project_path:str, project_name=''):
        """Constructs a benchmark based on a yaml file."""
        projects = []
        with open(project_path, 'r') as project_file:
            data = yaml.safe_load(project_file)
        if not data:
            return []
        
        project_name = data.get('project', project_name)
        language = data.get('language', '')
        target_path = data.get('target_path')
        target_name = data.get('target_name')
        use_context = data.get('use_context', False)
        file_type = data.get('input_type', '')
        main_repo = data.get('main_repo')

        return cls(
            project_name,
            language,
            '',
            [],
            file_type,
            main_repo,
            use_context,
        )


    def __str__(self):
        return (f'project={self.project}, '
                f'language={self.language},'
                f'input_type={self.input_type}, '
                f'return_type={self.return_type}, '
                f'main_repo={self.main_repo}, ')