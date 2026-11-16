# Deploy Runbook (UAT)

`<env>` is the env file: on Git Bash, wherever you keep it (on the corp
machine `corp_s16_local/uat.env`, outside the restored copy); on
CloudShell, the copy that came in the pack. `<tag>` is new each time:
`api-YYYYMMDD-NN`. Git Bash steps run from the restored copy's root
(`repo/` and `deploy-agent/` side by side).

## 0. Prepare (by hand)

1. The env file filled from `0-prepare/uat.env.example`.
2. Git Bash: `aws sso login --profile <AWS_PROFILE>`; optionally
   `export RUNS_DIR=<a folder outside the restored copy>` so run evidence
   goes there (default: `local/runs/` beside `deploy-agent/`).
3. Pick the tag, e.g. `api-20261027-01`.
4. Git Bash: pack for the two CloudShells, into a new folder outside the
   restored copy:

   ```bash
   bash deploy-agent/0-prepare/pack.sh <env> <out-dir>
   ```

   `build.tar.gz` (repo, kit, env; LF line ends) is for step 2;
   `smoke-paste.txt` is for step 4b.
5. CloudShell: upload `build.tar.gz`, then `tar xzf build.tar.gz`.

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

This environment takes no uploads: open `smoke-paste.txt` from step 0,
copy all of it, paste. It writes `~/s16-smoke/` and runs

```bash
CLOUDSHELL=1 bash ~/s16-smoke/4b-verify-inside/smoke.sh ~/s16-smoke/<env file name>
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
