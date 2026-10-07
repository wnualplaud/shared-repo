# config/

One file per environment: `config/<env>.env` (git-ignored), copied from
`config/env.example`. When adding a key, add it to `env.example` and to every
`<env>.env`; `scripts/compare-env.sh <env>` reports keys missing on either side. The scripts
take the env name: `bash scripts/00-check.sh uat` loads `config/uat.env`.

Variables the scripts and templates read (all required):

| Variable | Used for |
|---|---|
| `AWS_PROFILE`, `AWS_REGION` | which account/region every call hits |
| `APP` | tags, policy name, `--started-by` |
| `CLUSTER` | ECS cluster to run in |
| `FAMILY` | task definition family |
| `TASK_ROLE` | role the app uses for AWS calls (created by `10-task-role.sh`) |
| `EXECUTION_ROLE` | role ECS uses to pull the image and write logs |
| `IMAGE_REPO`, `IMAGE_TAG` | ECR repository and tag of the image |
| `LOG_GROUP`, `LOG_PREFIX` | CloudWatch log group and stream prefix |
| `APP_ENV` | replaces `<env>` in query table names |
| `ATHENA_DATABASE`, `ATHENA_WORKGROUP`, `ATHENA_QUERY_TIMEOUT_SECONDS` | Athena settings passed to the app |
| `BUCKET`, `ATHENA_RESULTS_PREFIX`, `MART_DATA_PREFIX` | S3 for query results and Athena table data |
| `TABLE_AC_LIST`, `TABLE_AC_DTL` | DynamoDB tables the task role may read |
| `SUBNETS`, `SECURITY_GROUPS`, `ASSIGN_PUBLIC_IP` | network for `run-task` (comma-separated ids, quoted) |

`ACCOUNT_ID` is looked up with `sts get-caller-identity`; do not set it.
A value still written as `<...>` stops every script.
