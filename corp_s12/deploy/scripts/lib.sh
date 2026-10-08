# shared helpers; sourced by the numbered scripts
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${1:?usage: $0 <env>   (loads config/<env>.env)}"
CONFIG="$DEPLOY_DIR/config/$ENV_NAME.env"
[ -f "$CONFIG" ] || { echo "missing $CONFIG (copy $ENV_NAME.env.example and fill it)"; exit 1; }

# placeholders left in a value line (comments ignored)
if grep -n '<[^>]*>' "$CONFIG" | grep -v '^[0-9]*:[[:space:]]*#' | grep -q .; then
  echo "unfilled values in $CONFIG:"; grep -n '<[^>]*>' "$CONFIG" | grep -v '^[0-9]*:[[:space:]]*#'; exit 1
fi

# strip Windows CRLF so values do not end in \r
set -a; . <(sed 's/\r$//' "$CONFIG"); set +a
export AWS_DEFAULT_REGION="$AWS_REGION"
export AWS_CLI_FILE_ENCODING=UTF-8      # Windows AWS CLI reads file:// with the system code page
export MSYS_NO_PATHCONV=1               # Git Bash: keep /ecs/... as is


ACCOUNT_ID="${ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
export ACCOUNT_ID
# work from deploy/ and pass relative paths to the CLI: on Git Bash, aws.exe cannot open
# /c/Users/... paths (MSYS_NO_PATHCONV=1 keeps them unconverted)
cd "$DEPLOY_DIR"
OUT_DIR="out/$ENV_NAME"; mkdir -p "$OUT_DIR"

show_target() {
  echo "env=$ENV_NAME profile=$AWS_PROFILE region=$AWS_REGION account=$ACCOUNT_ID"
}

# render <template> <output>: replace every ${VAR} with its value; fail on any left over
render() {
  local src="$1" dst="$2" text var
  text="$(cat "$src")"
  for var in $(grep -o '\${[A-Z_][A-Z0-9_]*}' "$src" | sort -u | tr -d '${}'); do
    [ -n "${!var:-}" ] || { echo "no value for \${$var} in $src"; exit 1; }
    text="${text//"\${$var}"/${!var}}"
  done
  printf '%s\n' "$text" > "$dst"
  echo "rendered $dst"
}
