# IRSA role for the AWS Load Balancer Controller (installed via Helm in the
# `kube-system` namespace, service account `aws-load-balancer-controller` -
# see DEPLOYMENT.md). Uses the community module's built-in policy attachment
# for the controller's well-known IAM policy.
module "alb_controller_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = ">= 5.30, < 6.0"

  role_name = "${var.project_name}-alb-controller"

  attach_load_balancer_controller_policy = true

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:aws-load-balancer-controller"]
    }
  }
}

# IRSA role for the External Secrets Operator, scoped to read-only access on
# just the one secret this app needs (k8s/cluster-secret-store.yaml references
# this role via the `external-secrets:external-secrets` service account).
data "aws_iam_policy_document" "eso_secrets_read" {
  statement {
    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = [aws_secretsmanager_secret.backend_env.arn]
  }
}

resource "aws_iam_policy" "eso_secrets_read" {
  name   = "${var.project_name}-eso-secrets-read"
  policy = data.aws_iam_policy_document.eso_secrets_read.json
}

module "eso_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = ">= 5.30, < 6.0"

  role_name = "${var.project_name}-external-secrets"

  role_policy_arns = {
    secrets_read = aws_iam_policy.eso_secrets_read.arn
  }

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["external-secrets:external-secrets"]
    }
  }
}
