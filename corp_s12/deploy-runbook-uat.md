# S12.T06 --- UAT Deploy Runbook (CloudShell build + Fargate service)

Build the image in AWS CloudShell and run it as its own ECS service next
to the vendor's test app. Verified end to end in the trial account
(`ap-southeast-1`, task definition `s12-serving-api:3`, image `dce8d1a`)
on 2026-10-07; this runbook is the same flow with UAT names.

Templates:

```text
infra/aws/uat/task-definition.uat.json
infra/aws/uat/task-role-policy.uat.json
infra/aws/iam/ecs-task-trust-policy.json   (reuse)
```

## 0. Fill These In First

| Placeholder | Meaning | Source |
|---|---|---|
| `<ACCOUNT_ID>` | UAT AWS account | `aws sts get-caller-identity` |
| `<EXECUTION_ROLE_NAME>` | ECS execution role (shared is fine) | infra / existing |
| `<ATHENA_WORKGROUP>` | our own workgroup (recommended) | create, see step 4 |
| `<ATHENA_RESULTS_BUCKET>` | bucket for query results; prefix `athena-results/serving-api/` | infra |
| `<MART_DATA_BUCKET>` / `<MART_DATA_PREFIX>` | S3 location of `rdxuat_db1.rdx_tbl3` | data team |
| `<IMAGE_TAG>` | git short commit of the build | step 1 |
| VPC, private subnets, ALB listener ARN | network | infra |

Confirm with the data team before deploying:

- DynamoDB `rdxuat_tbl1`: PK `citizenId`, SK `accountKey`
  (`accountSubType#accountId`);
- DynamoDB `rdxuat_tbl2`: PK `accountId`, SK
  `accountSubType`; attributes `institutionName`, `lastAvailable*`;
- Athena `rdxuat_db1.rdx_tbl3` columns include
  `transactionInformation`, `debtorAccountId`, `merchantNameEn`.

## 1. Package The Source (local machine)

```bash
cd sandbox/s12-serving-api-fargate/deliverables
git rev-parse --short HEAD                     # -> IMAGE_TAG
zip -r ../serving-api-src.zip Dockerfile requirements.txt app.py \
  endpoint_registry.py endpoint_handler_template.py connectors handlers \
  -x '*/__pycache__/*'
```

Fill the placeholders in the two UAT templates, then upload them and
the trust policy as well (steps 4--5 read them from the CloudShell home):

```text
infra/aws/uat/task-definition.uat.json
infra/aws/uat/task-role-policy.uat.json
infra/aws/iam/ecs-task-trust-policy.json
```

Upload `serving-api-src.zip` in CloudShell (Actions -> Upload file).
CloudShell is x86_64, matching `runtimePlatform.cpuArchitecture`.

## 2. Build And Check In CloudShell

```bash
export AWS_REGION=ap-southeast-7 AWS_DEFAULT_REGION=ap-southeast-7
IMAGE_TAG=<IMAGE_TAG>
mkdir -p ~/serving-api && cd ~/serving-api && unzip -o ~/serving-api-src.zip
docker build -t rdx-serving-api:$IMAGE_TAG .
docker run --rm rdx-serving-api:$IMAGE_TAG sh -c 'python --version; id -u'
# expect: Python 3.11.x, 10001
```

Docker space in CloudShell is small; `docker system prune -f` if a
build fails for disk space.

## 3. Push To ECR

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REG=$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
aws ecr create-repository --repository-name rdx-serving-api \
  --image-scanning-configuration scanOnPush=true      # first time only
aws ecr get-login-password | docker login --username AWS --password-stdin $REG
docker tag rdx-serving-api:$IMAGE_TAG $REG/rdx-serving-api:$IMAGE_TAG
docker push $REG/rdx-serving-api:$IMAGE_TAG
```

## 4. IAM, Logs, Athena Workgroup (first time only)

```bash
aws iam create-role --role-name rdx-uat-serving-api-task-role \
  --assume-role-policy-document file://ecs-task-trust-policy.json
aws iam put-role-policy --role-name rdx-uat-serving-api-task-role \
  --policy-name rdx-uat-serving-api-data-access \
  --policy-document file://task-role-policy.uat.json      # placeholders filled
aws logs create-log-group --log-group-name /ecs/rdx-uat-serving-api
aws athena create-work-group --name <ATHENA_WORKGROUP> \
  --configuration "ResultConfiguration={OutputLocation=s3://<ATHENA_RESULTS_BUCKET>/athena-results/serving-api/}"
```

Own workgroup: Athena keeps query text and execution parameters
(account / citizen ids) in the workgroup history.

## 5. Register The Task Definition

```bash
aws ecs register-task-definition \
  --cli-input-json file://task-definition.uat.json     # placeholders filled
```

## 6. Network: Target Group, ALB Rule, Security Group

- Task SG: inbound tcp/8080 from the ALB's SG only.
- Target group: target type `ip`, protocol HTTP, port 8080, health check
  path `/health`.
- ALB listener rule: forward our paths (`/rdx_ep2`, `/rdx_ep1`,
  `/rdx_ep3`, `/rdx_ep4`) to the target group; check they do not
  overlap the vendor test app's paths.
- ALB idle timeout (default 60 s) is shared by every app on the ALB;
  keep it above `ATHENA_QUERY_TIMEOUT_SECONDS`.

## 7. Create The Service

```bash
aws ecs create-service --cluster <CLUSTER> --service-name rdx-uat-serving-api \
  --task-definition rdx-uat-serving-api --desired-count 1 --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<SUBNET_A>,<SUBNET_B>],securityGroups=[<TASK_SG>],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=<TG_ARN>,containerName=app,containerPort=8080" \
  --health-check-grace-period-seconds 30
```

Private subnets need a path to ECR, CloudWatch Logs, DynamoDB, Athena,
Glue and S3 (NAT or VPC endpoints).

## 8. Verify

```bash
aws ecs describe-services --cluster <CLUSTER> --services rdx-uat-serving-api \
  --query 'services[0].[status,runningCount,deployments[0].rolloutState]'
aws elbv2 describe-target-health --target-group-arn <TG_ARN>
aws logs tail /ecs/rdx-uat-serving-api --since 10m
```

The ALB is internal: plain CloudShell runs outside the VPC and cannot
reach it. Call it from inside the network (or a CloudShell VPC
environment in the VPC):

```bash
curl -s http://<ALB_DNS>/health
curl -s -X POST http://<ALB_DNS>/rdx_ep2 -H 'content-type: application/json' \
  -d '{"accountId":"<REAL_ID>","accountSubType":"<SUBTYPE>","language":"TH"}'
```

Failure signatures seen in trial:

| Symptom | Cause |
|---|---|
| task stops, log `KeyError: 'APP_ENV'` / `'ATHENA_WORKGROUP'` | env var missing in task definition |
| 500, `ResourceNotFoundException` | DynamoDB table name (check `APP_ENV`) |
| 500, `AccessDeniedException` | task role policy |
| 500, `NoRegionError` | `AWS_DEFAULT_REGION` missing |
| 500, Athena `INVALID_PARAMETER_USAGE` | `?` count vs bound values |

## 9. Update / Roll Back

```bash
# new image -> new task definition revision, then:
aws ecs update-service --cluster <CLUSTER> --service rdx-uat-serving-api \
  --task-definition rdx-uat-serving-api:<REVISION>
```

Roll back by pointing `--task-definition` at the previous revision.
