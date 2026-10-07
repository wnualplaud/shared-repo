#!/usr/bin/env bash
# 00-check.sh <env>: read-only checks that everything the deploy refers to exists
. "$(dirname "$0")/lib.sh"
show_target

ok()   { echo "  ok    $*"; }
miss() { echo "  MISS  $*"; FAILED=1; }
FAILED=0
check() { local label="$1"; shift; if "$@" >/dev/null 2>&1; then ok "$label"; else miss "$label"; fi; }

check "cluster $CLUSTER"                aws ecs describe-clusters --clusters "$CLUSTER" --query 'clusters[0].clusterName' --output text
check "execution role $EXECUTION_ROLE"  aws iam get-role --role-name "$EXECUTION_ROLE"
check "image $IMAGE_REPO:$IMAGE_TAG"    aws ecr describe-images --repository-name "$IMAGE_REPO" --image-ids imageTag="$IMAGE_TAG"
check "log group $LOG_GROUP"            test "$(aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP" --query "logGroups[?logGroupName=='$LOG_GROUP'] | length(@)" --output text)" = 1
check "table $TABLE_AC_LIST"            aws dynamodb describe-table --table-name "$TABLE_AC_LIST"
check "table $TABLE_AC_DTL"             aws dynamodb describe-table --table-name "$TABLE_AC_DTL"
check "bucket $BUCKET"                  aws s3api head-bucket --bucket "$BUCKET"
check "subnets $SUBNETS"                aws ec2 describe-subnets --subnet-ids ${SUBNETS//,/ }
check "security groups $SECURITY_GROUPS" aws ec2 describe-security-groups --group-ids ${SECURITY_GROUPS//,/ }
if aws iam get-role --role-name "$TASK_ROLE" >/dev/null 2>&1; then ok "task role $TASK_ROLE"; else echo "  todo  task role $TASK_ROLE (10-task-role.sh)"; fi
if aws glue get-database --name "$ATHENA_DATABASE" >/dev/null 2>&1; then ok "glue database $ATHENA_DATABASE"; else echo "  warn  glue database $ATHENA_DATABASE missing (/transaction will fail)"; fi

[ "$FAILED" = 0 ] && echo "all required resources found" || { echo "missing resources above"; exit 1; }
