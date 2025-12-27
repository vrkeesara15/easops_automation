resource "google_service_account" "n8n" {
  account_id   = "n8n-sa"
  display_name = "n8n Cloud Run service account"
}

resource "google_service_account" "langgraph" {
  account_id   = "langgraph-sa"
  display_name = "LangGraph Cloud Run service account"
}

resource "google_project_iam_member" "n8n_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.n8n.email}"
}

resource "google_project_iam_member" "langgraph_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.langgraph.email}"
}

resource "google_project_iam_member" "langgraph_firestore_access" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.langgraph.email}"
}

resource "google_storage_bucket_iam_member" "n8n_bucket_admin" {
  bucket = google_storage_bucket.n8n.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.n8n.email}"
}
