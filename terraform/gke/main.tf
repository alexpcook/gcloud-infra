data "google_billing_account" "apc" {
  display_name = "apc"
  open         = true
}

resource "time_static" "creation_time" {}

resource "google_project" "apc" {
  project_id = "apc-${time_static.creation_time.unix}"
  name       = "apc-${time_static.creation_time.unix}"

  billing_account = data.google_billing_account.apc.id

  deletion_policy = "DELETE"
}

resource "google_project_service" "compute" {
  project = google_project.apc.project_id
  service = "compute.googleapis.com"
}

resource "google_project_service" "container" {
  project = google_project.apc.project_id
  service = "container.googleapis.com"
}

data "google_compute_zones" "available" {
  project = google_project.apc.project_id

  depends_on = [
    google_project_service.compute
  ]
}

locals {
  gke_cluster_zone = data.google_compute_zones.available.names[0]
}

resource "google_service_account" "gke" {
  project = google_project.apc.project_id

  account_id   = "gke-sa"
  display_name = "GKE Service Account"
}

resource "google_project_iam_member" "gke_default_node_service_account" {
  project = google_project.apc.project_id
  role    = "roles/container.defaultNodeServiceAccount"
  member  = "serviceAccount:${google_service_account.gke.email}"
}

resource "google_container_cluster" "primary" {
  project = google_project.apc.project_id

  name     = "primary"
  location = local.gke_cluster_zone

  remove_default_node_pool = true
  initial_node_count       = 1

  maintenance_policy {
    daily_maintenance_window {
      start_time = "08:00"
    }
  }

  deletion_protection = false
}

resource "google_container_node_pool" "default" {
  project = google_project.apc.project_id

  name     = "default"
  location = local.gke_cluster_zone
  cluster  = google_container_cluster.primary.name

  node_config {
    spot = true

    machine_type = "e2-small"
    disk_size_gb = 12

    service_account = google_service_account.gke.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }

  autoscaling {
    min_node_count = 0
    max_node_count = 1
  }
}
