#!/usr/bin/env bash
# session: Git Bash
# a new task definition revision with the new image, then the service onto it
#   bash deploy.sh <env-file> <tag> --dry-run    show the diff and what would run; changes nothing
#   bash deploy.sh <env-file> <tag>              register, update-service, wait
set -euo pipefail
source "$(dirname "$0")/../99-libs/lib.sh"
load_env "${1:-}"
TAG=${2:?tag pushed in 2-build}
DRY=${3:-}
OUT=$(run_dir release)

say "the running task definition"
old_td=$(current_task_def)
ok "${old_td##*/}"
echo "${old_td##*/}" > "$OUT/rollback-revision"

say "the new image"
aws ecr describe-images --repository-name "$ECR_REPO" --image-ids imageTag="$TAG" >/dev/null || fail "tag $TAG not in $ECR_REPO"
new_image="$REGISTRY/$ECR_REPO:$TAG"
ok "$new_image"

# only the fields register-task-definition accepts, from the running one; then swap the image
fields='{family:family,taskRoleArn:taskRoleArn,executionRoleArn:executionRoleArn,networkMode:networkMode,containerDefinitions:containerDefinitions,requiresCompatibilities:requiresCompatibilities,cpu:cpu,memory:memory,runtimePlatform:runtimePlatform}'
aws ecs describe-task-definition --task-definition "$old_td" --query "taskDefinition.$fields" --output json > "$OUT/old.json"
if grep -qE '^    "[A-Za-z]+": null' "$OUT/old.json"; then
    fail "a field is absent in the running task definition (null in old.json): drop it from \$fields"
fi
old_image=$(aws ecs describe-task-definition --task-definition "$old_td" \
    --query "taskDefinition.containerDefinitions[?name=='$CONTAINER'].image | [0]" --output text)
[ "$(grep -c "\"$old_image\"" "$OUT/old.json")" = 1 ] || fail "image $old_image not found exactly once in the task definition"
sed "s|\"$old_image\"|\"$new_image\"|" "$OUT/old.json" > "$OUT/new.json"

say "diff (only the image should change)"
diff "$OUT/old.json" "$OUT/new.json" || true
[ "$(diff "$OUT/old.json" "$OUT/new.json" | grep -c '^[<>]')" = 2 ] || fail "more than the image changed"

if [ "$DRY" = --dry-run ]; then
    say "dry run: would run"
    echo "   aws ecs register-task-definition --cli-input-json <new.json>"
    echo "   aws ecs update-service --cluster $CLUSTER --service $SERVICE --task-definition <family>:<new revision>"
    echo "   aws ecs wait services-stable ...   (rollback: ${old_td##*/})"
    echo "   saved in $OUT"
    exit 0
fi

say "register"
new_td=$(aws ecs register-task-definition --cli-input-json "$(cat "$OUT/new.json")" \
    --query 'taskDefinition.taskDefinitionArn' --output text)
ok "${new_td##*/}"
echo "${new_td##*/}" > "$OUT/new-revision"

say "update-service -> ${new_td##*/}"
aws ecs update-service --cluster "$CLUSTER" --service "$SERVICE" --task-definition "$new_td" \
    --query 'service.taskDefinition' --output text >/dev/null

say "wait for the service to settle (up to 10 minutes)"
aws ecs wait services-stable --cluster "$CLUSTER" --services "$SERVICE" || fail "not stable: check 4a, or roll back to ${old_td##*/}"
ok "stable on ${new_td##*/}; rollback point ${old_td##*/}"
echo "   saved in $OUT"
