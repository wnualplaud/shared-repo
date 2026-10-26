#!/usr/bin/env bash
# session: CloudShell VPC environment (reaches the internal ALB)
# verify from inside: /health, then one call per endpoint; passes when nothing answers 5xx
#   CLOUDSHELL=1 bash smoke.sh <env-file>
# SMOKE_BASE_URL empty: found from the service's load balancer.
# SMOKE_* test keys empty: dummy values, so data calls answer 4xx (still no 5xx expected).
set -euo pipefail
source "$(dirname "$0")/../99-libs/lib.sh"
load_env "${1:-}"
status=0

base=${SMOKE_BASE_URL:-}
if [ -z "$base" ] || [[ "$base" == *"<"* ]]; then
    tg=$(aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" --query 'services[0].loadBalancers[0].targetGroupArn' --output text)
    none "$tg" && fail "no SMOKE_BASE_URL and no load balancer on the service"
    lb=$(aws elbv2 describe-target-groups --target-group-arns "$tg" --query 'TargetGroups[0].LoadBalancerArns[0]' --output text)
    base="http://$(aws elbv2 describe-load-balancers --load-balancer-arns "$lb" --query 'LoadBalancers[0].DNSName' --output text)"
fi
acct=${SMOKE_ACCOUNT_ID:-0000000000}; [[ "$acct" == *"<"* ]] && acct=0000000000
cid=${SMOKE_CITIZEN_ID:-0000000000000}; [[ "$cid" == *"<"* ]] && cid=0000000000000
sub=${SMOKE_SUBTYPE:-SAVING}
say "calling $base"

call() {  # path body -> prints the status code and the start of the body
    local code
    code=$(curl -s -o /tmp/smoke.body -w '%{http_code}' --max-time 30 \
        -H 'Content-Type: application/json' ${2:+-d "$2"} "$base$1") || code=000
    printf '   %-14s %s  %s\n' "$1" "$code" "$(head -c 160 /tmp/smoke.body)"
    case $code in 2??|4??) ;; *) status=1 ;; esac
}

say "health"
call /health ""

say "endpoints (4xx can be the data; 5xx or no answer fails)"
call /rdx_ep1 "{\"citizenId\":\"$cid\",\"accountSubType\":\"$sub\",\"language\":\"TH\",\"auxiliaryReferenceId\":\"smoke\"}"
call /rdx_ep2      "{\"accountId\":\"$acct\",\"accountSubType\":\"$sub\",\"language\":\"TH\",\"auxiliaryReferenceId\":\"smoke\"}"
call /rdx_ep3      "{\"accountId\":\"$acct\",\"accountSubType\":\"$sub\",\"language\":\"TH\",\"auxiliaryReferenceId\":\"smoke\"}"
call /rdx_ep4  "{\"accountId\":\"$acct\",\"accountSubType\":\"$sub\",\"language\":\"TH\",\"auxiliaryReferenceId\":\"smoke\",\"fromBookingDateTime\":\"2026-10-01T00:00:00+07:00\",\"toBookingDateTime\":\"2026-10-26T23:59:59+07:00\"}"

[ $status = 0 ] && ok "no 5xx" || warn "a call failed (5xx or no answer)"
exit $status
