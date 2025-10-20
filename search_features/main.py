from corpus_searcher import *
import project
import argparse

parser = argparse.ArgumentParser(description="A script that takes command-line input.")
parser.add_argument("project_name", help="project name to fuzz")
parser.add_argument("--file_type", type=str, help="file type take in")
parser.add_argument("--project_yaml", type=str, help="project yaml files path")
parser.add_argument("--model_type", type=str, help="which AI model to use")
parser.add_argument("--fuzzer_url", type=str, help="github repo link contain fuzzer")

args = parser.parse_args()

project_name = args.project_name
file_type = args.file_type
project_yaml = args.project_yaml

print(f"Hello, {args.project_name}!")

mupdf_project = project.Project.from_yaml(project.Project, project_name=project_name, project_path=project_yaml)
mupdf_fuzzer_url = 'https://api.github.com/repos/google/oss-fuzz/blob/master/projects/mupdf/pdf_fuzzer.cc?ref=master'
corpus_searcher(file_type, mupdf_project, 'gpt-4o', mupdf_fuzzer_url, query_numebr=20)