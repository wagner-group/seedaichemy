# SeedAIchemy: LLM-driven Seed Corpus Generation for Fuzzing

SeedAIchemy is a LLM-based seed corpus generation tool for fuzzing. It runs five different seed generation techniques, deduplicates the outputs, and combines the results into a single corpus.

---

## 📦 Installation

1. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Add API keys to a `.env` file in the root directory.

   Example `.env` file:

   ```env
   OPENAI_API_KEY=""
   SERP_API_KEY=""
   GOOGLE_API_KEY=""
   SEARCH_ENGINE_ID=""
   GITHUB_API_KEY=""
   AWS_ACCESS_KEY_ID=""
   AWS_SECRET_ACCESS_KEY=""
   AWS_REGION_NAME=""
   AWS_BUCKET_NAME=""
   AWS_SESSION_TOKEN=""
   ```

   Alternatively, set environment variables via the command line:

   ```bash
   export OPENAI_API_KEY=""
   export SERP_API_KEY=""
   export GOOGLE_API_KEY=""
   export SEARCH_ENGINE_ID=""
   export GITHUB_API_KEY=""
   export AWS_ACCESS_KEY_ID=""
   export AWS_SECRET_ACCESS_KEY=""
   export AWS_REGION_NAME=""
   export AWS_BUCKET_NAME=""
   export AWS_SESSION_TOKEN=""
   ```

   - See `search_features/README.md` for setting up Google API keys and Search Engine ID.  
   - See `common_crawl/README.md` for AWS bucket setup instructions.

---

## 🚀 Running the Tool

To generate and combine a corpus, run

```bash
python3 combine.py [options] <output_directory> <file_extension>
```
For example,
```bash
python3 combine.py -d ./combined_output pdf
```
### Optional Arguments

- `-d` — Delete intermediate and output directories from previous runs (default: `False`)  
- `-t` — Run time limit for each technique in seconds (default: `3600`)  
- `-s` — Maximum file size in KB (files larger than this will be ignored, default: `1024`)  
- `-n` — Maximum number of files (default: `40000`)
- `-e` — Disable extension and magic number checking (default: `False`). If True, replace `<file_extension>` with a file description (ex. "binary_blob").

Press `Ctrl+C` once to stop generation early and combine intermediate outputs.

## Running Magma Experiment

If people trying to recreate Magma experiment results in the paper, please refer to this Magma fork https://github.com/jiangjingzhi2003/magma

## Credits

- File extension to MIME type mapping data is from [Qti3e/extensions.json](https://gist.github.com/Qti3e/6341245314bf3513abb080677cd1c93b), released under [The Unlicense](http://unlicense.org/).
