#!/usr/bin/env bash
# 30-run-task.sh <env>: run one task of the latest revision in the vendor's subnets, then report
. "$(dirname "$0")/lib.sh"
show_target

NET="awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUPS],assignPublicIp=$ASSIGN_PUBLIC_IP}"
TASK_ARN=$(aws ecs run-task --cluster "$CLUSTER" --launch-type FARGATE --task-definition "$FAMILY" \
  --network-configuration "$NET" --started-by "$APP-smoke" --query 'tasks[0].taskArn' --output text)
TASK_ID="${TASK_ARN##*/}"
echo "task $TASK_ID started; waiting for RUNNING"
echo "$TASK_ARN" > "$OUT_DIR/last-task-arn"

aws ecs wait tasks-running --cluster "$CLUSTER" --tasks "$TASK_ARN" || true
for i in 1 2 3 4 5 6; do
  read -r LAST HEALTH STOPPED <<<"$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$TASK_ARN" \
    --query 'tasks[0].[lastStatus,containers[0].healthStatus,stoppedReason]' --output text)"
  [ "$STOPPED" = None ] && STOPPED=""
  echo "  status=$LAST health=$HEALTH ${STOPPED:+reason=$STOPPED}"
  [ "$HEALTH" = HEALTHY ] || [ "$LAST" = STOPPED ] && break
  sleep 20
done

IP=$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$TASK_ARN" \
  --query 'tasks[0].containers[0].networkInterfaces[0].privateIpv4Address' --output text)
echo "private IP: $IP   (reachable from inside the VPC only, e.g. CloudShell VPC environment)"
echo "log stream: $LOG_PREFIX/app/$TASK_ID"
aws logs get-log-events --log-group-name "$LOG_GROUP" --log-stream-name "$LOG_PREFIX/app/$TASK_ID" \
  --limit 20 --query 'events[].message' --output text | tr '\t' '\n' || true
echo "stop with: aws ecs stop-task --cluster $CLUSTER --task $TASK_ID --reason smoke-done"
