# Google Cloud Storage Setup Guide

This guide explains how to set up Google Cloud Storage integration for the PDF upload functionality.

## Prerequisites

1. **Google Cloud Project**: You need a Google Cloud project with billing enabled
2. **Google Cloud Storage Bucket**: The bucket `agent-binod` should exist (as referenced in the URL)
3. **Authentication**: Service account or application default credentials

## Setup Steps

### 1. Create a Google Cloud Storage Bucket

If the bucket `agent-binod` doesn't exist, create it:

```bash
# Install Google Cloud CLI if not already installed
# https://cloud.google.com/sdk/docs/install

# Set your project ID
gcloud config set project YOUR_PROJECT_ID

# Create the bucket
gsutil mb gs://agent-binod

# Make the bucket publicly readable (optional, for public URLs)
gsutil iam ch allUsers:objectViewer gs://agent-binod
```

### 2. Set Up Authentication

#### Option A: Application Default Credentials (Recommended for Development)

```bash
# Authenticate with your Google account
gcloud auth application-default login

# Set the project ID
gcloud config set project YOUR_PROJECT_ID
```

#### Option B: Service Account (Recommended for Production)

1. Create a service account:
```bash
gcloud iam service-accounts create pdf-uploader \
    --display-name="PDF Upload Service Account"
```

2. Grant Storage Object Admin role:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:pdf-uploader@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

3. Download the service account key:
```bash
gcloud iam service-accounts keys create service-account-key.json \
    --iam-account=pdf-uploader@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

4. Set the environment variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

### 3. Environment Variables

Set the following environment variables:

```bash
# Required: Your Google Cloud Project ID
export GOOGLE_CLOUD_PROJECT_ID="your-project-id"

# Optional: Path to service account key (if using service account)
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

### 4. Test the Setup

Run the test script to verify everything works:

```bash
cd agent/manager/tools
python test_gcs_upload.py
```

## Configuration

The PDF upload functionality is configured in `pdf_creator.py`:

- **Bucket Name**: `GCS_BUCKET_NAME = "agent-binod"` (change if needed)
- **Project ID**: Set via `GOOGLE_CLOUD_PROJECT_ID` environment variable
- **File Path**: PDFs are stored in `health_roadmaps/` folder with unique filenames

## File Naming Convention

Uploaded PDFs follow this naming pattern:
```
health_roadmaps/{user_name}_{timestamp}_{uuid}.pdf
```

Example: `health_roadmaps/John_Doe_20241221_143052_a1b2c3d4.pdf`

## Fallback Behavior

If Google Cloud Storage upload fails, the function will:
1. Log the error
2. Return a base64-encoded PDF instead of a URL
3. Continue functioning normally

## Troubleshooting

### Common Issues

1. **Authentication Error**: Ensure you're authenticated with `gcloud auth application-default login`
2. **Bucket Not Found**: Verify the bucket `agent-binod` exists in your project
3. **Permission Denied**: Check that your account has Storage Object Admin permissions
4. **Project ID Not Set**: Set the `GOOGLE_CLOUD_PROJECT_ID` environment variable

### Debug Mode

To see detailed error messages, check the console output when the PDF creator tool runs.

## Security Considerations

- The uploaded PDFs are made publicly accessible
- Consider implementing access controls if needed
- Service account keys should be kept secure and not committed to version control
- Use IAM roles with minimal required permissions 