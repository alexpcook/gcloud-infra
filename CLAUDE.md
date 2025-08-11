# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This repository contains Google Cloud infrastructure configuration using Terraform, organized into two main components:

### Two-Tier Terraform Structure

- **GKE Infrastructure** (`terraform/gke/`): Creates GCP project, enables APIs, provisions GKE cluster with autoscaling node pool
- **Kubernetes Resources** (`terraform/k8s/`): Deploys applications to the GKE cluster using dynamic manifest processing

The architecture follows a separation of concerns where the GKE layer handles the underlying infrastructure and the K8s layer manages application deployments.

### Dynamic Kubernetes Deployment Pattern

The K8s configuration uses a sophisticated pattern in `terraform/k8s/main.tf:1-23`:

- Uses `fileset()` to discover all YAML manifests in the `apps/` directory
- Automatically creates namespaces based on directory structure (`apps/nginx/` creates `nginx` namespace)
- Dynamically processes all YAML files using `kubernetes_manifest` resource with `for_each`

This pattern allows adding new applications by simply placing YAML files in appropriately named subdirectories under `apps/`.

## Common Development Commands

### GKE Cluster Management

```bash
# Initialize and deploy GKE cluster
cd terraform/gke
terraform init
terraform plan
terraform apply

# Get kubectl connection command (from terraform output)
terraform output kubectl_connection_command
```

### Kubernetes Application Deployment

```bash
# Deploy applications to existing GKE cluster
cd terraform/k8s
terraform init
terraform plan
terraform apply
```

### Required Variables for K8s Deployment

The K8s deployment requires these variables:

- `project`: GKE cluster project ID (e.g., "apc-1754876275")
- `location`: GKE cluster location (e.g., "us-west1-a")
- `cluster`: GKE cluster name (e.g., "primary")

### Adding New Applications

1. Create directory under `terraform/k8s/apps/[app-name]/`
2. Add Kubernetes YAML manifests to the directory
3. Run `terraform apply` - namespace and resources will be created automatically

## Infrastructure Details

### GKE Configuration

- Uses spot instances (e2-small) for cost optimization
- Autoscaling: 0-1 nodes to minimize costs
- Deletion protection disabled for development environments
- Service account with cloud-platform scope

### Kubernetes Resources

- LoadBalancer services for external access
- Resource limits and requests configured for applications
- Automatic namespace creation based on directory structure

## Provider Versions

- Terraform: >= 1.0
- Google provider: ~> 6.47  
- Kubernetes provider: ~> 2.38
