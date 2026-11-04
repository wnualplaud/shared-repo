# Deploy Runbook (UAT)

`<env>` is `../local/uat.env` on Git Bash; on CloudShell, the copy you
uploaded. `<tag>` is new each time: `api-YYYYMMDD-NN`.

## 0. Prepare (by hand)

1. `../local/uat.env` filled from `0-prepare/uat.env.example`.
2. Git Bash: `aws sso login --profile <AWS_PROFILE>`.
3. Pick the tag, e.g. `api-20261027-01`.
4. CloudShell: upload `deploy-agent/` (with `99-libs/`), the env file and
   `repo/` (zip, then unzip).

## 1. Preflight (Git Bash, reads)

```bash
bash 1-preflight/check-env.sh <env>
bash 1-preflight/check-aws.sh <env>
```

Look at: every line `ok`; the **rollback point** (e.g. `rdx-uat-ecs:13`):
write it down. `WARN running 2 of 1` outside a deploy means tasks are
being replaced: look at the service events before going on.

## 2. Build (CloudShell, changes ECR)

```bash
CLOUDSHELL=1 bash 2-build/build-push.sh <env> <tag> <path-to-repo>
```

Look at: `pushed <repo>:<tag>`. A `FAIL tag ... exists` means pick a new
tag. Takes a few minutes, mostly silent.

## 3. Release (Git Bash, changes ECS)

```bash
bash 3-release/deploy.sh <env> <tag> --dry-run
```

Look at: the diff shows **one line**, the image; with `TASK_ENV` in the
env file, also one `"value"` line per name in it (and `container env to
set: ...` above the diff). Anything more: stop. Rollback (step 9) goes
back to the old revision, so its env values come back too.

```bash
bash 3-release/deploy.sh <env> <tag>
```

Look at: `stable on <family:new revision>`. The last step waits silently
for up to 10 minutes: not hung (the rehearsal's rollback took 9 min 12 s).
On `FAIL not stable`, run 4a first and judge from what it shows before
rolling back.

## 4a. Verify outside (Git Bash, reads)

```bash
bash 4a-verify-outside/check.sh <env> <family:new revision>
```

Look at: `runs <new revision>`; targets `healthy`; `running 1 of 1`; no
error lines in the logs; exit code 0. Anything else is a real problem
(B10, the health check path, was fixed on 2026-10-27). The saved
`target-health.txt`, `events.txt` and `logs.txt` are the evidence to send
the vendor.

## 4b. Verify inside (CloudShell VPC environment, reads)

```bash
CLOUDSHELL=1 bash 4b-verify-inside/smoke.sh <env>
```

Look at: `/health 200`; no 5xx and no `000` (no answer). 4xx can be the
data; with `SMOKE_*` set to a mock account all five answer `200`. Then rerun 4a to keep the smoke calls in the logs.

## 9. Recover (Git Bash, changes ECS), only if 4a / 4b fail

```bash
bash 9-recover/rollback.sh <env> <rollback point from step 1>
```

Look at: `back on <revision>`; then 4a again with that revision. The
same long wait as step 3 applies.

## After

- `git tag -a s16/api/r01 <commit deployed>`; note the tag, revisions and
  what was seen in `releases/api/r01-.../README.md` (Deploy).
- Tell the client the keys changed.
