import os
import sys
import subprocess
import time
import signal
import hashlib
import shutil
import argparse

from dotenv import load_dotenv
from datetime import datetime
from copy import deepcopy


def hash_value(file_path):
    hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            hash.update(byte_block)
    return hash.hexdigest()


def add_to_output(root, file, output):
    src_path = os.path.join(root, file)
    if file[0] == ".":
        file = "untitled" + file
    base, ext = os.path.splitext(file)
    if len(base) > 100:
        base = base[:100]
    dst_path = os.path.join(output, f"{base}{ext}")

    counter = 1
    while os.path.exists(dst_path):
        dst_path = os.path.join(output, f"{base}_{counter}{ext}")
        counter += 1
    shutil.copy2(src_path, dst_path)


def merge_dirs(dirs, output_dir, size_limit, max_file_num):

    hash_set = set()  # Track unique files
    files_added = 0  # Track files from non-github search
    github_dirs = []  # Track if we found a github directory

    # First, add the files from the non-github directories
    for dir in dirs:
        if not os.path.exists(dir):
            continue
        if dir[:14] == "github_queries":
            print(f"Skipping github ({dir}) for now...")
            github_dirs.append(dir)
            continue
        for root, _, files in os.walk(dir):
            print(f"Adding files from {dir}...")
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)

                # Skip files that are too large
                if file_size > size_limit * 1024:
                    continue

                # Check for duplicates using hash
                hash = hash_value(file_path)
                if hash in hash_set:
                    continue
                else:
                    hash_set.add(hash)

                # Add file to output
                add_to_output(root, file, output_dir)
                files_added += 1

    files_left = max_file_num - files_added

    # Now, include the github files
    if github_dirs != [] and files_left > 0:
        github_files = []
        print(f"Unique files added before including github: {files_added}")
        print(f"Trying to add github files...")

        # Get all the files and sort by size
        for github_dir in github_dirs:
            for root, _, files in os.walk(github_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)

                    # Skip files that are too large
                    if file_size > size_limit * 1024:
                        continue

                    # Check for duplicates using hash
                    hash = hash_value(file_path)
                    if hash in hash_set:
                        continue
                    else:
                        hash_set.add(hash)

                    # Add file to list
                    github_files.append((root, file, file_size))

        if len(github_files) > files_left:
            github_files.sort(key=lambda t: t[2])
            github_files = github_files[:files_left]

        # Add smallest github files to output
        for root, file, file_size in github_files:
            add_to_output(root, file, output_dir)

        print(f"Successfully added {len(github_files)} github files")
    else:
        print(f"No github files were added!")


def delete_dir(path, delete):
    if os.path.exists(path) and os.path.isdir(path):
        if delete:
            shutil.rmtree(path)
        else:
            raise FileExistsError(
                f"Folder found at {path} from the previous run. Add -d option to the command to delete the directory, or manually rename/delete it."
            )


def count_files(directory):
    count = 0
    if os.path.exists(directory):
        for _, _, files in os.walk(directory):
            for file in files:
                count += 1
    return count


def terminate_process_group(process, name):
    """Terminate a process and its entire process group."""
    try:
        if process.poll() is None:
            # Get the process group ID
            pgid = os.getpgid(process.pid)
            print(f"Terminating process group {pgid} for {name}...")

            # Send SIGTERM to the entire process group
            os.killpg(pgid, signal.SIGTERM)

            # Wait a bit for graceful termination
            time.sleep(2)

            # Check if process is still running
            if process.poll() is None:
                print(f"Force killing process group {pgid} for {name}...")
                # Send SIGKILL to the entire process group
                os.killpg(pgid, signal.SIGKILL)
                time.sleep(1)

                # Final check
                if process.poll() is None:
                    print(f"Warning: {name} process group {pgid} may still be running")
                else:
                    print(f"Successfully terminated {name} process group {pgid}")
            else:
                print(f"Successfully terminated {name} process group {pgid}")
    except Exception as e:
        print(f"Error terminating {name} process: {e}")
        # Fallback to direct process termination
        try:
            if process.poll() is None:
                process.terminate()
                time.sleep(1)
                if process.poll() is None:
                    process.kill()
        except Exception as e2:
            print(f"Fallback termination failed for {name}: {e2}")


