locals {
  billing_budget_pubsub_member = "serviceAccount:service-${var.billing_account_id}@gcp-sa-billingbudgets.iam.gserviceaccount.com"
}

resource "google_pubsub_topic" "billing_alerts" {
  name    = "billing-alerts"
  project = var.project_id
}

resource "google_pubsub_topic_iam_member" "billing_budget_publisher" {
  topic  = google_pubsub_topic.billing_alerts.name
  role   = "roles/pubsub.publisher"
  member = local.billing_budget_pubsub_member
}

resource "google_monitoring_notification_channel" "billing_email" {
  for_each = toset(var.billing_alert_emails)

  display_name = "Billing alerts ${each.value}"
  type         = "email"

  labels = {
    email_address = each.value
  }
}

resource "google_monitoring_notification_channel" "billing_pubsub" {
  display_name = "Billing alerts Pub/Sub"
  type         = "pubsub"

  labels = {
    topic = google_pubsub_topic.billing_alerts.id
  }
}

resource "google_billing_budget" "monthly" {
  billing_account = var.billing_account_id
  display_name    = "Monthly budget for ${var.project_id}"

  amount {
    specified_amount {
      currency_code = "USD"
      units         = var.billing_monthly_budget
    }
  }

  budget_filter {
    projects = ["projects/${var.project_number}"]
  }

  threshold_rules {
    threshold_percent = 0.5
  }

  threshold_rules {
    threshold_percent = 0.75
  }

  threshold_rules {
    threshold_percent = 0.9
  }

  threshold_rules {
    threshold_percent = 1.0
  }

  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "FORECASTED_SPEND"
  }

  all_updates_rule {
    pubsub_topic                   = google_pubsub_topic.billing_alerts.id
    schema_version                 = "1.0"
    disable_default_iam_recipients = true
    monitoring_notification_channels = concat(
      [google_monitoring_notification_channel.billing_pubsub.id],
      [for c in google_monitoring_notification_channel.billing_email : c.id]
    )
  }

  depends_on = [google_pubsub_topic_iam_member.billing_budget_publisher]
}

resource "google_monitoring_alert_policy" "billing_cost_anomaly" {
  display_name = "Billing cost anomaly (daily)"
  combiner     = "OR"

  conditions {
    display_name = "Daily spend > threshold"
    condition_threshold {
      filter          = "metric.type=\"billing.googleapis.com/billing_account/cost\" resource.type=\"billing_account\""
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.billing_daily_anomaly_threshold
      aggregations {
        alignment_period   = "86400s"
        per_series_aligner = "ALIGN_DELTA"
      }
    }
  }

  notification_channels = concat(
    [google_monitoring_notification_channel.billing_pubsub.id],
    [for c in google_monitoring_notification_channel.billing_email : c.id]
  )
}
