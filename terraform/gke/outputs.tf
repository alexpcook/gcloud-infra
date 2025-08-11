# Add this to your Terraform configuration
output "kubectl_connection_command" {
  value = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --zone=${google_container_cluster.primary.location} --project=${google_project.apc.project_id}"
}
