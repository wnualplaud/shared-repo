# corp/s16

S16's files for the corp machine, redacted. This branch holds only these
files (no history shared with `main`); `main`'s `corp_s16/` is the older
way and stays as history.

| Path | What |
|---|---|
| `repo/` | the app (as on GitLab) |
| `deploy-agent/` | the deploy kit (`deploy-agent/README.md`, `runbook.md`) |
| `.checksums.sha1` | sha1 of every file before redaction: checks a restore |
| `redact-cases.md` | one line per redaction rule, to read after `restore` |

## Layout on the corp machine

```
api/
├── corp_s16_repo_redacted/   git clone of this branch: pull only, never edited, can be re-cloned
├── corp_s16_restored/rNN/    restore output per release (real names); nothing written into it
├── corp_s16_pack/rNN/        pack.sh output: build.tar.gz (CloudShell), smoke-paste.txt (CloudShell VPC)
├── corp_s16_local/           uat.env, runs/ (RUNS_DIR): kept across releases
├── toolkits/                 git clone of the `toolkits` branch (redact engine)
└── rules/rules_s16.py        real names, typed by hand, in no git repo
external/
└── rdx-your-data-api/        the GitLab clone
```

## First time

```sh
cd api
git clone --single-branch --branch corp/s16 <shared-repo url> corp_s16_repo_redacted
git clone --single-branch --branch toolkits <shared-repo url> toolkits
mkdir -p rules corp_s16_restored corp_s16_pack corp_s16_local/runs
# type rules/rules_s16.py; fill corp_s16_local/uat.env from deploy-agent/0-prepare/uat.env.example
```

## Each release (example: r07)

```sh
cd api/corp_s16_repo_redacted && git pull
python ../toolkits/redact/redact.py restore ../rules/rules_s16.py . ../corp_s16_restored/r07
cd ../corp_s16_restored/r07 && sha1sum -c --quiet .checksums.sha1   # silent = every file restored right
export RUNS_DIR=$(cd ../../corp_s16_local && pwd)/runs
bash deploy-agent/0-prepare/pack.sh ../../corp_s16_local/uat.env ../../corp_s16_pack/r07
# then deploy-agent/runbook.md, steps 1 to 4b, with ../../corp_s16_local/uat.env
cp -r repo/. ../../../external/rdx-your-data-api/
cd ../../../external/rdx-your-data-api && git status && git diff      # review before committing
```

Notes:

- A `FAILED` line from `sha1sum -c` names a file a rule typo restored
  wrong: fix `rules_s16.py`, delete that `rNN/`, restore again.
- `restore` and `pack.sh` refuse a destination that already exists. To
  redo a release, use a new name (`r07-2`) or delete the old folder.
- Copy into the GitLab clone without deleting: it may hold files this
  branch does not (CI settings).
- Never commit or push from `corp_s16_repo_redacted/`.
