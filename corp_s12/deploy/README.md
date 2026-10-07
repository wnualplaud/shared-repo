# deploy/

Scripts and templates to deploy the API image to ECS Fargate. No
environment values live here; they come from `config/<env>.env`.

```text
config/<env>.env     real values (git-ignored); see config/README.md
templates/           JSON with ${VAR} placeholders
scripts/             lib.sh + numbered steps
out/<env>/           rendered JSON actually sent (git-ignored)
```

```bash
bash scripts/validate-env.sh uat     # offline: config/uat.env complete and well-formed
bash scripts/00-check.sh uat           # read-only: everything referenced exists
bash scripts/10-task-role.sh uat       # create task role if missing, write its policy
bash scripts/20-task-definition.sh uat # register a new revision
bash scripts/30-run-task.sh uat        # run one task, report status/health/logs
```

The image itself is built and pushed separately (CloudShell: docker build,
docker tag, docker push).
