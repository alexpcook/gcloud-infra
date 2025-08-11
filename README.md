# GCloud Infrastructure

A two-tier Terraform configuration for deploying Google Kubernetes Engine (GKE) clusters and applications on Google Cloud Platform.

## What This Does

This project provisions:

- A GKE cluster with autoscaling and cost-optimized spot instances
- Dynamic Kubernetes application deployments from YAML manifests
- Automatic namespace creation based on directory structure

## Prerequisites

- [Terraform](https://terraform.io/downloads) >= 1.0
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- GCP project with billing enabled
- Authentication configured (`gcloud auth application-default login`)

## Quick Start

1. **Deploy the GKE cluster:**

   ```bash
   cd terraform/gke
   terraform init
   terraform apply
   ```

2. **Connect to your cluster:**

   ```bash
   # Get the connection command from terraform output
   terraform output kubectl_connection_command
   # Run the displayed command
   ```

3. **Deploy applications:**

   ```bash
   cd ../k8s
   terraform init
   # Set required variables (project, location, cluster from GKE output)
   terraform apply
   ```

## Project Structure

```tree
terraform/
├── gke/           # GKE cluster infrastructure
└── k8s/           # Kubernetes applications
    └── apps/      # Application manifests (auto-deployed)
        └── nginx/ # Example application
```

## Adding Applications

Drop YAML manifests into `terraform/k8s/apps/[app-name]/` and run `terraform apply`. The namespace will be created automatically.

## Cost Optimization

- Uses e2-small spot instances
- Autoscales from 0-1 nodes
- Designed for development/testing environments

---

*For detailed development guidance, architecture details, and troubleshooting, see [CLAUDE.md](CLAUDE.md).*
