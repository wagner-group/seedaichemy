# how to run: python check_file_types.py --dir ./corpus --file-type pdf

import os
import shutil
import subprocess
from openai import OpenAI
import openai
from typing import List
from tqdm import tqdm
import argparse
import logging

LOG_FILE = "scripts/bug_trackers/script_logs.txt"  # Log file path
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler(LOG_FILE),
    logging.StreamHandler()  # Optionally log to the console as well
])


parser = argparse.ArgumentParser(description="Filter and extract files by type using LLM and file command.")
parser.add_argument("--dir", type=str, default="./attachments", help="Directory containing downloaded attachments.")
parser.add_argument("--type", type=str, required=True, help="Target file type (e.g., pdf, core, trace).")
parser.add_argument("-e", action='store_true', help="Disable extension and magic number checking")
args = parser.parse_args()



DOWNLOAD_DIR = os.path.abspath(args.dir)
UNZIP_DIR = os.path.join(DOWNLOAD_DIR, 'unzipped')
MATCH_DIR = os.path.join(DOWNLOAD_DIR, 'matching_files')
TARGET_FILE_NAME = args.type.lower()
TOTAL_MATCH = 0

os.makedirs(UNZIP_DIR, exist_ok=True)
os.makedirs(MATCH_DIR, exist_ok=True)

openai.api_key = os.getenv("OPENAI_API_KEY")  #  this is fine

def get_acceptable_file_outputs(target: str) -> List[str]:

    prompt = f"""
        You're a file classification assistant. A user wants to find files of type: '{target}'.
        They will use the Linux `file` command to identify file types.

        Please return a list of possible `file` outputs that should be accepted as valid for this type. Return only one per line, no explanation.
        Example: For 'pdf' you might return:
        PDF document
        application/pdf
        ISO 32000 PDF

        Now return valid matches for: '{target}'
"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    lines = response.choices[0].message.content.strip().split("\n")
    return [line.strip().lower() for line in lines if line.strip()]

# === Helper: Run `file` command ===
def get_file_type(filepath: str) -> str:
    try:
        output = subprocess.check_output(['file', '--brief', filepath], text=True)
        return output.strip()
    except subprocess.CalledProcessError:
        return ""

# === Helper: Try to unzip archive files ===
def unzip_file(filepath: str):
    try:
        if filepath.endswith('.zip'):
            subprocess.run(['unzip', '-o', filepath, '-d', UNZIP_DIR], check=True)
        elif filepath.endswith(('.tar.gz', '.tgz')):
            subprocess.run(['tar', '-xzf', filepath, '-C', UNZIP_DIR], check=True)
        elif filepath.endswith('.tar'):
            subprocess.run(['tar', '-xf', filepath, '-C', UNZIP_DIR], check=True)
        elif filepath.endswith('.gz') and not filepath.endswith('.tar.gz'):
            out_path = os.path.join(UNZIP_DIR, os.path.basename(filepath[:-3]))
            with open(out_path, 'wb') as out_file:
                subprocess.run(['gunzip', '-c', filepath], stdout=out_file, check=True)
        elif filepath.endswith('.xz'):
            out_path = os.path.join(UNZIP_DIR, os.path.basename(filepath[:-3]))
            with open(out_path, 'wb') as out_file:
                subprocess.run(['unxz', '-c', filepath], stdout=out_file, check=True)
        elif filepath.endswith('.rar'):
            subprocess.run(['unrar', 'x', '-o+', filepath, UNZIP_DIR], check=True)
        else:
            return False
        return True
    except subprocess.CalledProcessError:
        return False

# === Core logic: check file type and move if it matches ===
def check_and_copy_if_match(filepath: str, acceptable_outputs: List[str]):
    global TOTAL_MATCH
    
    if args.e:
        # Always copy without checking
        destination = os.path.join(MATCH_DIR, os.path.basename(filepath))
        shutil.copy2(filepath, destination)
        TOTAL_MATCH += 1  #  Increment match counter
    else:
        # File type checking
        file_type = get_file_type(filepath).lower()
        if not file_type:
            return
        logging.info(f" Type: {file_type}")
        if any(expected in file_type for expected in acceptable_outputs):
            destination = os.path.join(MATCH_DIR, os.path.basename(filepath))
            shutil.copy2(filepath, destination)
            TOTAL_MATCH += 1  #  Increment match counter
        else:
            return
# === Main Function ===
def analyze():

    logging.info(f"Asking LLM for acceptable file types for: {TARGET_FILE_NAME}")
    acceptable_outputs = get_acceptable_file_outputs(TARGET_FILE_NAME)
    logging.info(" Acceptable matches:")
    for pattern in acceptable_outputs:
        logging.info(f"   - {pattern}")

    # Step 1: Go through downloaded files
        all_downloaded_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(DOWNLOAD_DIR)
        for file in files
        if UNZIP_DIR not in os.path.join(root, file) and MATCH_DIR not in os.path.join(root, file)
    ]

    for full_path in tqdm(all_downloaded_files, desc="Scanning attachments"):
        if unzip_file(full_path):
            continue
        check_and_copy_if_match(full_path, acceptable_outputs)

    # Step 2: Go through unzipped files
    unzipped_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(UNZIP_DIR)
        for file in files
    ]
    for full_path in tqdm(unzipped_files, desc="Scanning unzipped files"):
        check_and_copy_if_match(full_path, acceptable_outputs)
    print(f"TOTAL MATCHING FILES: {TOTAL_MATCH}")
    logging.info(f"TOTAL MATCHING FILES: {TOTAL_MATCH}")

# === Run ===
if __name__ == "__main__":
    analyze()


