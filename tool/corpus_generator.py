#!/usr/bin/env python3
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
from tool.github_tool import fetch_github_file
from tool.prompt import prompt_generation, save_prompt
import agent.model as model
import tool.project as project
from search_features import oss_fuzz_checkout
import tool.output_parser as parser
import subprocess

REPO_OWNER = "google"
REPO_NAME = "oss-fuzz"
BRANCH = 'main'
DEFAULT_TEMPLATE_DIR = 'prompts'
DEFAULT_RESPONSE_DIR = 'response'
RAW_OUTPUT_EXT = '.rawoutput'

"""From oss-fuzz-gen: https://github.com/google/oss-fuzz-gen/blob/main/llm_toolkit/corpus_generator.py
"""
def get_script(
    prompt: str,
    response_dir: str,
    corpus_model: model.LLM
) -> str:
  """Uses LLMs to generate a python script that will create a seed corpus for a
  harness.

  The script generated is purely generated and should be considered untrusted
  in the general sense. OSS-Fuzz-gen already executes arbitrary code since
  OSS-Fuzz-gen executes arbitrary open source projects with no checking on
  what code is committed to the given projects."""

  corpus_model.query_llm(prompt, response_dir)
  for file in os.listdir(response_dir):
    if not parser.is_raw_output(file):
      continue
    corpus_generator_path = os.path.join(response_dir, file)
    with open(corpus_generator_path, 'r') as f:
      corpus_generator_source = f.read()

    corpus_generator_source = corpus_generator_source.replace('</results>', '')
    corpus_generator_source = corpus_generator_source.replace('<results>', '')
    corpus_generator_source = corpus_generator_source.replace('```python', '')
    corpus_generator_source = corpus_generator_source.replace('```', '')
    return corpus_generator_source

  # Return an empty Python program if generation failed.
  return 'import os'


def corpus_generator_llm_code_path(ai_binary: str,
        fixer_model_name: str,
        target_harness_path: str,
        project:project.Project,
        response_dir: str,
        ):
     
    corpus_model = model.LLM.setup(
      ai_binary=ai_binary,
      name=fixer_model_name,
    )

    # Get the corpus generation template
    with open(
        os.path.join(DEFAULT_TEMPLATE_DIR,
                    'corpus_generation_via_code_path.txt'), 'r') as f:
        prompt_to_query = f.read()
    with open(target_harness_path) as target_harness_file:
        target_harness_code = target_harness_file.read()

    prompt_to_query = prompt_to_query.replace('{HARNESS_SOURCE_CODE}',
                                                target_harness_code)

    project_repository = project.main_repo
    # TODO: generate code path
    target_code_path = "Call path: pcap_parse [line 1929] -> gen_scode [line 7023] -> lookup_proto [line 6116] -> pcap_nametollc"

    prompt_to_query = prompt_to_query.replace('{FILETYPE}', project.input_type)
    prompt_to_query = prompt_to_query.replace('{PROJECT_NAME}', project.project)
    prompt_to_query = prompt_to_query.replace('{PROJECT_REPOSITORY}',
                                                project_repository)
    prompt_to_query = prompt_to_query.replace('{CODE_PATH}',
                                                target_code_path)

    # prompt = corpus_model.prompt_type()()
    # prompt.add_priming(prompt_to_query)
    prompt = prompt_generation(prompt_to_query)

    response_dir = f'{os.path.splitext(target_harness_path)[0]}-corpus'
    os.makedirs(response_dir, exist_ok=True)
    prompt_path = os.path.join(response_dir, 'prompt.txt')
    save_prompt(prompt_path, prompt_to_query)

    return get_script(prompt=prompt, response_dir=response_dir, corpus_model=corpus_model)

# running a python script
def run_script(script:str, target_harness_path:str, language='python', id=1):
   if language == 'python':
      file_name = f'python_script_{id}.py'
      response_dir = f'{os.path.splitext(target_harness_path)[0]}-corpus'
      script_path = os.path.join(response_dir, file_name)
      with open(script_path, 'w+') as script_file:
        script_file.write(script)
      stdout_file = os.path.join(response_dir, f'python_script_{id}_output.txt')
      stderr_file = os.path.join(response_dir, f'python_script_{id}_error.txt')
      with open(stdout_file, "w") as out, open(stderr_file, "w") as err:
        result = subprocess.run(
            ["python3", file_name],
            cwd=response_dir,
            stdout=out,
            stderr=err
        )
      if result.returncode != 0:
          print(f"Script failed. See '{stderr_file}' for errors and '{stdout_file}' for output.")
      else:
          print(f"Script succeeded. Output is in '{stdout_file}'.")

if __name__ == "__main__":
    libpcap_project = project.Project.from_yaml(project.Project, 
                                                project_name='libpcap', 
                                                project_path='search_features/projects/libpcap/project.yaml',
                                                )
    script = corpus_generator_llm_code_path(
       ai_binary='',
       fixer_model_name='gpt-4.1',
       target_harness_path='search_features/projects/libpcap/fuzz_both.c',
       project= libpcap_project,
       response_dir='search_features/projects/libpcap/response'
    )
    run_script(script=script, target_harness_path='search_features/projects/libpcap/fuzz_both.c')