if __name__ == "__main__":

    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Generate fuzzing seed files thorough different techniques, deduplicate and combine all files into one corpus"
    )
    parser.add_argument("output_dir", help="The output directory")
    parser.add_argument("file_type", help="The file extension intended to fuzz with")
    parser.add_argument(
        "-d",
        action="store_true",
        help="Delete result intermediate and output directories from the previous run",
    )
    parser.add_argument("-t", type=int, help="Run time limit, in seconds", default=3600)
    parser.add_argument(
        "-s",
        type=int,
        help="File size limit, in KBs, will ignore files greater than this number",
        default=1024,
    )
    parser.add_argument(
        "-n", type=int, help="Maximum number of files in output corpus", default=40000
    )
    parser.add_argument(
        "-e", action="store_true", help="Disable extension and magic number checking"
    )

    # Hidden arguments
    parser.add_argument(
        "-trial_name",
        type=str,
        help="Name of the trial for experiment, will be used to name intermediate result",
        default="trial-1",
    )

    # load arguments
    args = parser.parse_args()
    file_type = args.file_type
    trial_name = args.trial_name
    output_dir = args.output_dir
    timeout = args.t

    # Delete output directories from previous run
    delete_dir(output_dir, args.d)

    # record current time for logs
    now = datetime.now().strftime("%Y-%m-%d %H%M%S")
    logs_dir = os.path.join("logs", now, trial_name)

    # directories for each corpus generation method

    # search_queries: stores files in generated subdirectories under the main corpus dir
    SEARCH_QUERIES_DIR = os.path.join(
        "search_queries", trial_name, f"{file_type}_corpus"
    )

    # search_features: stores files in generated response-features subdirectories
    SEARCH_FEATURES_DIR = os.path.join(
        "search_features", trial_name, f"{file_type}_corpus"
    )

    # github_queries: stores files in generated subdirectories under the main corpus dir
    GITHUB_QUERIES_DIR = os.path.join(
        "github_queries", trial_name, f"{file_type}_corpus"
    )

    # common_crawl: stores files directly in the output directory
    COMMON_CRAWL_DIR = os.path.join("common_crawl", trial_name, f"{file_type}_corpus")

    # bug_tracker: stores filtered files in matching_files subdirectory
    BUG_TRACKER_DIR = os.path.join("bug_tracker", trial_name, f"{file_type}_corpus")

    dirs = [
        SEARCH_QUERIES_DIR,
        SEARCH_FEATURES_DIR,
        GITHUB_QUERIES_DIR,
        COMMON_CRAWL_DIR,
        BUG_TRACKER_DIR,
    ]

    # define the running command and other information for each method

    # Get the current Python executable to ensure subprocesses use the same environment
    python_executable = sys.executable

    search_queries = {
        "name": "search_queries",
        "command": f'{python_executable} -u -m search_queries.search_queries {SEARCH_QUERIES_DIR} {file_type}{" -e" if args.e else ""}',  # bash command to run the method
        "log": os.path.join(logs_dir, "search_queries.log"),  # log file
        "dir": SEARCH_QUERIES_DIR,  # sub-corpus directory
        "keys": [
            "OPENAI_API_KEY",
            "SERP_API_KEY",
        ],  # API keys required to run this method
        "enable": True,  # whether to run this method in corpus generation, will set to false if any of the required keys are null or empty
    }

    search_features = {
        "name": "search_features",
        "command": f"{python_executable} -u -m search_features.corpus_searcher {file_type} {SEARCH_FEATURES_DIR}",
        "log": os.path.join(logs_dir, "search_features.log"),
        "dir": SEARCH_FEATURES_DIR,
        "keys": ["OPENAI_API_KEY", "GOOGLE_API_KEY", "SEARCH_ENGINE_ID"],
        "enable": True,
    }

    github_queries = {
        "name": "github_queries",
        "command": f'{python_executable} -u -m github_queries.github_search.github_downloader {file_type} {GITHUB_QUERIES_DIR} {trial_name}{" -e" if args.e else ""}',
        "log": os.path.join(logs_dir, "github_queries.log"),
        "dir": GITHUB_QUERIES_DIR,
        "keys": ["OPENAI_API_KEY", "GITHUB_API_KEY"],
        "enable": True,
    }

    common_crawl = {
        "name": "common_crawl",
        "command": f"{python_executable} -u common_crawl/scripts/extract_seed_files_cc/get_seeds_common_crawl.py --output {COMMON_CRAWL_DIR} {file_type}",
        "log": os.path.join(logs_dir, "common_crawl.log"),
        "dir": COMMON_CRAWL_DIR,
        "keys": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION_NAME"],
        "enable": True,
    }

    bug_tracker = {
        "name": "bug_tracker",
        "command": f'{python_executable} -u -m scripts.bug_trackers.bug_tracker_extraction --dir "{BUG_TRACKER_DIR}" --type {file_type} --source both{" -e" if args.e else ""} && {python_executable} -u -m scripts.check_file_types --dir "{BUG_TRACKER_DIR}" --type {file_type}{" -e" if args.e else ""}',
        "log": os.path.join(logs_dir, "bug_tracker.log"),
        "dir": BUG_TRACKER_DIR,
        "keys": ["OPENAI_API_KEY"],
        "enable": True,
    }

    methods = [
        search_queries,
        search_features,
        github_queries,
        common_crawl,
        bug_tracker,
    ]

    file_types = [ft.strip() for ft in file_type.split(",") if ft.strip()]

    if len(file_types) > 1:
        # Multiple file types — duplicate and update methods per file_type
        methods_temp = []
        dirs_temp = []
        for ft in file_types:
            print(ft)
            for base_method in methods:
                method = deepcopy(base_method)
                method["name"] = f"{base_method['name']}_{ft}"
                method["command"] = base_method["command"].replace(file_type, ft)
                method["dir"] = base_method["dir"].replace(file_type, ft)
                method["log"] = base_method["log"].replace(".log", f"_{ft}.log")

                dirs_temp.append(method["dir"])
                methods_temp.append(method)
    else:
        # Single file type — use original methods
        methods_temp = methods
        dirs_temp = [method["dir"] for method in methods]
    methods = methods_temp
    dirs = dirs_temp

    # Delete directories from previous run
    for dir in dirs:
        # For bug_tracker, delete the parent directory since it creates matching_files subdirectory
        if dir == BUG_TRACKER_DIR:
            parent_dir = os.path.dirname(dir)
            delete_dir(parent_dir, args.d)
        else:
            delete_dir(dir, args.d)

    processes = []
    start_time = time.time()
    duration = None
    try:
        # check whether each method has all of its required API keys available; if not, set enable to false

        print("Checking API keys for each method...")
        for method in methods:
            for key in method["keys"]:
                print(f"Checking {key} for {method['name']} method...")
                if not os.getenv(key):
                    print(
                        f"API key {key} not found. Disabling {method['name']} method."
                    )
                    method["enable"] = False
                    break
        print()

        # start running each method in parallel

        for method in methods:
            if not method["enable"]:
                continue
            # cmd = method['command']
            cmd = f"exec {method['command']}"
            log_path = method["log"]

            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            log_file = open(log_path, "w")

            # Create process with new process group for proper termination
            p = subprocess.Popen(
                cmd,
                shell=True,
                # start_new_session=True,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid,  # Create new process group
            )
            processes.append((p, log_file, method["name"]))

        # checking timeout

        while True:
            time.sleep(1)
            if all(p.poll() is not None for p, _, _ in processes):
                print("All processes completed within time.")
                duration = time.time() - start_time
                break
            if time.time() - start_time > timeout:
                print("Time limit exceeded. Terminating all processes...")
                duration = timeout
                for p, _, name in processes:
                    if p.poll() is None:
                        terminate_process_group(p, name)
                break

    except KeyboardInterrupt:
        print("Keyboard interrupted")
        print("Terminating all processes...")
        duration = time.time() - start_time
        for p, _, name in processes:
            if p.poll() is None:
                terminate_process_group(p, name)

    finally:
        print()
        for _, log_file, _ in processes:
            log_file.close()

        # counting files generated by each method
        with open(os.path.join(logs_dir, "combine.log"), "w") as f:
            f.write(f"File type: {file_types}\n")
            f.write(f"Run duration: {duration} seconds\n")
            f.write(f"File size limit: {args.s} KB\n")
            for method in methods:
                name = method["name"]
                dir = method["dir"]
                if method["enable"]:
                    count_log = f"{name} generated {count_files(dir)} files at {dir}."
                    print(count_log)
                    f.write(f"{count_log}\n")
                else:
                    f.write(
                        f"{name} method not enabled, or its required API key not provided.\n"
                    )
        print()

        print("Combining intermediate corpora to the output corpus...")
        os.makedirs(output_dir, exist_ok=True)
        merge_dirs(dirs, output_dir, args.s, args.n)
        print()

        # counting files after size filtering
        with open(os.path.join(logs_dir, "combine.log"), "a") as f:
            f.write("\n=== File counts after size filtering ===\n")
            for method in methods:
                name = method["name"]
                dir = method["dir"]
                if method["enable"]:
                    # Count files that would pass size filter
                    filtered_count = 0
                    if os.path.exists(dir):
                        for root, _, files in os.walk(dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                try:
                                    if os.path.getsize(file_path) <= args.s * 1024:
                                        filtered_count += 1
                                except:
                                    pass
                    count_log = f"{name} has {filtered_count} files under {args.s}KB size limit at {dir}."
                    print(count_log)
                    f.write(f"{count_log}\n")
                else:
                    f.write(
                        f"{name} method not enabled, or its required API key not provided.\n"
                    )

        with open(os.path.join(logs_dir, "combine.log"), "a") as f:
            count_log = f"Total of {count_files(output_dir)} {file_type} distinct files generated at {output_dir}."
            print(count_log)
            f.write(f"{count_log}\n")
