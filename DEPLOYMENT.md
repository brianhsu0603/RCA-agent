# Deploying to AWS (EKS)

This deploys `backend` (FastAPI), `worker` (Celery), and `frontend` (React, built
static + nginx) to an EKS cluster, backed by RDS Postgres and ElastiCache Redis
instead of the docker-compose `db`/`redis` containers. Infra is provisioned with
Terraform (`infra/terraform/`); app manifests are plain Kubernetes YAML +
Kustomize (`k8s/`).

**Costs money**: this creates a real EKS cluster, RDS instance, ElastiCache
node, NAT gateway, and ALB - all billable. Don't run `terraform apply` against
an AWS account you don't intend to pay for.

## Prerequisites

- AWS CLI configured with credentials for the target account (`aws sts get-caller-identity` to confirm)
- `terraform` >= 1.7, `kubectl`, `helm`, `docker`
- An Anthropic API key

## 1. Provision AWS infra with Terraform

```
cd infra/terraform
terraform init
terraform apply -var="anthropic_api_key=sk-ant-..." -var="aws_region=us-east-1"
```

Review the plan before confirming - this takes ~15-20 minutes (EKS control
plane + node group + RDS are the slow parts). Note the outputs when done:

```
terraform output
```

You'll need `ecr_backend_repository_url`, `ecr_frontend_repository_url`,
`alb_controller_role_arn`, and `external_secrets_role_arn` below.

## 2. Point kubectl at the new cluster

```
aws eks update-kubeconfig --name rca-agent --region us-east-1
kubectl get nodes   # sanity check
```

## 3. Install cluster add-ons

**AWS Load Balancer Controller** (so `k8s/ingress.yaml` provisions a real ALB):

```
helm repo add eks https://aws.github.io/eks-charts
helm repo update
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=rca-agent \
  --set serviceAccount.create=true \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"="<alb_controller_role_arn>"
```

**External Secrets Operator** (syncs `rca-agent/backend-env` from Secrets
Manager into the `backend-env` K8s Secret that `k8s/backend-deployment.yaml`
etc. consume via `envFrom`):

```
helm repo add external-secrets https://charts.external-secrets.io
helm repo update
helm install external-secrets external-secrets/external-secrets \
  -n external-secrets --create-namespace \
  --set serviceAccount.name=external-secrets \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"="<external_secrets_role_arn>"
```

**metrics-server** (required for `k8s/hpa-backend.yaml`):

```
aws eks create-addon --cluster-name rca-agent --addon-name metrics-server
```

Also double-check `k8s/cluster-secret-store.yaml`'s `region:` field matches
the region you used in Terraform (defaults to `us-east-1` in both places).

## 4. Build and push the first images

```
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker build -t <ecr_backend_repository_url>:initial ./backend
docker push <ecr_backend_repository_url>:initial

docker build -f ./frontend/Dockerfile.prod -t <ecr_frontend_repository_url>:initial ./frontend
docker push <ecr_frontend_repository_url>:initial
```

## 5. Deploy the app

Edit `k8s/kustomization.yaml`'s `images:` section to point `newName` at your
actual ECR repo URLs (from `terraform output`) and set `newTag: initial` to
match step 4. Then:

```
kubectl apply -k k8s/
kubectl -n rca-agent get pods -w   # wait for Running
kubectl -n rca-agent get ingress rca-agent   # ADDRESS column = ALB hostname, may take a few minutes to appear
```

Once the ALB is provisioned, open its hostname in a browser - you should see
the triage queue UI, and API calls should succeed via nginx's `/api` proxy.

## 6. (Optional) Wire up CI/CD

`.github/workflows/deploy.yml` builds+pushes both images on every push to
`main` and re-applies the manifests with the new tag. One manual one-time
step first: create a GitHub OIDC identity provider in the AWS account and an
IAM role trusting it (scoped to `repo:<org>/<repo>:ref:refs/heads/main`) with
permissions to push to both ECR repos and call the EKS API, then set its ARN
as the `AWS_DEPLOY_ROLE_ARN` secret in the GitHub repo settings. This wasn't
automated in Terraform to avoid provisioning GitHub-side OIDC trust for a repo
that may not exist yet / may live under a different AWS account than the one
running this Terraform.

## Adding a custom domain + TLS

Not configured by default (no domain was given). Once you have one: request
an ACM certificate for it, add `alb.ingress.kubernetes.io/certificate-arn` and
a `spec.rules[].host` to `k8s/ingress.yaml`, and point a Route 53 (or other
DNS) record at the ALB hostname.

## Tearing it down

`aws_db_instance.this` has `deletion_protection = true` - set it to `false`
and `terraform apply` once before `terraform destroy` will succeed on it.
Also delete the `k8s` resources first (`kubectl delete -k k8s/`) so the ALB
and any EBS volumes are cleaned up before Terraform removes the VPC/subnets
they live in.
