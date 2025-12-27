############################
# n8n – Cloud Run v2
############################

resource "google_cloud_run_v2_service" "n8n" {
  name     = local.n8n_service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.n8n.email

    scaling {
      max_instance_count = 1
    }

    containers {
      image = var.n8n_image

      ports {
        container_port = 5678
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      dynamic "env" {
        for_each = toset([
          "N8N_BASIC_AUTH_ACTIVE",
          "N8N_BASIC_AUTH_USER",
          "N8N_BASIC_AUTH_PASSWORD",
          "N8N_ENCRYPTION_KEY",
          "WEBHOOK_URL"
        ])
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.n8n[env.key].secret_id
              version = "latest"
            }
          }
        }
      }

      volume_mounts {
        name       = "n8n-data"
        mount_path = "/home/node/.n8n"
      }
    }

    volumes {
      name = "n8n-data"
      gcs {
        bucket    = google_storage_bucket.n8n.name
        read_only = false
      }
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [
    google_project_service.required,
    google_secret_manager_secret_version.n8n,
    google_storage_bucket.n8n
  ]
}

############################
# LangGraph – Cloud Run v1
############################

resource "google_cloud_run_service" "langgraph" {
  name     = local.langgraph_service_name
  location = var.region

  metadata {
    annotations = {
      "run.googleapis.com/ingress"      = "all"
      "run.googleapis.com/launch-stage" = "GA"
    }
  }

  template {
    spec {
      service_account_name = google_service_account.langgraph.email

      containers {
        image = var.langgraph_image

        ports {
          container_port = 8000
        }

        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }

        dynamic "env" {
          for_each = toset([
            "OPENAI_API_KEY"
          ])
          content {
            name = env.key
            value_from {
              secret_key_ref {
                name = google_secret_manager_secret.langgraph[env.key].secret_id
                key  = "latest"
              }
            }
          }
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true

  depends_on = [
    google_project_service.required,
    google_secret_manager_secret_version.langgraph
  ]
}

############################
# Public Access
############################

resource "google_cloud_run_v2_service_iam_member" "n8n_public_invoker" {
  name     = google_cloud_run_v2_service.n8n.name
  location = google_cloud_run_v2_service.n8n.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_service_iam_member" "langgraph_public_invoker" {
  service  = google_cloud_run_service.langgraph.name
  location = google_cloud_run_service.langgraph.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
