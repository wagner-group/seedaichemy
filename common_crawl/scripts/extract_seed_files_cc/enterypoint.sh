#!/bin/bash
# pip install boto3 pyathena

# Export AWS credentials and region

export AWS_ACCESS_KEY_ID="your_access_key_id_here"
export AWS_SECRET_ACCESS_KEY="your_secret_access_key_here"

export AWS_REGION_NAME="us-east-1"
export AWS_BUCKET_NAME="s3://your_bucket_name_here"

# Run the Python script with arguments
python get_seeds_common_crawl.py "bin" --limit 10