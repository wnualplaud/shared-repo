#!/usr/bin/env bash
# compare-env.sh <env>: compare the KEYS of config/env.example and config/<env>.env, both ways,
# and check env.example covers every ${VAR} used by the templates. Values are not read.
set -uo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${1:?usage: $0 <env>   (compares config/env.example with config/<env>.env)}"
EXAMPLE="$DEPLOY_DIR/config/env.example"
REAL="$DEPLOY_DIR/config/$ENV_NAME.env"
[ -f "$EXAMPLE" ] || { echo "missing $EXAMPLE"; exit 1; }
[ -f "$REAL" ]    || { echo "missing $REAL"; exit 1; }

keys() { sed 's/\r$//' "$1" | grep -oE '^[[:space:]]*[A-Z_][A-Z0-9_]*=' | tr -d ' =' | sort -u; }
EX_KEYS=$(keys "$EXAMPLE"); REAL_KEYS=$(keys "$REAL")
TPL_KEYS=$(grep -oh '\${[A-Z_][A-Z0-9_]*}' "$DEPLOY_DIR"/templates/*.json | tr -d '${}' | sort -u | grep -v '^ACCOUNT_ID$')

ERR=0
report() { local title="$1" list="$2"; [ -z "$list" ] && return; echo "$title"; printf '  %s\n' $list; ERR=1; }

report "in env.example but not in $ENV_NAME.env (add to $ENV_NAME.env):" "$(comm -23 <(echo "$EX_KEYS") <(echo "$REAL_KEYS"))"
report "in $ENV_NAME.env but not in env.example (add to env.example):"   "$(comm -13 <(echo "$EX_KEYS") <(echo "$REAL_KEYS"))"
report "used in templates but not in env.example (add to both):"        "$(comm -23 <(echo "$TPL_KEYS") <(echo "$EX_KEYS"))"

[ "$ERR" = 0 ] && echo "keys match: env.example = $ENV_NAME.env ($(echo "$EX_KEYS" | wc -l) keys), templates covered"
exit $ERR
