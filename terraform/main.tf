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
  name               = "oss-taapp-hw3-api-fix"
  plan               = "starter"
  region             = "virginia"
  start_command      = "uvicorn ai_chat_service.main:app --host 0.0.0.0 --port $PORT"

  runtime_source = {
    native_runtime = {
      auto_deploy   = true
      branch        = var.repo_branch
      build_command = "uv sync --all-packages --extra dev"
      repo_url = var.repo_url
      runtime  = "node"
    }
  }

  env_vars = {
    CLAUDE_API_KEY = var.claude_api_key
  }
}
