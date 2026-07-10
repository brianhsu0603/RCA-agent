resource "aws_secretsmanager_secret" "backend_env" {
  name = "${var.project_name}/backend-env"
}

resource "aws_secretsmanager_secret_version" "backend_env" {
  secret_id = aws_secretsmanager_secret.backend_env.id

  secret_string = jsonencode({
    DATABASE_URL      = "postgresql+psycopg2://${aws_db_instance.this.username}:${random_password.db.result}@${aws_db_instance.this.address}:5432/${aws_db_instance.this.db_name}"
    REDIS_URL         = "redis://${aws_elasticache_cluster.this.cache_nodes[0].address}:6379/0"
    ANTHROPIC_API_KEY = var.anthropic_api_key
    SLACK_BOT_TOKEN   = var.slack_bot_token
    TRIAGE_MODEL      = var.triage_model
    RCA_MODEL         = var.rca_model
  })
}
