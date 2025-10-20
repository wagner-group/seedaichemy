A private repository for us to collaborate on using LLMs for fuzzing.

This branch is using google search engine to gather corpus for specific github public program
Steps to use this tool
#### step 0 Set up API Keys
This tool use Google API keys for webscraping
First set up Google API keys by going to this website: https://console.cloud.google.com/
Detail instruction link: https://support.google.com/googleapi/answer/6158862?hl=en

Second set up Goolge programmable search Engine: https://programmablesearchengine.google.com/
1. **Go to the PSE Control Panel**  
   [https://programmablesearchengine.google.com/controlpanel](https://programmablesearchengine.google.com/controlpanel)

2. **Create a New Search Engine**
   - Click **"Add"**
   - Enter the sites you want to search (e.g., `example.com` or `*.edu`)
   - Give it a name and click **Create**

3. **Find Your Search Engine ID (CX)**
   - After creating the engine, click on its name
   - In the setup page, copy the **Search engine ID (CX)** from the **Details** section

Finally, in your local .env file, set GOOGLE_API_KEY = [your google project api key] and SEARCH_ENGINE_ID = [your search engine ID]

note: if you are using VScode, you might need to reload the whole directory some VScode can update your environment variables


#### step 1
run ```pip install -r requirements.txt``` to install dependencies

#### step 2
if you are trying to gather corpus fos oss-fuzz project, please create a folder with the name of the project and put project yaml file inside that folder.
Example: projects - mupdf - project.yaml

#### step 3
go to corpus_searcher.py file

create a project object with following format 
project = project.Project.from_yaml(project.Project, project_name=[name of the project], project_path=[the directory path you store your project yaml])
example: mupdf_project = project.Project.from_yaml(project.Project, project_name='mupdf', project_path='projects/mupdf/project.yaml')

#### step 4
find where the fuzzer code link, the file in oss-fuzz contains the fuzzing-harness

#### step 5
call ```corpus_searcher('pdf', mupdf_project, "gpt-4o", mupdf_fuzzer_url, query_number=30)```

## Alternative feather specific corpus search

#### step 1
run ```pip install -r requirements.txt``` to install dependencies

#### step 2
go to corpus_searcher.py
```fs = file_features_generation('pdf', 33, 'gpt-4o', DEFAULT_RESPONSE_DIR)```

```feature_specific_query_gen(fs, 'pdf', 3, 'gpt-4o', DEFAULT_RESPONSE_DIR ,search=True, magic=False)```

replace 'pdf' with file type you want
