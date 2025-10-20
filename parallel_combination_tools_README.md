# Parallel Corpus Generator

This tool runs multiple corpus generation jobs in parallel.

## Usage

Run the parallel corpus generator with a config file:

```bash
python3 parallel_combination_tools.py --config <path to config_file.json>
```

- `config_file.json`: JSON config file specifying the file type, timeout, and other options.

## Example

This command generates an example config file called `parallel_config.json`
```bash
python3 parallel_combination_tools.py --create-template
```

## Config File Format

A config file is a JSON file with the following fields:

```json
{
  "file_type": "png",
  "timeout": 3600,
  "file_size": 1024,
  "output_base": "corpus_output",
  "delete_previous": true,
  "trials_num": 10,
  "max_parallel_trials": 10
}
```

- `file_type`: Target file extension.
- `timeout`: Timeout for each run (in seconds).
- `file_size`: File size limit (in KB).
- `output_base`: Base directory for output corpora.
- `delete_previous`: If true, delete previous output directories.
- `trials_num`: Total number of trials
- `max_parallel_trials`: Max number of parallel trials.

## Output

- Each run creates a subdirectory in the output base directory: e.g. `corpus_output/trial_1/`
- Logs are stored in `logs/trial_1`
