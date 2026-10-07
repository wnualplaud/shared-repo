#!/usr/bin/env bash
# load-mock.sh <items.json>
#   writes the items into the table named inside the file, then prints the item count.
#   File format: {"<table>": [{"PutRequest": {"Item": {...}}}, ...]}  (max 25 items per file)
set -euo pipefail
# Windows AWS CLI reads file:// with the system code page; the data has Thai text.
export AWS_CLI_FILE_ENCODING=UTF-8
F="${1:?usage: load-mock.sh <items.json>}"

export AWS_PROFILE="${AWS_PROFILE:-yourdata-uat}"
export AWS_REGION="${AWS_REGION:-ap-southeast-7}" AWS_DEFAULT_REGION="${AWS_REGION}"

T=$(sed -n 's/^{ *"\([^"]*\)".*/\1/p; s/^ *"\([^"]*\)": *\[.*/\1/p' "$F" | head -1)
echo "account=$(aws sts get-caller-identity --query Account --output text) profile=$AWS_PROFILE region=$AWS_REGION table=$T file=$F"

aws dynamodb batch-write-item --request-items "file://$F" --query UnprocessedItems
echo "items in $T: $(aws dynamodb scan --table-name "$T" --select COUNT --query Count --output text)"
