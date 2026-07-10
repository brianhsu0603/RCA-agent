module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = ">= 20.0, < 21.0"

  cluster_name    = var.project_name
  cluster_version = var.cluster_version

  cluster_endpoint_public_access = true

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  enable_cluster_creator_admin_permissions = true

  eks_managed_node_groups = {
    default = {
      instance_types = var.node_instance_types
      desired_size   = var.node_desired_size
      min_size       = var.node_min_size
      max_size       = var.node_max_size
    }
  }

  # IRSA (IAM Roles for Service Accounts) is required by the AWS Load Balancer
  # Controller and External Secrets Operator role bindings in iam-irsa.tf.
  enable_irsa = true

  tags = {
    Project = var.project_name
  }
}
