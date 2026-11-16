#!/usr/bin/env bash
# session: any (offline, no AWS call)
# preflight: the env file has every key, filled and well-formed
#   bash check-env.sh <env-file>
set -euo pipefail
source "$(dirname "$0")/../99-libs/lib.sh"

say "env file ${1:-}"
load_env "${1:-}"    # fails on a missing file or an empty key
ok "keys present: $KEYS"

[[ "$ACCOUNT_ID" =~ ^[0-9]{12}$ ]] || fail "ACCOUNT_ID is not 12 digits"
[[ "$AWS_REGION" =~ ^[a-z]{2}-[a-z]+-[0-9]$ ]] || fail "AWS_REGION looks wrong: $AWS_REGION"
grep -q '<' "$1" && warn "a placeholder (<...>) is still in $1" || ok "no placeholders left"
ok "well-formed"
