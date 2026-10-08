#!/usr/bin/env bash
# smoke-test.sh <host-or-ip>[:port]
#   Calls the API with the mock-data cases below and checks each HTTP status.
#   Needs only bash + curl; run it where the task is reachable
#   (e.g. a CloudShell VPC environment): bash smoke-test.sh 10.0.1.23
set -uo pipefail

TARGET="${1:?usage: $0 <host-or-ip>[:port]}"
[[ "$TARGET" == *:* ]] || TARGET="$TARGET:8080"
BASE="http://$TARGET"

# expected-status | method | path | json body | what it checks   (mock data: tracks/t07-uat-deploy/mocked)
CASES=$(cat <<'EOF'
200|GET|/health||app is up
200|POST|/account/list|{"citizen_id":"1100000000001","accountSubType":"SAVINGS","language":"EN","auxiliaryReferenceId":"r1"}|list: 2 SAVINGS accounts, EN with TH fallback
200|POST|/account/list|{"citizen_id":"1100000000001","accountSubType":"CURRENT","language":"TH","auxiliaryReferenceId":"r1"}|list: 1 CURRENT account
200|POST|/account/list|{"citizen_id":"1100000000009","accountSubType":"SAVINGS","auxiliaryReferenceId":"r1"}|list: unknown citizen -> empty list
400|POST|/account/list|{"citizen_id":"1100000000001","accountSubType":"SAVINGS","language":"JP"}|unsupported language
200|POST|/account|{"accountId":"1000000001","accountSubType":"SAVINGS","language":"EN","auxiliaryReferenceId":"r1"}|account: EN name + EN home branch
200|POST|/account|{"accountId":"1000000002","accountSubType":"SAVINGS","language":"EN","auxiliaryReferenceId":"r1"}|account: no EN -> TH fallback
404|POST|/account|{"accountId":"1000000001","accountSubType":"CURRENT"}|account: subtype does not match
404|POST|/account|{"accountId":"9999999999","accountSubType":"SAVINGS"}|account: unknown id
400|POST|/account|{"accountId":"1000000001","accountSubType":"FOO"}|subtype not in enum
400|POST|/account|{"accountId":"1000000001","accountSubType":"ALL"}|ALL not supported yet
200|POST|/balance|{"accountId":"2000000001","accountSubType":"CURRENT","auxiliaryReferenceId":"r1"}|balance: negative ledger, credit limit
200|POST|/balance|{"accountId":"1000000002","accountSubType":"SAVINGS","auxiliaryReferenceId":"r1"}|balance: no available balance
404|POST|/balance|{"accountId":"9999999999","accountSubType":"SAVINGS"}|balance: unknown id
404|POST|/statement|{}|statement disabled
EOF
)

PASS=0; FAIL=0
while IFS='|' read -r WANT METHOD PATH_ BODY NOTE; do
  [ -z "$WANT" ] && continue
  if [ "$METHOD" = GET ]; then
    RESP=$(curl -s -m 60 -w $'\n%{http_code}' "$BASE$PATH_")
  else
    RESP=$(curl -s -m 60 -w $'\n%{http_code}' -X POST "$BASE$PATH_" \
             -H "Content-Type: application/json" --data "$BODY")
  fi
  GOT="${RESP##*$'\n'}"; OUT="${RESP%$'\n'*}"
  if [ "$GOT" = "$WANT" ]; then MARK=PASS; PASS=$((PASS+1)); else MARK=FAIL; FAIL=$((FAIL+1)); fi
  printf '%s  %s (want %s)  %-5s %-14s %s\n' "$MARK" "$GOT" "$WANT" "$METHOD" "$PATH_" "$NOTE"
  printf '      %.300s\n' "$OUT"
done <<< "$CASES"

echo "result: $PASS passed, $FAIL failed  ($BASE)"
[ "$FAIL" = 0 ]
