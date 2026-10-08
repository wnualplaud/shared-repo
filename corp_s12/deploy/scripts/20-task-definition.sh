#!/usr/bin/env bash
# 20-task-definition.sh <env>: register a new task definition revision
. "$(dirname "$0")/lib.sh"
show_target

render "templates/task-definition.json" "$OUT_DIR/task-definition.json"
aws ecs register-task-definition --cli-input-json "file://$OUT_DIR/task-definition.json" \
  --query 'taskDefinition.[family,revision,containerDefinitions[0].image]' --output text
