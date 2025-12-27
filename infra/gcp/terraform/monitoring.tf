locals {
  monitoring_notification_channels = var.monitoring_notification_channels
}

resource "google_logging_metric" "n8n_execution_failures" {
  name   = "n8n_execution_failures"
  filter = "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${local.n8n_service_name}\" (severity>=ERROR OR textPayload:\"Execution failed\" OR jsonPayload.message:\"Execution failed\" OR jsonPayload.msg:\"Execution failed\")"

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
    display_name = "n8n execution failures"
  }
}

resource "google_logging_metric" "langgraph_5xx_errors" {
  name   = "langgraph_5xx_errors"
  filter = "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${local.langgraph_service_name}\" httpRequest.status>=500"

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
    display_name = "LangGraph 5xx errors"
  }
}

resource "google_monitoring_alert_policy" "n8n_error_spike" {
  display_name = "n8n execution failures spike"
  combiner     = "OR"

  conditions {
    display_name = "n8n execution failures > 5 in 5m"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.n8n_execution_failures.name}\" resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${local.n8n_service_name}\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }

  notification_channels = local.monitoring_notification_channels
  depends_on            = [google_logging_metric.n8n_execution_failures]
}

resource "google_monitoring_alert_policy" "langgraph_5xx_spike" {
  display_name = "LangGraph 5xx spike"
  combiner     = "OR"

  conditions {
    display_name = "LangGraph 5xx > 10 in 5m"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.langgraph_5xx_errors.name}\" resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${local.langgraph_service_name}\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }

  notification_channels = local.monitoring_notification_channels
  depends_on            = [google_logging_metric.langgraph_5xx_errors]
}

resource "google_monitoring_alert_policy" "n8n_crash_loop" {
  display_name = "n8n container restart surge"
  combiner     = "OR"

  conditions {
    display_name = "n8n start count > 5 in 10m"
    condition_threshold {
      filter          = "metric.type=\"run.googleapis.com/container/start_count\" resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${local.n8n_service_name}\""
      duration        = "600s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5
      aggregations {
        alignment_period   = "600s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }

  notification_channels = local.monitoring_notification_channels
}

resource "google_monitoring_uptime_check_config" "n8n" {
  display_name = "n8n uptime"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path         = "/"
    port         = 443
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = var.n8n_domain
    }
  }
}

resource "google_monitoring_uptime_check_config" "langgraph" {
  display_name = "LangGraph uptime"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path         = "/"
    port         = 443
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = var.langgraph_domain
    }
  }
}

resource "google_logging_project_exclusion" "cloud_run_health_checks" {
  name        = "exclude-cloud-run-health-checks"
  description = "Exclude noisy Cloud Run health checks to keep logging costs low."
  filter      = "resource.type=\"cloud_run_revision\" httpRequest.requestUrl:(\"/health\" OR \"/healthz\" OR \"/_ah/health\")"
  disabled    = false
}
