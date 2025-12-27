locals {
  n8n_service_name       = "n8n"
  langgraph_service_name = "langgraph"

  n8n_bucket_name = "${var.project_id}-n8n-data"

  langgraph_firestore_project_id = var.langgraph_firestore_project_id != "" ? var.langgraph_firestore_project_id : var.project_id

  langgraph_secret_values = merge(
    var.langgraph_secret_values,
    {
      FIRESTORE_PROJECT_ID = local.langgraph_firestore_project_id
    }
  )
}

resource "google_project_service" "required" {
  for_each = toset([
    "run.googleapis.com",
    "firestore.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "storage.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com"
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}
