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

variable "claude_api_key" {
  description = "Anthropic Claude API key for ai_chat_service."
  type        = string
  sensitive   = true
}

variable "render_owner_id" {
  description = "Render owner/team ID"
  type        = string
}

# Smart chat bot / chat client
variable "chat_provider" {
  description = "Chat provider to use (e.g., discord)."
  type        = string
  default     = "discord"
}

variable "chat_channel_ids" {
  description = "Comma-separated list of chat channel IDs."
  type        = string
}

variable "discord_bot_token" {
  description = "Discord bot token for chat client."
  type        = string
  sensitive   = true
}

# Ticketing (Jira)
variable "ticket_user_id" {
  description = "User ID used by the ticket implementation (reporter)."
  type        = string
}

variable "ticket_project_key" {
  description = "Jira project key for ticket creation."
  type        = string
}

variable "jira_api_token" {
  description = "Jira PAT for basic auth (preferred over OAuth if set)."
  type        = string
  sensitive   = true
}

variable "jira_api_email" {
  description = "Email associated with the Jira PAT."
  type        = string
}

variable "jira_cloud_id" {
  description = "Jira Cloud site ID."
  type        = string
}

variable "jira_api_base" {
  description = "Jira API base URL; defaults to https://api.atlassian.com/ex/jira/<cloud_id> if not overridden."
  type        = string
}

# Bot loop tuning
variable "max_messages_per_poll" {
  description = "Max messages fetched per poll."
  type        = number
  default     = 5
}

variable "poll_interval_seconds" {
  description = "Polling interval in seconds."
  type        = number
  default     = 8
}
