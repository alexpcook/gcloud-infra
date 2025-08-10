resource "google_project" "gke" {
  name       = "GKE Experiment"
  project_id = "gke-experiment"
  org_id     = "0"
}
