# corp/s16

S16's files for the corp machine, redacted. This branch holds only these
files (no history shared with `main`); `main`'s `corp_s16/` is the older
way and stays as history.

| Folder | What |
|---|---|
| `repo/` | the app |
| `deploy-agent/` | the deploy kit (`deploy-agent/README.md`, `runbook.md`) |
| `testbed/` | mock data and test scripts |
| `redact-cases.md` | one line per redaction rule, to read after `restore` |

## On the corp machine

First time:

```sh
git clone --single-branch --branch corp/s16 <shared-repo url> s16
cd s16
python redact.py restore .      # the private redact script, kept outside this repo
```

Each later send:

```sh
git checkout -- .               # drop the restored names (tracked files only)
git clean -fd repo testbed deploy-agent   # drop renamed handler folders left by restore
git pull
python redact.py restore .
```

Never commit or push from the corp machine. `local/` and `runs/` are
ignored, so an env file and run evidence kept there survive each pull.
