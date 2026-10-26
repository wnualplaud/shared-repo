# shared by every step: load the env file, report, keep a run log
# usage in a script:  source "$(dirname "$0")/../99-libs/lib.sh"; load_env "$1"

KEYS="AWS_REGION ACCOUNT_ID ECR_REPO CLUSTER SERVICE CONTAINER LOG_GROUP"

say()  { echo "== $*"; }
ok()   { echo "   ok    $*"; }
warn() { echo "   WARN  $*"; }
fail() { echo "   FAIL  $*"; exit 1; }
none() { [ -z "${1:-}" ] || [ "$1" = None ]; }

load_env() {  # env file
    [ -f "${1:-}" ] || fail "env file not found: ${1:-<none given>}"
    set -a; source "$1"; set +a
    local k
    for k in $KEYS; do [ -n "${!k:-}" ] || fail "$k is empty in $1"; done
    # CloudShell sessions carry their own credentials: no profile there
    if [ "${CLOUDSHELL:-}" = 1 ] || [ -z "${AWS_PROFILE:-}" ]; then unset AWS_PROFILE; fi
    export AWS_DEFAULT_REGION="$AWS_REGION"
    export AWS_RETRY_MODE=adaptive AWS_MAX_ATTEMPTS=10
    REGISTRY="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
}

run_dir() {  # -> a folder for this run's evidence, outside git (deliverables/local/runs/<stamp>)
    local d
    d="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/local/runs/$(date +%Y%m%d-%H%M%S)-$1"
    mkdir -p "$d"; echo "$d"
}

current_task_def() {  # the task definition ARN the service runs now
    aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" \
        --query 'services[0].taskDefinition' --output text
}
