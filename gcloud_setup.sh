#!/bin/bash
set -eux

# Default app credentials
gcloud auth application-default login

# Project
PROJECT_ID="apc-$(date +%s)"
gcloud projects create $PROJECT_ID

# Service account
gcloud iam service-accounts create terraform-sa \
    --project $PROJECT_ID \
    --display-name="Terraform Service Account" \
    --description="Service account for Terraform infrastructure management"

# Service account permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:terraform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/editor"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:terraform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/container.admin"

# Service account key
KEY_FILE="$(pwd)/terraform-sa-key.json"
gcloud iam service-accounts keys create $KEY_FILE \
    --iam-account=terraform-sa@$PROJECT_ID.iam.gserviceaccount.com
chmod 600 $KEY_FILE
