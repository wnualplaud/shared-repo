#!/usr/bin/env bash
# build-push.sh <deliverables-dir> <ecr-repo> <remote-tag>
#   Builds the image from <deliverables-dir> and pushes it to <ecr-repo>:<remote-tag>.
#   Run where docker works (CloudShell). Region from AWS_REGION (default ap-southeast-7).
#   e.g. bash build-push.sh ~/serving-api/deliverables <ecr-repo> yourdata-api-uat-20261008-02
set -euo pipefail

SRC="${1:?usage: $0 <deliverables-dir> <ecr-repo> <remote-tag>}"
REPO="${2:?ecr repo name}"
TAG="${3:?remote tag, e.g. yourdata-api-uat-YYYYMMDD-NN}"
export AWS_REGION="${AWS_REGION:-ap-southeast-7}" AWS_DEFAULT_REGION="${AWS_REGION:-ap-southeast-7}"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REG="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
echo "region=$AWS_REGION account=$ACCOUNT_ID image=$REPO:$TAG source=$SRC"

if aws ecr describe-images --repository-name "$REPO" --image-ids imageTag="$TAG" >/dev/null 2>&1; then
  echo "tag $TAG already exists in $REPO; use a new tag (keeps rollback possible)"; exit 1
fi

docker build -t "$REPO:$TAG" "$SRC"
docker run --rm "$REPO:$TAG" sh -c 'python --version; id -u; ls /app/handlers | tr "\n" " "; echo'

aws ecr get-login-password | docker login --username AWS --password-stdin "$REG"
docker tag "$REPO:$TAG" "$REG/$REPO:$TAG"
docker push "$REG/$REPO:$TAG"

aws ecr describe-images --repository-name "$REPO" --image-ids imageTag="$TAG" \
  --query 'imageDetails[0].[imageTags[0],imagePushedAt,imageDigest]' --output text
echo "next: set IMAGE_TAG=$TAG in config/<env>.env, then 20-task-definition.sh and 30-run-task.sh"
