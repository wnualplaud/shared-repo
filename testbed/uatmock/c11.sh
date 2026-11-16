#!/usr/bin/env bash
# api r06 c11: our own mock stores in UAT (ap-southeast-7), APP_ENV=uatmock.
# Run in the UAT account's CloudShell, from this folder (testbed/uatmock/),
# with testbed/tables/ and testbed/mock/out/ beside it (upload testbed/ as a zip).
#
#   bash c11.sh check      read only: account, region, files, what exists already
#   bash c11.sh dynamodb   create rdxuatmock_tbl2 / _list, put the 11 mock accounts
#   bash c11.sh policy     inline policy yourdata-api-uatmock on the task role (DynamoDB + S3 read)
#   bash c11.sh athena     database rdxuatmock_db1, table rdx_tbl3, the 20 mock rows
#   bash c11.sh grants     Lake Formation: DESCRIBE on the database, SELECT + DESCRIBE on the table
#   bash c11.sh verify     read only: counts, the policy, the grants
#   bash c11.sh undo       everything above, in reverse
#
# Each writing step asks "yes" first. Nothing here holds an account id: it is
# read from the credentials and shown as its last 4 digits.
set -euo pipefail

export AWS_REGION=ap-southeast-7 AWS_DEFAULT_REGION=ap-southeast-7
export ENV=uatmock
export WAREHOUSE=s3://rdxorg-rdx-uat-share/yourdata-api-mock/iceberg
OUT=s3://rdxorg-rdx-uat-control/athena-results/
ROLE=rdx-uat-ecs-task-role
POLICY=yourdata-api-uatmock
DB=rdx${ENV}_db1
TABLES=(rdx_tbl2 rdx_tbl1)
# file name -> DynamoDB table, written out whole (redact.py replaces whole names only)
declare -A DDB=([rdx_tbl2]="rdx${ENV}_tbl2" [rdx_tbl1]="rdx${ENV}_tbl1")
HERE="$(cd "$(dirname "$0")" && pwd)"
TB="$HERE/.."

say()  { printf '\n== %s\n' "$*"; }
fail() { printf 'FAILED: %s\n' "$*" >&2; exit 1; }
ask()  { read -rp "$1 Type yes to go on: " a; [ "$a" = yes ] || fail "stopped"; }

account() {
    ACCT="$(aws sts get-caller-identity --query Account --output text)"
    echo "account ...${ACCT: -4}  region $AWS_REGION  ENV=$ENV"
}

# one .sql file (or text with -q) in Athena: ${ENV} ${WAREHOUSE} filled, a trailing ; dropped, waits
athena_run() {
    local q id s
    if [ "$1" = -q ]; then q="$(envsubst '$ENV $WAREHOUSE' <<<"$2")"; else
        q="$(envsubst '$ENV $WAREHOUSE' < "$1" | sed 's/;[[:space:]]*$//')"; fi
    id="$(aws athena start-query-execution --work-group primary \
        --result-configuration OutputLocation="$OUT" --query-string "$q" \
        --query QueryExecutionId --output text)"
    while s="$(aws athena get-query-execution --query-execution-id "$id" \
            --query QueryExecution.Status.State --output text)"; \
          [ "$s" = QUEUED ] || [ "$s" = RUNNING ]; do sleep 2; done
    echo "${1##*/}${2:+ $2}: $s"
    if [ "$s" != SUCCEEDED ]; then
        aws athena get-query-execution --query-execution-id "$id" \
            --query QueryExecution.Status.StateChangeReason --output text
        return 1
    fi
    LAST_QID="$id"
}

athena_value() {  # the first data row of the last query, tab-separated
    aws athena get-query-results --query-execution-id "$LAST_QID" \
        --query 'ResultSet.Rows[1].Data[].VarCharValue' --output text
}

check() {
    say "account"; account
    say "files"
    for f in "${TABLES[@]/%/.table.json}"; do [ -f "$TB/tables/$f" ] && echo "ok tables/$f" || fail "missing tables/$f"; done
    for f in "${TABLES[@]/%/.items.json}"; do [ -f "$TB/mock/out/$f" ] && echo "ok mock/out/$f" || fail "missing mock/out/$f"; done
    for f in tables/create_database.sql tables/rdx_tbl3.sql mock/out/rdx_tbl3.insert.sql; do
        [ -f "$TB/$f" ] && echo "ok $f" || fail "missing $f"; done
    command -v envsubst >/dev/null || fail "envsubst not found"
    say "what exists already (nothing is expected on a first run)"
    for t in "${TABLES[@]}"; do
        aws dynamodb describe-table --table-name "${DDB[$t]}" --query Table.TableStatus --output text 2>/dev/null \
            | sed "s/^/${DDB[$t]}: /" || echo "${DDB[$t]}: none"
    done
    aws glue get-database --name "$DB" --query Database.Name --output text 2>/dev/null || echo "$DB: none"
    aws iam get-role-policy --role-name "$ROLE" --policy-name "$POLICY" --query PolicyName --output text 2>/dev/null \
        || echo "$POLICY: none"
    say "role"; aws iam get-role --role-name "$ROLE" --query Role.Arn --output text | sed 's/::[0-9]*:/::<acct>:/'
}

