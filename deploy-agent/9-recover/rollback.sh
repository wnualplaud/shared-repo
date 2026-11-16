#!/usr/bin/env bash
# session: Git Bash
# put the service back on an earlier revision (the rollback point saved by 1 and 3)
#   bash rollback.sh <env-file> <revision, e.g. rdx-uat-ecs:13>
set -euo pipefail
source "$(dirname "$0")/../99-libs/lib.sh"
load_env "${1:-}"
REV=${2:?revision to go back to}

say "service runs $(current_task_def | sed 's|.*/||'), going back to $REV"
aws ecs describe-task-definition --task-definition "$REV" >/dev/null || fail "no task definition $REV"
aws ecs update-service --cluster "$CLUSTER" --service "$SERVICE" --task-definition "$REV" \
    --query 'service.taskDefinition' --output text >/dev/null
aws ecs wait services-stable --cluster "$CLUSTER" --services "$SERVICE" || fail "not stable after the rollback: check events"
ok "back on $REV"
