variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short name used to prefix/tag all resources"
  type        = string
  default     = "rca-agent"
}

variable "cluster_version" {
  description = "EKS control plane version"
  type        = string
  default     = "1.30"
}

variable "node_instance_types" {
  description = "Instance types for the EKS managed node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_min_size" {
  type    = number
  default = 2
}

variable "node_max_size" {
  type    = number
  default = 4
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "db_allocated_storage" {
  type    = number
  default = 20
}

variable "redis_node_type" {
  type    = string
  default = "cache.t4g.micro"
}

variable "anthropic_api_key" {
  description = "Anthropic API key used by the triage and RCA agents"
  type        = string
  sensitive   = true
}

variable "slack_bot_token" {
  description = "Optional Slack bot token for real Slack ingestion"
  type        = string
  default     = ""
  sensitive   = true
}

variable "dd_api_key" {
  description = "Optional Datadog API key for the Datadog Agent DaemonSet (k8s/datadog-agent-daemonset.yaml). Leave blank to leave the Agent unconfigured."
  type        = string
  default     = ""
  sensitive   = true
}

variable "sentry_dsn" {
  description = "Optional Sentry DSN for backend/worker error tracking. Leave blank to leave Sentry disabled."
  type        = string
  default     = ""
  sensitive   = true
}

variable "github_repo" {
  description = "GitHub \"owner/repo\" allowed to assume the CI deploy role via OIDC"
  type        = string
  default     = "brianhsu0603/RCA-agent"
}

variable "triage_model" {
  type    = string
  default = "claude-haiku-4-5-20251001"
}

variable "rca_model" {
  type    = string
  default = "claude-sonnet-5"
}