dynamodb() {
    account; ask "Create the two DynamoDB tables and put the mock."
    for t in "${TABLES[@]}"; do
        say "${DDB[$t]}"
        envsubst '$ENV' < "$TB/tables/$t.table.json" > "/tmp/$t.table.json"
        aws dynamodb create-table --cli-input-json "file:///tmp/$t.table.json" --query TableDescription.TableStatus --output text
        aws dynamodb wait table-exists --table-name "${DDB[$t]}"
        envsubst '$ENV' < "$TB/mock/out/$t.items.json" > "/tmp/$t.items.json"
        aws dynamodb batch-write-item --request-items "file:///tmp/$t.items.json" --query UnprocessedItems
        echo "items: $(aws dynamodb scan --table-name "${DDB[$t]}" --select COUNT --query Count)"
    done
}

policy() {
    account; ask "Put inline policy $POLICY on $ROLE."
    cat > /tmp/policy.json <<EOF
{"Version": "2012-10-17", "Statement": [
  {"Sid": "DynamoDbMockRead", "Effect": "Allow",
   "Action": ["dynamodb:PartiQLSelect", "dynamodb:Query"],
   "Resource": ["arn:aws:dynamodb:${AWS_REGION}:${ACCT}:table/rdx${ENV}_tbl2",
                "arn:aws:dynamodb:${AWS_REGION}:${ACCT}:table/rdx${ENV}_tbl1"]},
  {"Sid": "S3MockRead", "Effect": "Allow", "Action": "s3:GetObject",
   "Resource": "arn:aws:s3:::rdxorg-rdx-uat-share/yourdata-api-mock/*"},
  {"Sid": "S3MockList", "Effect": "Allow", "Action": "s3:ListBucket",
   "Resource": "arn:aws:s3:::rdxorg-rdx-uat-share",
   "Condition": {"StringLike": {"s3:prefix": "yourdata-api-mock/*"}}},
  {"Sid": "GlueMockRead", "Effect": "Allow",
   "Action": ["glue:GetDatabase", "glue:GetTable", "glue:GetPartition", "glue:GetPartitions", "glue:BatchGetPartition"],
   "Resource": ["arn:aws:glue:${AWS_REGION}:${ACCT}:catalog",
                "arn:aws:glue:${AWS_REGION}:${ACCT}:database/${DB}",
                "arn:aws:glue:${AWS_REGION}:${ACCT}:table/${DB}/*"]}
]}
EOF
    aws iam put-role-policy --role-name "$ROLE" --policy-name "$POLICY" --policy-document file:///tmp/policy.json
    aws iam list-role-policies --role-name "$ROLE" --query PolicyNames --output text
}

athena() {
    account; ask "Create $DB, its rdx_tbl3 at $WAREHOUSE, and insert the mock."
    athena_run "$TB/tables/create_database.sql"
    athena_run "$TB/tables/rdx_tbl3.sql"
    athena_run "$TB/mock/out/rdx_tbl3.insert.sql"
    athena_run -q 'SELECT count(*), count(DISTINCT accountId) FROM rdx${ENV}_db1.rdx_tbl3'
    echo "rows, accounts: $(athena_value)"
}

grants() {
    account; ask "Grant $ROLE: DESCRIBE on $DB, SELECT + DESCRIBE on $DB.rdx_tbl3."
    local p="DataLakePrincipalIdentifier=arn:aws:iam::${ACCT}:role/${ROLE}"
    aws lakeformation grant-permissions --principal "$p" --permissions DESCRIBE --resource "Database={Name=$DB}"
    aws lakeformation grant-permissions --principal "$p" --permissions SELECT DESCRIBE \
        --resource "Table={DatabaseName=$DB,Name=rdx_tbl3}"
    echo ok
}

verify() {
    say "account"; account
    say "DynamoDB"
    for t in "${TABLES[@]}"; do
        echo "${DDB[$t]}: $(aws dynamodb scan --table-name "${DDB[$t]}" --select COUNT --query Count) items"
    done
    say "Athena"
    athena_run -q 'SELECT count(*), count(DISTINCT accountId) FROM rdx${ENV}_db1.rdx_tbl3'
    echo "rows, accounts: $(athena_value)"
    say "policy $POLICY"
    aws iam get-role-policy --role-name "$ROLE" --policy-name "$POLICY" --query 'PolicyDocument.Statement[].Sid' --output text
    say "Lake Formation on $DB.rdx_tbl3"
    aws lakeformation list-permissions --resource "Table={DatabaseName=$DB,Name=rdx_tbl3}" \
        --query 'PrincipalResourcePermissions[].[Principal.DataLakePrincipalIdentifier,join(`,`,Permissions)]' --output text \
        | sed 's/::[0-9]*:/::<acct>:/'
}

undo() {
    account; ask "Remove everything this script made (grants, Athena table + database + files, policy, DynamoDB tables)."
    local p="DataLakePrincipalIdentifier=arn:aws:iam::${ACCT}:role/${ROLE}"
    aws lakeformation revoke-permissions --principal "$p" --permissions SELECT DESCRIBE \
        --resource "Table={DatabaseName=$DB,Name=rdx_tbl3}" || true
    aws lakeformation revoke-permissions --principal "$p" --permissions DESCRIBE --resource "Database={Name=$DB}" || true
    athena_run -q 'DROP TABLE IF EXISTS rdx${ENV}_db1.rdx_tbl3' || true
    athena_run -q 'DROP DATABASE IF EXISTS rdx${ENV}_db1' || true
    aws s3 rm --recursive "$WAREHOUSE/$DB/" || true
    aws iam delete-role-policy --role-name "$ROLE" --policy-name "$POLICY" || true
    for t in "${TABLES[@]}"; do aws dynamodb delete-table --table-name "${DDB[$t]}" --query TableDescription.TableStatus --output text || true; done
}

case "${1:-}" in
    check|dynamodb|policy|athena|grants|verify|undo) "$1" ;;
    *) sed -n '2,15p' "$0"; exit 1 ;;
esac
