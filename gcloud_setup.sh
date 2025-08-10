#!/bin/bash
set -eux

gcloud auth application-default login

PROJECT_ID="apc-$(date +%s)"
gcloud projects create $PROJECT_ID

echo "project = \"$PROJECT_ID\"" > terraform/terraform.tfvars
