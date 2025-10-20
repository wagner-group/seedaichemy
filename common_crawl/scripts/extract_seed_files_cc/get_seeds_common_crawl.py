import os
import argparse
from urllib.parse import urlparse
import pandas as pd
import requests
import logging
from pyathena import connect
from pyathena.pandas.cursor import PandasCursor
from concurrent.futures import ThreadPoolExecutor, as_completed
from connect_to_aws import ensure_table_and_repair
import sys


# Set up logging

LOG_FILE = "common_crawl/script_logs.txt"  # Log file path
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler(LOG_FILE),
    logging.StreamHandler()  # Optionally log to the console as well
])
# Load AWS credentials and region from environment variables
aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')    
aws_session_token = os.environ.get('AWS_SESSION_TOKEN')
region_name = os.environ.get('AWS_REGION_NAME')
bucket_name = os.environ.get('AWS_BUCKET_NAME')

# Ensure environment variables are set
if not all([aws_access_key, aws_secret_key, region_name]):
    logging.error("AWS credentials or region not set properly. Exiting.")
    exit(1)

# Argument parsing function
def get_args():
    parser = argparse.ArgumentParser(description="Retrieve and download files from Common Crawl.")
    parser.add_argument("file_type", help="The type of the seed file or the input format to query.", type=str)
    parser.add_argument("--limit", help="Number of records to fetch (default: 10000)", type=int, default=10000)
    parser.add_argument("--output", help="Output folder for downloaded files.", type=str, default="seed_files")
    return parser.parse_args()

# Athena connection function
def connect_to_athena():
    # s3_staging_dir = bucket_name 
    s3_staging_dir = f"s3://{bucket_name}/athena-results/" 
    conn = connect(
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        aws_session_token=aws_session_token,
        s3_staging_dir=s3_staging_dir,
        region_name=region_name,
        cursor_class=PandasCursor  # Returns results as a DataFrame
    )
    return conn

# Athena query function
def run_query(data_type, limit=10000):
    conn = None
    while conn is None:
        conn = connect_to_athena()
        #add a filter for files to be less than 3 GB
        query = f"""
        SELECT url, warc_filename, warc_record_offset, warc_record_length, 
            content_mime_detected, content_languages
        FROM ccindex.ccindex 
        WHERE crawl = 'CC-MAIN-2025-08' 
        AND subset = 'warc' 
        AND content_mime_type = '{data_type}'
        AND warc_record_length < 3221225472
        LIMIT {limit};
        """
        try:
            df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            logging.error(f"Error running Athena query: {str(e)}")
            return None

# Download function for files with concurrency
def download_file(url, file_format, output_folder, index):
    headers = {
         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    try:
        parsed_url = urlparse(url)
        original_filename = os.path.basename(parsed_url.path)
        sanitized_file_format = file_format.replace('/', '__').replace('+', '_')
        filename = os.path.join(output_folder, f"{index}_{sanitized_file_format}_{original_filename}")
        with requests.get(url, headers=headers, allow_redirects=True, timeout=30, stream=True) as response:
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # filter out keep-alive chunks
                            f.write(chunk)
                logging.info(f"Downloaded: {filename}")
                return True
            else:
                logging.warning(f"Failed to download {url} - Status code: {response.status_code}")
                return False
    except requests.exceptions.RequestException as req_err: # Catch specific requests errors
        logging.error(f"Network/Request error downloading {url}: {req_err}")
        return False
    except Exception as e:
        logging.error(f"Error downloading {url}: {str(e)}")
        return False

# Function to handle multiple downloads concurrently
def download_files_concurrently(df, file_format, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = []
        for i, url in enumerate(df['url']):
            futures.append(executor.submit(download_file, url, file_format, output_folder, i))
        
        for future in as_completed(futures):
            if future.result():
                success_count += 1
            else:
                fail_count += 1

    logging.info(f"Download completed. Success: {success_count}, Fail: {fail_count}")
    return success_count, fail_count

# Read file formats from a mapping file
def get_file_formats_matching(file_format):
    try:
        with open('common_crawl/scripts/extract_seed_files_cc/files_formats_cc.txt') as f:
            files_format_mapping = f.read().splitlines()
        return [line for line in files_format_mapping if file_format in line]
    except Exception as e:
        logging.error(f"Error reading file format mappings: {str(e)}")
        return []

# Main function
def main():
    args = get_args()
    target_file_format = args.file_type
    output_folder = args.output
    matched_files_format = get_file_formats_matching(target_file_format)
    ensure_table_and_repair()  # Ensure the Athena table is created and repaired
    if not matched_files_format:
        logging.error(f"No file formats found matching '{target_file_format}'. Exiting.")
        exit(1)

    logging.info(f"Matched file formats: {matched_files_format}")

    for file_format in matched_files_format:
        logging.info(f"Processing file format: {file_format}")
        df_result = run_query(file_format, args.limit)

        if df_result is not None:
            df_result.to_csv(f"common_crawl/{file_format.replace('+','_').replace('/','__')}.csv")
            success_count, fail_count = download_files_concurrently(df_result, target_file_format, output_folder)
            logging.info(f"Collected data for format '{file_format}': {success_count} successfully downloaded, {fail_count} failed.")
        else:
            logging.warning(f"No data returned for format: {file_format}")

if __name__ == "__main__":
    main()
