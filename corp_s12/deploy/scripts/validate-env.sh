#!/usr/bin/env bash
# validate-env.sh <env>: offline check of config/<env>.env (no AWS calls)
#   - every variable the scripts/templates need is present and non-empty
#   - no <placeholder> left, no CRLF line endings
#   - basic format of region, ids, prefixes, numbers
set -uo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${1:?usage: $0 <env>   (checks config/<env>.env)}"
CONFIG="$DEPLOY_DIR/config/$ENV_NAME.env"
[ -f "$CONFIG" ] || { echo "missing $CONFIG"; exit 1; }

ERR=0; WARN=0
err()  { echo "  ERROR $*"; ERR=$((ERR+1)); }
warn() { echo "  warn  $*"; WARN=$((WARN+1)); }
echo "checking $CONFIG"

# required = fixed list used by the scripts + every ${VAR} in the templates (minus ACCOUNT_ID)
SCRIPT_VARS="AWS_PROFILE AWS_REGION APP CLUSTER FAMILY TASK_ROLE EXECUTION_ROLE IMAGE_REPO IMAGE_TAG
LOG_GROUP LOG_PREFIX TABLE_AC_LIST TABLE_AC_DTL SUBNETS SECURITY_GROUPS ASSIGN_PUBLIC_IP"
TEMPLATE_VARS=$(grep -oh '\${[A-Z_][A-Z0-9_]*}' "$DEPLOY_DIR"/templates/*.json | tr -d '${}' | sort -u | grep -v '^ACCOUNT_ID$')
REQUIRED=$(printf '%s\n' $SCRIPT_VARS $TEMPLATE_VARS | sort -u)

grep -q $'\r' "$CONFIG" && warn "CRLF line endings (the scripts strip them; better save as LF)"
grep -n '<[A-Za-z0-9_-]*>' "$CONFIG" | sed 's/^/  ERROR placeholder left: line /' && ERR=$((ERR+1))
grep -q '^[[:space:]]*ACCOUNT_ID=' "$CONFIG" && warn "ACCOUNT_ID is set; scripts look it up themselves"

# load without running anything else in the shell
set -a; . <(sed 's/\r$//' "$CONFIG" | grep -v '<[A-Za-z0-9_-]*>'); set +a

for v in $REQUIRED; do
  [ -n "${!v:-}" ] || err "$v is missing or empty"
done
for v in $(sed 's/\r$//' "$CONFIG" | grep -oE '^[A-Z_][A-Z0-9_]*=' | tr -d '='); do
  printf '%s\n' $REQUIRED | grep -qx "$v" || warn "$v is set but not used by the scripts/templates"
done

match() { local v="$1" re="$2" hint="$3"; [ -z "${!v:-}" ] || [[ "${!v}" =~ $re ]] || err "$v='${!v}' $hint"; }
match AWS_REGION        '^[a-z]{2}-[a-z]+-[0-9]$'                    "is not a region (e.g. ap-southeast-7)"
match SUBNETS           '^subnet-[0-9a-f]+(,subnet-[0-9a-f]+)*$'     "must be subnet-ids separated by commas, no spaces"
match SECURITY_GROUPS   '^sg-[0-9a-f]+(,sg-[0-9a-f]+)*$'             "must be sg-ids separated by commas, no spaces"
match ASSIGN_PUBLIC_IP  '^(ENABLED|DISABLED)$'                        "must be ENABLED or DISABLED"
match LOG_GROUP         '^/'                                          "should start with /"
match IMAGE_TAG         '^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$'         "is not a valid image tag"
match BUCKET            '^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$'          "is not a valid bucket name (no s3://, no slash)"
match ATHENA_RESULTS_PREFIX '^[^/].*[^/]$'                            "must not start or end with /"
match MART_DATA_PREFIX  '^[^/].*[^/]$'                                "must not start or end with /"
match ATHENA_QUERY_TIMEOUT_SECONDS '^[0-9]+$'                         "must be a whole number"
match APP_ENV           '^[a-z]+$'                                    "should be lowercase letters (dev, sit, uat, prod)"
[ -n "${APP_ENV:-}" ] && [ -n "${TABLE_AC_LIST:-}" ] && [[ "$TABLE_AC_LIST" != *"$APP_ENV"* ]] \
  && warn "TABLE_AC_LIST does not contain APP_ENV='$APP_ENV' (queries build table names from APP_ENV)"

echo "result: $ERR error(s), $WARN warning(s)"
[ "$ERR" = 0 ]
