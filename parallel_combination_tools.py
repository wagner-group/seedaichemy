#!/usr/bin/env python3
"""
Parallel combination tool

This script automates the process of running multiple corpus generation attempts
in parallel.

Usage:
    python3 parallel_combination_tools.py --config <path to config_file.json>
"""

import os
import sys
import subprocess
import argparse
import json
import time
import signal

from datetime import datetime
from dotenv import load_dotenv
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import Lock

load_dotenv()

lock = Lock()
running_processes = []


def handle_manual_terminate(signum, frame):
    """
    Handle manual termination by terminating each subprocess.
    """
    print(f"\n[!] Received signal {signum}. Terminating subprocesses...")
    for p in running_processes:
        try:
            print(f"[-] Killing process PID={p.pid}")
            os.killpg(os.getpgid(p.pid), signal.SIGINT)
        except Exception as e:
            print(f"[!] Error killing process: {e}")
    sys.exit(1)


# Register signal handlers
signal.signal(signal.SIGINT, handle_manual_terminate)  # Ctrl+C
signal.signal(signal.SIGTERM, handle_manual_terminate)  # kill


# run a single trial of corpus generation
def run_single_trial(
    trial_id: int,
    file_type: str,
    output_dir: str,
    timeout: int,
    file_size: int,
    delete_previous: bool,
) -> Dict[str, Any]:
    """
    Start a subprocess that runs the combination tool with the given settings.
    """

    trial_dir_name = f"trial-{trial_id}{output_dir.replace('/', '-')}"
    output_dir = os.path.join(output_dir, f"trial_{trial_id}")
    cmd = [
        "python3",
        "combine.py",
        "-d" if delete_previous else "",
        "-t",
        str(timeout),
        "-s",
        str(file_size),
        "-trial_name",
        trial_dir_name,
        output_dir,
        file_type,
    ]
    cmd = [arg for arg in cmd if arg]

    try:
        p = subprocess.Popen(
            cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid,  # Create new process group
        )
        with lock:
            running_processes.append(p)
        stdout, stderr = p.communicate()

        return {
            "trial": trial_id,
            "success": p.returncode == 0,
            "return_code": p.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "output_dir": output_dir,
        }
    except Exception as e:
        return {
            "trial": trial_id,
            "success": False,
            "return_code": -1,
            "stdout": "",
            "stderr": str(e),
            "output_dir": output_dir,
        }


