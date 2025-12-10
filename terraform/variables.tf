variable "render_api_key" {
  description = "Render API key (set via TF_VAR_render_api_key or tfvars; do not commit real value)."
  type        = string
  sensitive   = true
}

variable "repo_url" {
  description = "Git repository URL Render pulls from."
  type        = string
}

variable "repo_branch" {
  description = "Git branch to deploy."
  type        = string
  default     = "main"
}

variable "render_owner_id" {
  description = "Render owner/team ID"
  type        = string
}
