# AWS Setup Instructions

Follow these steps to create an IAM user with the correct permissions and access keys, configure S3, and prepare for Athena queries

## 1 Create AWS User 
1. Open the [IAM Console](https://console.aws.amazon.com/iam/)
2. In the sidebar, create a new IAM user by going to **Users → Add users**
3. Go to IAM Console → Users → Your user → security credentials
4. Under Console sign-in go to Enable console access  and add the password to be used latter with this user

   
## 2 Create Access Key
1. Go to the Security credentials > Scroll down to Access keys →  Create access key
2. Choose Application running outside AWS  → Create access key
3. Save your access key ID and secret key securely (you won’t see the secret key again).
5. Go to IAM Console → Users → Your user → Permissions tab to add permission 
   1. go to Permissions tab →  Add permissions → Attach policies directly
   2. Search for and add `AmazonAthenaFullAccess` and  `AmazonS3FullAccess`  (or `AmazonS3ReadOnlyAccess` if you want more limited access)


## 3 Create a Bucket:
### 3a. AWS Management Console
1. Login using the Account ID, Your new user, password
2. Go to S3 Console: https://s3.console.aws.amazon.com/s3/home
3. Click "Create bucket"
4. Fill in bucket details:
   1. Bucket name: Choose a unique name (e.g., fuzzing-query-results)
   2. Region: Match your Athena region
5. Leave default settings, or:
   1. Uncheck “Block all public access” (not recommended unless needed)
   2. Enable versioning (optional but useful)
6. Click "Create bucket"
7. ✅ Done — your bucket URI will be: `s3://fuzzing-query-results/`

### 3b. AWS CLI
1. Export your credentials:
```bash
export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="YOUR_SECRET_ACCESS_KEY"
export AWS_SESSION_TOKEN="YOUR_SESSION_TOKEN"
```
2. Create the bucket
```bash
aws s3api create-bucket \
  --bucket your_bucket_name \
  --region your_region_name \
  --create-bucket-configuration LocationConstraint=your_region_name
```