def run_corpus_generation(
    output_dir: str,
    file_type: str,
    timeout: int,
    file_size: int,
    trials_num: int,
    delete_previous: bool,
    max_parallel_trials: int,
) -> Dict[str, Any]:

    print(f"\n{'='*60}")
    print(f"Running {trials_num} corpus generation trials for: {file_type}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    if delete_previous and os.path.exists(output_dir):
        print(f"Deleting previous output directory: {output_dir}...")
        for root, dirs, files in os.walk(output_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(output_dir)
        print(f"Done deleting previous output directory.")
        print()

    start_time = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=max_parallel_trials) as executor:
        futures = {}
        for trial_id in range(1, trials_num + 1):
            time_sleep = 180
            futures[
                executor.submit(
                    run_single_trial,
                    trial_id,
                    file_type,
                    output_dir,
                    timeout,
                    file_size,
                    delete_previous,
                )
            ] = trial_id
            print(f"Trial {trial_id} started. Sleeping for {time_sleep} seconds...")
            time.sleep(time_sleep)  # 180 second pause for google search rate limiting
            print(f"Done sleeping.")
        print()

        print("Waiting for trials to finish...")
        for future in as_completed(futures):
            trial_result = future.result()
            trial_id = trial_result["trial"]

            if trial_result["success"]:
                print(f"✅ Trial {trial_id} succeeded.")
            else:
                print(f"❌ Trial {trial_id} failed: {trial_result['stderr']}")

            results.append(trial_result)

    duration = time.time() - start_time
    return {
        "file_type": file_type,
        "total_trials": trials_num,
        "duration_sec": duration,
        "results": results,
    }


def save_results(results: List[Dict[str, Any]], output_file: str):
    """Save results to a JSON file."""
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to: {output_file}")


def create_config_template():
    """Create a template configuration file."""
    config = {
        "file_type": "png",
        "timeout": 3600,
        "file_size": 1024,
        "output_base": "corpus_output",
        "delete_previous": True,
        "trials_num": 10,
        "max_parallel_trials": 10,
    }
    with open("parallel_config.json", "w") as f:
        json.dump(config, f, indent=2)
    print("Configuration template created: parallel_config.json")


def validate_config(config: dict):
    try:
        file_type = config["file_type"]
        assert file_type != None
    except:
        print("Error: No file type specified")
        sys.exit(1)
    try:
        timeout = config["timeout"]
        assert timeout != None
    except:
        print("Error: No timeout specified")
        sys.exit(1)
    try:
        file_size = config["file_size"]
        assert file_size != None
    except:
        print("Error: No file size specified")
        sys.exit(1)
    try:
        output_base = config["output_base"]
        assert output_base != None
    except:
        print("Error: No output base specified")
        sys.exit(1)
    try:
        delete_previous = config["delete_previous"]
        assert delete_previous != None
    except:
        print("Error: Delete previous not specified")
        sys.exit(1)
    try:
        trials_num = config["trials_num"]
        assert trials_num != None
    except:
        print("Error: Number of trials not specified")
        sys.exit(1)
    try:
        max_parallel = config["max_parallel_trials"]
        assert max_parallel != None
    except:
        print("Error: Max parallel trials not specified")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Batch Corpus Generator")
    parser.add_argument("--config", help="JSON configuration file")
    parser.add_argument("--file-type", help="File type")
    parser.add_argument("--timeout", help="Timeout in seconds")
    parser.add_argument("--file-size", help="File size in KB")
    parser.add_argument(
        "--output-base", default="corpus_output", help="Base output directory"
    )
    parser.add_argument(
        "--delete-previous", action="store_true", help="Delete previous results"
    )
    parser.add_argument(
        "--create-template", action="store_true", help="Create a configuration template"
    )
    parser.add_argument(
        "--trials-num", help="Number of trials to run for each configuration"
    )
    parser.add_argument(
        "--max-parallel-trials", help="Maximum number of parallel trials"
    )
    args = parser.parse_args()

    if args.create_template:
        create_config_template()
        return

    # Load configuration
    if args.config:
        with open(args.config, "r") as f:
            config = json.load(f)
    else:
        # Use command line arguments
        config = {
            "file_type": args.file_type,
            "timeout": args.timeout,
            "file_size": args.file_size,
            "output_base": args.output_base,
            "delete_previous": args.delete_previous,
            "trials_num": args.trials_num,
            "max_parallel_trials": args.max_parallel_trials,
        }
    validate_config(config)

    print(f"Configuration:")
    print(f"  File type: {config['file_type']}")
    print(f"  Timeout: {config['timeout']}")
    print(f"  File size: {config['file_size']}")
    print(f"  Output base: {config['output_base']}")
    print(f"  Delete previous: {config['delete_previous']}")
    print(f"  Number of trials: {config['trials_num']}")
    print(f"  Max parallel trials: {config['max_parallel_trials']}")

    # Run all combinations multiple times
    result = run_corpus_generation(
        output_dir=config["output_base"],
        file_type=config["file_type"],
        timeout=config["timeout"],
        file_size=config["file_size"],
        trials_num=config["trials_num"],
        delete_previous=config["delete_previous"],
        max_parallel_trials=config["max_parallel_trials"],
    )

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not os.path.exists("parallel_corpus_logs"):
        os.makedirs("parallel_corpus_logs")
    output_file = f"parallel_corpus_logs/corpus_results_{timestamp}.json"
    save_results([result], output_file)


if __name__ == "__main__":
    main()
