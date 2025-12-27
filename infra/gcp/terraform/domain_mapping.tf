resource "google_cloud_run_domain_mapping" "n8n" {
  provider = google-beta

  location = var.region
  name     = var.n8n_domain

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_v2_service.n8n.name
  }

  depends_on = [google_cloud_run_v2_service.n8n]
}

resource "google_cloud_run_domain_mapping" "langgraph" {
  provider = google-beta

  location = var.region
  name     = var.langgraph_domain

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_service.langgraph.name
  }

  depends_on = [google_cloud_run_service.langgraph]
}
