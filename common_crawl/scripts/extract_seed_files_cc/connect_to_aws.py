import boto3
import logging
import os
from pyathena import connect
from botocore.exceptions import ClientError

# region_name = "us-east-1"
region_name = os.environ.get('AWS_REGION_NAME')
database_name = "ccindex"
table_name = "ccindex"
s3_location = "s3://commoncrawl/cc-index/table/cc-main/warc/"

# Athena query runner
# def run_athena_query(query, s3_output):
#    check_aws_credentials()
#    conn = connect(region_name=region_name, s3_staging_dir=s3_output)
#    cursor = conn.cursor()
#    cursor.execute(query)
#    return cursor.fetchall()

def run_athena_query(query, s3_output):
    check_aws_credentials()
    session = boto3.Session(
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
        region_name=region_name
    )
    conn = connect(region_name=region_name, s3_staging_dir=s3_output, boto3_session=session)
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()

# Glue catalog client
glue = boto3.client("glue", region_name=region_name)

def table_exists():
    try:
        glue.get_table(DatabaseName=database_name, Name=table_name)
        logging.info(f"Table {database_name}.{table_name} already exists.")
        return True
    except glue.exceptions.EntityNotFoundException:
        logging.info(f"Table {database_name}.{table_name} does not exist.")
        return False

def create_database_if_not_exists():
    try:
        glue.create_database(DatabaseInput={"Name": database_name})
        logging.info(f"Database {database_name} created.")
    except glue.exceptions.AlreadyExistsException:
        logging.info(f"Database {database_name} already exists.")

def create_table():
    table_input = {
        "Name": table_name,
        "TableType": "EXTERNAL_TABLE",
        "Parameters": {
            "EXTERNAL": "TRUE",
            "classification": "parquet"
        },
        "StorageDescriptor": {
            "Columns": [
                {"Name": "url_surtkey", "Type": "string"},
                {"Name": "url", "Type": "string"},
                {"Name": "url_host_name", "Type": "string"},
                {"Name": "url_host_tld", "Type": "string"},
                {"Name": "url_host_2nd_last_part", "Type": "string"},
                {"Name": "url_host_3rd_last_part", "Type": "string"},
                {"Name": "url_host_4th_last_part", "Type": "string"},
                {"Name": "url_host_5th_last_part", "Type": "string"},
                {"Name": "url_host_registry_suffix", "Type": "string"},
                {"Name": "url_host_registered_domain", "Type": "string"},
                {"Name": "url_host_private_suffix", "Type": "string"},
                {"Name": "url_host_private_domain", "Type": "string"},
                {"Name": "url_host_name_reversed", "Type": "string"},
                {"Name": "url_protocol", "Type": "string"},
                {"Name": "url_port", "Type": "int"},
                {"Name": "url_path", "Type": "string"},
                {"Name": "url_query", "Type": "string"},
                {"Name": "fetch_time", "Type": "timestamp"},
                {"Name": "fetch_status", "Type": "int"},
                {"Name": "fetch_redirect", "Type": "string"},
                {"Name": "content_digest", "Type": "string"},
                {"Name": "content_mime_type", "Type": "string"},
                {"Name": "content_mime_detected", "Type": "string"},
                {"Name": "content_charset", "Type": "string"},
                {"Name": "content_languages", "Type": "string"},
                {"Name": "content_truncated", "Type": "string"},
                {"Name": "warc_filename", "Type": "string"},
                {"Name": "warc_record_offset", "Type": "bigint"},
                {"Name": "warc_record_length", "Type": "int"},
                {"Name": "warc_segment", "Type": "string"}
            ],
            "Location": s3_location,
            "InputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
            "OutputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
            "SerdeInfo": {
                "SerializationLibrary": "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe",
                "Parameters": {"serialization.format": "1"}
            },
            "StoredAsSubDirectories": False
        },
        "PartitionKeys": [
            {"Name": "crawl", "Type": "string"},
            {"Name": "subset", "Type": "string"}
        ]
    }

    glue.create_table(DatabaseName=database_name, TableInput=table_input)
    logging.info(f"Created Glue table {database_name}.{table_name}")

def ensure_bucket_exists(bucket_name, region_name):
    """Check if the S3 bucket exists in the correct account and region."""
    s3 = boto3.client("s3", region_name=region_name)
    try:
        resp = s3.get_bucket_location(Bucket=bucket_name)
        bucket_region = resp.get("LocationConstraint") or "us-east-1"
        if bucket_region != region_name:
            raise ValueError(
                f"Bucket '{bucket_name}' is in region '{bucket_region}', but Athena is in '{region_name}'."
            )
        logging.info(f"Bucket '{bucket_name}' exists in region '{bucket_region}'.")
    except s3.exceptions.NoSuchBucket:
        raise ValueError(f"Bucket '{bucket_name}' does not exist in this AWS account.")
    except Exception as e:
        raise RuntimeError(f"Error checking bucket: {e}")

def check_aws_credentials():
    required_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        raise RuntimeError(
            f"Missing AWS environment variables: {', '.join(missing)}\n"
            f"Please export your AWS credentials before running.\n"
            f"Example:\n"
            f"    export AWS_ACCESS_KEY_ID=...\n"
            f"    export AWS_SECRET_ACCESS_KEY=...\n"
            f"    export AWS_SESSION_TOKEN=... (optional, only needed for sso or temporary credentials)\n"
        )

    sts = boto3.client("sts", region_name=os.environ.get("AWS_REGION_NAME", "us-west-2"))
    try:
        identity = sts.get_caller_identity()
        logging.info(
            f"AWS credentials valid. Account: {identity['Account']}, ARN: {identity['Arn']}"
        )
    except ClientError as e:
        if e.response["Error"]["Code"] in ("ExpiredToken", "ExpiredTokenException"):
            raise RuntimeError(
                "AWS credentials have expired. Please refresh them from AWS Access Portal."
            )
        elif e.response["Error"]["Code"] == "UnrecognizedClientException":
            raise RuntimeError(
                "AWS credentials are invalid. Make sure you copied all three values from AWS Access Portal."
            )
        else:
            raise

def ensure_table_and_repair():
    create_database_if_not_exists()
    if not table_exists():
        create_table()
    
    bucket_name = os.environ.get('AWS_BUCKET_NAME')
    ensure_bucket_exists(bucket_name, region_name)

    # Run MSCK REPAIR TABLE via Athena to load partitions
    s3_output = f"s3://{bucket_name}/athena-results/"  # Replace with your real S3 staging path
    run_athena_query(f"MSCK REPAIR TABLE {database_name}.{table_name}", s3_output)
    logging.info("MSCK REPAIR TABLE executed.")
