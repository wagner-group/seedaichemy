#how to use: python main.py --dir corpus --type png 
import os
import requests
import subprocess
from openai import OpenAI
from urllib.parse import urlparse
from launchpadlib.launchpad import Launchpad
import argparse
from tqdm import tqdm
import time
import logging
from tool.utils import check_magic_num_response

LOG_FILE = "scripts/bug_trackers/script_logs.txt"  # Log file path
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler(LOG_FILE),
    logging.StreamHandler()  # Optionally log to the console as well
])

parser = argparse.ArgumentParser(description="Filter and extract files by type using LLM and file command.")
parser.add_argument("--dir", type=str, default="./attachments", help="Directory containing downloaded attachments.")
parser.add_argument("--type", type=str, required=True, help="Target file type (e.g., pdf, core, trace).")
parser.add_argument("--source", type=str, choices=["launchpad", "bugzilla", "both"], default="both",
                    help="Bug tracker source to use: launchpad, bugzilla, or both.")
parser.add_argument("--max-limit", type=int, required=False,default=500, help="Maximum number of bugs to scan.")
parser.add_argument("-e", action='store_true', help="Disable extension and magic number checking")
args = parser.parse_args()

# === CONFIG ===
DOWNLOAD_DIR = os.path.abspath(args.dir)
TARGET_FILE = args.type
MAX_NUM_BUGS = args.max_limit
TOTAL_FILES=0
ALL_BUG_STATUSES = [
    'New', 'Incomplete', 'Opinion', 'Invalid',
    'Won\'t Fix', 'Expired', 'Confirmed', 'Triaged',
    'In Progress', 'Fix Committed', 'Fix Released'
]

# === SETUP ===
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
# === Helper: Extract final URL ===
def get_real_file_url(data_link):
    response = requests.get(data_link, allow_redirects=True)
    return response.url
# === Helper: Download via wget ===
def download_file(file_url, filename):
    global TOTAL_FILES
    try:
        if args.e:
            # Always download without checking
            subprocess.run(["wget", "-q", "-O", filename, file_url], check=True)
            logging.info(f"✅ Downloaded: {filename}")
            TOTAL_FILES+=1
            return
        else:
            # Extension checking
            if file_url.lower().endswith(TARGET_FILE.lower()):
                logging.info("Downloading file directly as it matches the target type.")
                subprocess.run(["wget", "-q", "-O", filename, file_url], check=True)
                logging.info(f"✅ Downloaded: {filename}")
                TOTAL_FILES+=1
                return
            # Path 2: Magic check
            try:
                response = requests.get(file_url, stream=True, timeout=10)
                logging.info(f"Downloading file: {file_url}")
                response.raise_for_status()  # Ensure we got a valid response
                # Magic number checking
                if check_magic_num_response(response, file_extension=TARGET_FILE.lstrip('.')):
                    logging.info(f"File matches magic number for {TARGET_FILE}, downloading...")
                    subprocess.run(["wget", "-q", "-O", filename, file_url], check=True)
                    logging.info(f"✅ Downloaded: {filename}")
                    TOTAL_FILES+=1
                    return
                else:
                    logging.info(f"File does not match magic number for {TARGET_FILE}, skipping download.")
                    return
            except:
                pass
        
    except subprocess.CalledProcessError  as e:
        logging.info(f"Failed to download: {file_url}: {e}")


