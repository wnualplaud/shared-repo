#!/usr/bin/env bash
# athena-run.sh <file.sql | "SQL string">
#   runs one statement in Athena, waits, prints state; prints rows for SELECT.
#   Needs ATHENA_OUTPUT_LOCATION (s3://.../); ATHENA_WORKGROUP defaults to primary.
set -euo pipefail
# Windows AWS CLI reads file:// with the system code page; the data has Thai text.
export AWS_CLI_FILE_ENCODING=UTF-8
SQL="${1:?usage: athena-run.sh <file.sql | \"SQL\">}"
# a file goes as file:// so the CLI reads it as UTF-8 (passing Thai text on the
# Windows command line can turn it into ???); a plain string is sent as is.
QS="$SQL"; [ -f "$SQL" ] && { QS="file://$SQL"; SQL="$(cat "$SQL")"; }

export AWS_PROFILE="${AWS_PROFILE:-yourdata-uat}"
export AWS_REGION="${AWS_REGION:-ap-southeast-7}" AWS_DEFAULT_REGION="${AWS_REGION}"
OUT="${ATHENA_OUTPUT_LOCATION:?set ATHENA_OUTPUT_LOCATION=s3://<bucket>/athena-results/serving-api/}"
WG="${ATHENA_WORKGROUP:-primary}"
echo "profile=$AWS_PROFILE region=$AWS_REGION workgroup=$WG output=$OUT"

ID=$(aws athena start-query-execution --work-group "$WG" --query-string "$QS" \
      --result-configuration "OutputLocation=$OUT" --query QueryExecutionId --output text)
while :; do
  ST=$(aws athena get-query-execution --query-execution-id "$ID" \
        --query 'QueryExecution.Status.[State,StateChangeReason]' --output text)
  case "$ST" in QUEUED*|RUNNING*) sleep 1 ;; *) break ;; esac
done
echo "$ID $ST"
case "$ST" in SUCCEEDED*) ;; *) exit 1 ;; esac
case "$(echo "$SQL" | tr '[:lower:]' '[:upper:]' | sed 's/^[[:space:]]*//')" in
  SELECT*|WITH*) aws athena get-query-results --query-execution-id "$ID" \
                   --query 'ResultSet.Rows[].Data[].VarCharValue' --output text ;;
esac
