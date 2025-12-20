terraform {
  required_providers {
    render = {
      source = "render-oss/render"
      version = "1.8.0"
    }
  }
}

provider "render" {
  api_key = var.render_api_key
  owner_id = var.render_owner_id
}

resource "render_web_service" "web" {
  name               = "oss-taapp-hw3"
  plan               = "starter"
  region             = "virginia"
  start_command      = "uvicorn smart_chat_bot.main:app --host 0.0.0.0 --port $PORT"

  runtime_source = {
    native_runtime = {
      auto_deploy   = true
      branch        = var.repo_branch
      build_command = "uv sync --all-packages --extra dev"
      repo_url = var.repo_url
      runtime  = "python"
    }
  }

  env_vars = {
    ANTHROPIC_API_KEY      = { value = var.claude_api_key }
    CHAT_PROVIDER          = { value = var.chat_provider }
    CHAT_CHANNEL_IDS       = { value = var.chat_channel_ids }
    DISCORD_BOT_TOKEN      = { value = var.discord_bot_token }
    TICKET_USER_ID         = { value = var.ticket_user_id }
    TICKET_PROJECT_KEY     = { value = var.ticket_project_key }
    JIRA_API_TOKEN         = { value = var.jira_api_token }
    JIRA_API_EMAIL         = { value = var.jira_api_email }
    JIRA_CLOUD_ID          = { value = var.jira_cloud_id }
    JIRA_API_BASE          = { value = var.jira_api_base }
    MAX_MESSAGES_PER_POLL  = { value = tostring(var.max_messages_per_poll) }
    POLL_INTERVAL_SECONDS  = { value = tostring(var.poll_interval_seconds) }
  }
}
