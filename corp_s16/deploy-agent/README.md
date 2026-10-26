# deliverables/deploy-agent

The deploy kit written by the agent for api r01 (prelim mode, user
2026-10-26), after the vendor's flow; tried end to end on the rehearsal
copy (`releases/rehearsal/r01-...`). The user's own kit, written to
learn, is `../deploy/` (same layout). Nothing real in these files:
values come from an env file in `../local/`.

| Folder | Session | Reads / changes | Run |
|---|---|---|---|
| `0-prepare/` | by hand | -- | copy `uat.env.example` to `../local/uat.env`, fill it; copy this folder to each session |
| `1-preflight/` | Git Bash | reads | `bash 1-preflight/check-env.sh <env>`, `bash 1-preflight/check-aws.sh <env>` |
| `2-build/` | CloudShell | changes ECR | `CLOUDSHELL=1 bash 2-build/build-push.sh <env> <tag> [app-dir]` |
| `3-release/` | Git Bash | changes ECS | `bash 3-release/deploy.sh <env> <tag> --dry-run`, then without `--dry-run` |
| `4a-verify-outside/` | Git Bash | reads | `bash 4a-verify-outside/check.sh <env> <family:revision>` |
| `4b-verify-inside/` | CloudShell VPC environment | reads | `CLOUDSHELL=1 bash 4b-verify-inside/smoke.sh <env>` |
| `9-recover/` | Git Bash | changes ECS | `bash 9-recover/rollback.sh <env> <family:revision>` |
| `99-libs/` | -- | -- | `lib.sh`, loaded by every script |

The order, and what to look at after each: `runbook.md`. Evidence of each
run goes to `../local/runs/<stamp>-<step>/` (outside git).
