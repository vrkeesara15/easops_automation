output "n8n_service_url" {
  value       = google_cloud_run_v2_service.n8n.uri
  description = "Default Cloud Run URL for n8n."
}

output "langgraph_service_url" {
  value       = google_cloud_run_service.langgraph.status[0].url
  description = "Default Cloud Run URL for LangGraph."
}

output "n8n_domain_records" {
  value       = google_cloud_run_domain_mapping.n8n.status[0].resource_records
  description = "DNS records required for automation.easops.com."
}

output "langgraph_domain_records" {
  value       = google_cloud_run_domain_mapping.langgraph.status[0].resource_records
  description = "DNS records required for agents.easops.com."
}

output "n8n_bucket_name" {
  value       = google_storage_bucket.n8n.name
  description = "GCS bucket used for n8n persistent data."
}