# === Step 1: Use GPT-4o to generate search queries ===
def generate_search_query_from_file(file_format, max_retries=3, backoff_factor=2):
    client = OpenAI()
    prompt = f"""You're assisting a developer searching Launchpad bug reports.
Based on this file format: {file_format}, generate a minimum of 5 concise and effective search queries to find relevant bugs (preferably with attachments) that might be related to this file format.
Return only plain text search queries, one per line.
Do NOT include markdown, code blocks, or any extra formatting."""
    
    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.info(f"Attempt {attempt} failed with error: {e}")
            if attempt == max_retries:
                logging.info("Max retries reached, raising exception.")
                raise
            sleep_time = backoff_factor ** (attempt - 1)
            logging.info(f"Retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)


def search_and_download_attachments(search_text):
    logging.info(f"Searching Launchpad for: '{search_text}'")
    launchpad = Launchpad.login_anonymously('my-app', 'production')
    tasks = launchpad.bugs.searchTasks(search_text=search_text, status=ALL_BUG_STATUSES)

    attachment_count = 0    
    for task in tqdm(tasks, desc="Processing bug tasks"):
        bug = task.bug
        if bug.attachments:
            for attachment in bug.attachments:
                if attachment_count >= MAX_NUM_BUGS:
                    break

                title = attachment.title or f"attachment_{attachment.id}"
                data_link = attachment.data_link
                real_file_url = get_real_file_url(data_link)
                parsed_url = urlparse(real_file_url)
                filename = f"{attachment_count}_{os.path.basename(parsed_url.path)}"
                filepath = os.path.join(DOWNLOAD_DIR, filename)

                # Directly download without threading
                download_file(real_file_url, filepath)

                attachment_count += 1
        if attachment_count >= MAX_NUM_BUGS:
            break

    if attachment_count == 0:
        logging.info("No attachments found.")
    else:
        logging.info(f"✅ Downloaded {attachment_count} attachments.")

def run_bugzilla_flow(queries, limit=500):
    global TOTAL_FILES
    import base64

    BUGZILLA_API_URL = "https://bugzilla.redhat.com/rest"
    NUM_BUGS = limit

    ALL_STATUSES = [
        "UNCONFIRMED", "CONFIRMED", "IN_PROGRESS", "ASSIGNED", "REOPENED", "NEW",
        "ON_DEV", "VERIFIED", "RELEASE_PENDING", "POST", "MODIFIED",
        "ON_QA", "QA_READY", "FAILS_QA", "CLOSED", "RESOLVED", "INVALID",
        "WONTFIX", "DUPLICATE", "WORKSFORME", "INCOMPLETE", "EOL"
    ]

    def get_attachments(bug_id):
        u = f"{BUGZILLA_API_URL}/bug/{bug_id}/attachment"
        r = requests.get(u)
        r.raise_for_status()
        return r.json().get("bugs", {})

    def download_attachment(att):
        global TOTAL_FILES
        try:
            filename = att["file_name"]
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            data = att.get("data")
            if not data:
                att_id = att.get("id")
                att_resp = requests.get(f"{BUGZILLA_API_URL}/attachment/{att_id}")
                att_resp.raise_for_status()
                att_data = att_resp.json().get("attachments", {}).get(str(att_id), {})
                data = att_data.get("data")
            if data:
                data_bytes = base64.b64decode(data)
                
                if args.e:
                    # Always download without checking
                    logging.info(f"Downloading {filename}")
                    with open(filepath, "wb") as f:
                        f.write(data_bytes)
                    TOTAL_FILES += 1
                    logging.info(f"✅ Downloaded: {filename}")
                else:
                    # Extension and magic number checking
                    if filename.lower().endswith(TARGET_FILE.lower()):
                        logging.info(f"Downloading {filename} directly as it matches the target type.")
                        with open(filepath, "wb") as f:
                            f.write(data_bytes)
                        TOTAL_FILES += 1
                        logging.info(f"✅ Downloaded: {filename}")
                    elif check_magic_num_response(data_bytes, file_extension=TARGET_FILE.lstrip('.')):
                        logging.info(f"File matches magic number for {TARGET_FILE}, downloading...")
                        with open(filepath, "wb") as f:
                            f.write(data_bytes)
                        TOTAL_FILES += 1
                        logging.info(f"✅ Downloaded: {filename}")
                    else:
                        logging.warning(f"⛔ Skipped {filename} due to filetype mismatch.")
        except Exception as e:
            logging.warning(f"❌ Failed to download {att['file_name']}: {e}")

    def search_bugs(query, limit=100):
        url = f"{BUGZILLA_API_URL}/bug"
        all_bugs, offset = [], 0
        while len(all_bugs) < limit:
            params = {
                "quicksearch": query,
                "status": ALL_STATUSES,
                "limit": 20,
                "offset": offset
            }
            try:
                r = requests.get(url, params=params)
                r.raise_for_status()
                bugs = r.json().get("bugs", [])
                if not bugs:
                    break
                all_bugs.extend(bugs)
                offset += 20
            except Exception as e:
                logging.warning(f"Bug search failed: {e}")
                break
        return all_bugs[:limit]

    # queries = generate_bugzilla_queries(file_format)
    for query in queries:
        logging.info(f"Searching Bugzilla with query: {query}")
        bugs = search_bugs(query, limit=NUM_BUGS)
        logging.info(f"Found {len(bugs)} bugs for query: {query}")
        for bug in bugs:
            attachments = get_attachments(bug["id"]).get(str(bug["id"]), [])
            for att in attachments:
                logging.info(f"Processing attachment: {att.get('file_name', 'Unknown')}")
                download_attachment(att)

# === MAIN FLOW ===
if __name__ == "__main__":
    try:
        start_total = time.time()
        search_texts = generate_search_query_from_file(TARGET_FILE)
        search_texts += f"\n{TARGET_FILE}" 
        logging.info(f"Generated search queries:\n{search_texts}")
        queries = search_texts.split("\n")
    except Exception as e:
        logging.warning(f"Falling back to using file type as query due to error: {e}")
        queries = [TARGET_FILE]

    if args.source in ["launchpad", "both"]:
        logging.info("Running Launchpad flow...")
        start_lp = time.time()
        
        for search_text in queries:
            logging.info(f"Generated query: {search_text}")
            search_and_download_attachments(search_text)
        logging.info(f"Total Launchpad files downloaded: {TOTAL_FILES}")
        end_lp = time.time()
        elapsed_lp = end_lp - start_lp
        logging.info(f"Launchpad flow completed in {elapsed_lp:.2f} seconds")


    if args.source in ["bugzilla", "both"]:
        logging.info("🔍 Running Bugzilla flow...")
        start_bz = time.time()

        run_bugzilla_flow(queries, limit=args.max_limit)
        end_bz = time.time()
        elapsed_bz = end_bz - start_bz
        logging.info(f"⏱️ Bugzilla flow completed in {elapsed_bz:.2f} seconds")

    end_total = time.time()
    total_elapsed = end_total - start_total
    logging.info(f"TOTAL FILES DOWNLOADED: {TOTAL_FILES}")
    logging.info(f"Script finished in {total_elapsed:.2f} seconds")
