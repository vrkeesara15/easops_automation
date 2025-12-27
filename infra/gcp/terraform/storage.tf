resource "google_storage_bucket" "n8n" {
  name     = local.n8n_bucket_name
  location = var.region

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  depends_on = [google_project_service.required]
}
