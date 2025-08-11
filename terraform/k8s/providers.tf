provider "google" {
  project = var.project
  region  = var.region
}

data "google_container_cluster" "main" {
  name     = var.cluster
  location = var.location
}

data "google_client_config" "provider" {}

provider "kubernetes" {
  host  = "https://${data.google_container_cluster.main.endpoint}"
  token = data.google_client_config.provider.access_token
  cluster_ca_certificate = base64decode(
    data.google_container_cluster.main.master_auth[0].cluster_ca_certificate
  )
}
