variable "project_id" {
  type        = string
  description = "GCP project ID."
}

variable "project_number" {
  type        = string
  description = "GCP project number."
}

variable "region" {
  type        = string
  description = "GCP region."
  default     = "us-central1"
}

variable "n8n_domain" {
  type        = string
  description = "Custom domain for n8n UI."
  default     = "automation.easops.com"
}

variable "langgraph_domain" {
  type        = string
  description = "Custom domain for LangGraph API."
  default     = "agents.easops.com"
}

variable "n8n_image" {
  type        = string
  description = "Container image for n8n."
  default     = "n8nio/n8n:latest"
}

variable "langgraph_image" {
  type        = string
  description = "Container image for LangGraph (set by CI/CD)."
}

variable "n8n_basic_auth_active" {
  type        = string
  description = "Enable basic auth for n8n (string for Secret Manager usage)."
  default     = "true"
  sensitive   = true
}

variable "n8n_basic_auth_user" {
  type        = string
  description = "Basic auth username for n8n."
  sensitive   = true
}

variable "n8n_basic_auth_password" {
  type        = string
  description = "Basic auth password for n8n."
  sensitive   = true
}

variable "n8n_encryption_key" {
  type        = string
  description = "n8n encryption key."
  sensitive   = true
}

variable "n8n_webhook_url" {
  type        = string
  description = "Webhook URL for n8n."
  default     = "https://automation.easops.com"
  sensitive   = true
}

variable "langgraph_firestore_project_id" {
  type        = string
  description = "Firestore project ID used by LangGraph. Defaults to project_id when empty."
  default     = ""
  sensitive   = true
}

variable "langgraph_secret_values" {
  type        = map(string)
  description = "Map of LangGraph secret env vars (e.g., OPENAI_API_KEY, GEMINI_API_KEY) to values."
  default     = {}
  sensitive   = true
}

variable "n8n_max_instances" {
  type        = number
  description = "Max instances for n8n Cloud Run service."
  default     = 2
}

variable "langgraph_max_instances" {
  type        = number
  description = "Max instances for LangGraph Cloud Run service."
  default     = 2
}
variable "openai_api_key" {
  description = "OpenAI API key for LangGraph"
  type        = string
  sensitive   = true
  default     = ""
}
