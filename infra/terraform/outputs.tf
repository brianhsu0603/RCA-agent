output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "region" {
  value = var.aws_region
}

output "ecr_backend_repository_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_repository_url" {
  value = aws_ecr_repository.frontend.repository_url
}

output "backend_env_secret_arn" {
  value = aws_secretsmanager_secret.backend_env.arn
}

output "alb_controller_role_arn" {
  value = module.alb_controller_irsa.iam_role_arn
}

output "external_secrets_role_arn" {
  value = module.eso_irsa.iam_role_arn
}

output "github_actions_deploy_role_arn" {
  value = aws_iam_role.github_actions_deploy.arn
}

output "rds_endpoint" {
  value = aws_db_instance.this.address
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.this.cache_nodes[0].address
}
