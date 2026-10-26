#!/usr/bin/env bash
# session: Git Bash
# verify from outside (AWS APIs, read-only): the service runs the expected revision, targets, events, logs
#   bash check.sh <env-file> [expected-revision, e.g. rdx-uat-ecs:14]
# Rerun it after 4b to keep the smoke calls' logs as evidence.
set -euo pipefail
source "$(dirname "$0")/../99-libs/lib.sh"
load_env "${1:-}"
EXPECTED=${2:-}
OUT=$(run_dir verify-outside)
status=0

say "service"
td=$(current_task_def)
if [ -n "$EXPECTED" ] && [ "${td##*/}" != "$EXPECTED" ]; then warn "runs ${td##*/}, expected $EXPECTED"; status=1; else ok "runs ${td##*/}"; fi
read -r running desired deployments rollout <<<"$(aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" \
    --query 'services[0].[runningCount,desiredCount,length(deployments),deployments[0].rolloutState]' --output text)"
[ "$running" = "$desired" ] && ok "running $running of $desired" || { warn "running $running of $desired"; status=1; }
[ "$deployments" = 1 ] && ok "one deployment, rollout $rollout" || { warn "$deployments deployments (rollout $rollout)"; status=1; }

say "targets (B10: unhealthy with 404 is known while the health check path is /)"
tg=$(aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" --query 'services[0].loadBalancers[0].targetGroupArn' --output text)
if none "$tg"; then
    warn "no load balancer on the service: skipped"
else
    aws elbv2 describe-target-health --target-group-arn "$tg" \
        --query 'TargetHealthDescriptions[].[Target.Id,TargetHealth.State,TargetHealth.Reason]' --output text | tee "$OUT/target-health.txt"
    aws elbv2 describe-target-groups --target-group-arns "$tg" \
        --query 'TargetGroups[0].[HealthCheckPath,Matcher.HttpCode]' --output text | sed 's/^/   health check path, codes: /' | tee -a "$OUT/target-health.txt"
fi

say "last service events"
aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" \
    --query 'services[0].events[:8].[createdAt,message]' --output text | tee "$OUT/events.txt"

say "app logs, last 15 minutes"
aws logs tail "$LOG_GROUP" --since 15m --format short > "$OUT/logs.txt" || true
tail -n 20 "$OUT/logs.txt"
grep -qiE 'traceback|error' "$OUT/logs.txt" && { warn "errors in the logs (see logs.txt)"; status=1; } || ok "no error lines"

echo "   saved in $OUT"
exit $status
