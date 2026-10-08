# deploy/

Scripts and templates to deploy the API image to ECS Fargate. No
environment values live here; they come from `config/<env>.env`.

```text
config/env.example   every key, placeholder values (shared)
config/<env>.env     real values (git-ignored); see config/README.md
templates/           JSON with ${VAR} placeholders
scripts/             lib.sh + numbered steps
out/<env>/           rendered JSON actually sent (git-ignored)
```

```bash
bash scripts/compare-env.sh uat      # keys: env.example <-> uat.env, both ways
bash scripts/validate-env.sh uat     # offline: config/uat.env complete and well-formed
bash scripts/00-check.sh uat           # read-only: everything referenced exists
bash scripts/10-task-role.sh uat       # create task role if missing, write its policy
bash scripts/20-task-definition.sh uat # register a new revision
bash scripts/30-run-task.sh uat        # run one task, report status/health/logs
```

CloudShell (docker available) and CloudShell VPC environment (inside the VPC):

```bash
bash scripts/build-push.sh <deliverables-dir> <ecr-repo> <remote-tag>   # CloudShell
bash scripts/smoke-test.sh <task-private-ip>                             # CloudShell VPC environment
```

`build-push.sh` refuses an existing tag; set the new tag as `IMAGE_TAG` in
`config/<env>.env`, then run `20-task-definition.sh` and `30-run-task.sh`.
