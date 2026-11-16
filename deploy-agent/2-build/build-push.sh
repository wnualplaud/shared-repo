#!/usr/bin/env bash
# session: CloudShell (docker)
# build the image from the app folder and push it under a new tag (refuses a tag that exists)
#   CLOUDSHELL=1 bash build-push.sh <env-file> <tag> [app-dir]     app-dir defaults to ../../repo
set -euo pipefail
source "$(dirname "$0")/../99-libs/lib.sh"
load_env "${1:-}"
TAG=${2:?tag, e.g. api-20261026-01}
APP_DIR=${3:-$(dirname "$0")/../../repo}
IMAGE="$REGISTRY/$ECR_REPO:$TAG"

say "checks"
command -v docker >/dev/null || fail "no docker here"
[ -f "$APP_DIR/Dockerfile" ] || fail "no Dockerfile in $APP_DIR"
if aws ecr describe-images --repository-name "$ECR_REPO" --image-ids imageTag="$TAG" >/dev/null 2>&1; then
    fail "tag $TAG exists in $ECR_REPO: pick a new one"
fi
ok "tag $TAG is new"

say "build $TAG"
docker build --platform linux/amd64 -t "$IMAGE" "$APP_DIR"

say "push"
aws ecr get-login-password | docker login --username AWS --password-stdin "$REGISTRY"
docker push "$IMAGE"
ok "pushed $ECR_REPO:$TAG"
