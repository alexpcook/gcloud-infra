variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-west1"
}

variable "project" {
  description = "The GKE cluster project ID"
  type        = string
}

variable "location" {
  description = "The GKE cluster location (region or zone)"
  type        = string
}

variable "cluster" {
  description = "The GKE cluster name"
  type        = string
}
