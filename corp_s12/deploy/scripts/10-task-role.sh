#!/usr/bin/env bash
# 10-task-role.sh <env>: create the task role if missing, then (re)write its inline policy
. "$(dirname "$0")/lib.sh"
show_target

render "$DEPLOY_DIR/templates/task-role-policy.json" "$OUT_DIR/task-role-policy.json"

if aws iam get-role --role-name "$TASK_ROLE" >/dev/null 2>&1; then
  echo "role exists: $TASK_ROLE"
else
  aws iam create-role --role-name "$TASK_ROLE" \
    --assume-role-policy-document "file://$DEPLOY_DIR/templates/ecs-task-trust-policy.json" \
    --tags Key=App,Value="$APP" --query 'Role.Arn' --output text
fi

aws iam put-role-policy --role-name "$TASK_ROLE" --policy-name "$APP-data-access" \
  --policy-document "file://$OUT_DIR/task-role-policy.json"
echo "policy statements: $(aws iam get-role-policy --role-name "$TASK_ROLE" --policy-name "$APP-data-access" \
  --query 'PolicyDocument.Statement[].Sid' --output text)"
