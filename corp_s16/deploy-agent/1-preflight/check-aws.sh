#!/usr/bin/env bash
# session: Git Bash
# preflight, read-only: can we deploy now, and what state is UAT in
#   bash check-aws.sh <env-file>
set -euo pipefail
source "$(dirname "$0")/../99-libs/lib.sh"
load_env "${1:-}"
OUT=$(run_dir preflight)

# 1. identity: the right account and region (also catches an expired SSO login)
say "1. identity"
acct=$(aws sts get-caller-identity --query Account --output text) || fail "not logged in (aws sso login?)"
[ "$acct" = "$ACCOUNT_ID" ] || fail "logged in to another account than ACCOUNT_ID"
ok "account matches ACCOUNT_ID, region $AWS_REGION"

# 2. resources the deploy touches exist
#   2.1 ECR repo, cluster, service, running task definition, task/execution role
say "2.1 what the release uses"
aws ecr describe-repositories --repository-names "$ECR_REPO" >/dev/null || fail "ECR repo $ECR_REPO"
ok "ECR repo $ECR_REPO"
[ "$(aws ecs describe-clusters --clusters "$CLUSTER" --query 'clusters[0].status' --output text)" = ACTIVE ] || fail "cluster $CLUSTER"
ok "cluster $CLUSTER"
[ "$(aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" --query 'services[0].status' --output text)" = ACTIVE ] || fail "service $SERVICE"
ok "service $SERVICE"
td=$(current_task_def)
aws ecs describe-task-definition --task-definition "$td" --query taskDefinition > "$OUT/task-definition.json"
ok "running task definition ${td##*/}"
for role in $(aws ecs describe-task-definition --task-definition "$td" --query 'taskDefinition.[taskRoleArn,executionRoleArn]' --output text); do
    none "$role" && continue
    aws iam get-role --role-name "${role##*/}" >/dev/null || fail "role ${role##*/}"
    ok "role ${role##*/}"
done

#   2.2 the running image still in ECR, target group, log group
say "2.2 what recover and verify use"
image=$(aws ecs describe-task-definition --task-definition "$td" \
    --query "taskDefinition.containerDefinitions[?name=='$CONTAINER'].image | [0]" --output text)
none "$image" && fail "no container named $CONTAINER in ${td##*/}"
aws ecr describe-images --repository-name "$ECR_REPO" --image-ids imageTag="${image##*:}" >/dev/null \
    || fail "running image ${image##*:} is gone from ECR: no rollback to it"
ok "running image ${image##*:} still in ECR"
tg=$(aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" --query 'services[0].loadBalancers[0].targetGroupArn' --output text)
if none "$tg"; then warn "no load balancer on the service: 4a skips target health"; else ok "target group ${tg##*:targetgroup/}"; fi
[ "$(aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP" --query "length(logGroups[?logGroupName=='$LOG_GROUP'])" --output text)" = 1 ] \
    || fail "log group $LOG_GROUP"
ok "log group $LOG_GROUP"

# 3.  current state: service healthy, no deployment in progress
say "3. current state"
read -r running desired deployments <<<"$(aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" \
    --query 'services[0].[runningCount,desiredCount,length(deployments)]' --output text)"
[ "$running" = "$desired" ] && ok "running $running of $desired" || warn "running $running of $desired"
[ "$deployments" = 1 ] || fail "$deployments deployments in progress: wait for the last one to finish"
ok "no deployment in progress"

#   running revision and its image (the rollback point)
echo "${td##*/}" > "$OUT/rollback-revision"
ok "rollback point: ${td##*/}, image ${image##*:}"
echo "   saved in $OUT"
