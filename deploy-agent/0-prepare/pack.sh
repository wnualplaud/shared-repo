#!/usr/bin/env bash
# session: Git Bash (corp machine), from a restored copy; reads only, writes only <out-dir>
# pack what the two CloudShells need, into a new folder outside the restored copy
#   bash deploy-agent/0-prepare/pack.sh <env-file> <out-dir>
# <out-dir> must not exist yet. It gets:
#   build.tar.gz     CloudShell: upload, `tar xzf build.tar.gz`, then step 2 (build)
#                    holds repo/, deploy-agent/ and the env file; text files in LF
#   smoke-paste.txt  CloudShell VPC environment (no uploads): paste it whole; it writes
#                    ~/s16-smoke/ (lib, smoke script, env) and runs step 4b
set -euo pipefail
KIT="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$KIT/.." && pwd)"
source "$KIT/99-libs/lib.sh"

env_file=${1:-}; out=${2:-}
[ -n "$out" ] || fail "usage: bash deploy-agent/0-prepare/pack.sh <env-file> <out-dir>"
load_env "$env_file"                       # fails on a missing key, as every step does
[ -e "$out" ] && fail "out-dir already exists: $out"
[ -d "$ROOT/repo" ] || fail "no repo/ next to deploy-agent/ (looked in $ROOT)"
case "$(cd "$(dirname "$out")" 2>/dev/null && pwd)/" in
    "$ROOT"/*) fail "out-dir is inside the restored copy; put it outside: $out" ;;
esac

stage=$(mktemp -d); trap 'rm -rf "$stage"' EXIT
env_name=$(basename "$env_file")

say "build.tar.gz"
cp -r "$ROOT/repo" "$KIT" "$stage/"
cp "$env_file" "$stage/$env_name"
find "$stage" -depth \( -name __pycache__ -o -name .venv -o -name local \) -type d -exec rm -rf {} +
# CR at line ends (a Windows editor or checkout) breaks bash on CloudShell ("invalid option name")
find "$stage" -type f -exec grep -Iq . {} \; -exec sed -i 's/\r$//' {} \;
mkdir -p "$out"
tar czf "$out/build.tar.gz" -C "$stage" repo "$(basename "$KIT")" "$env_name"
ok "$(tar tzf "$out/build.tar.gz" | wc -l) entries: repo/, $(basename "$KIT")/, $env_name"

say "smoke-paste.txt"
D=__S16_SMOKE_EOF__
for f in "$KIT/99-libs/lib.sh" "$KIT/4b-verify-inside/smoke.sh" "$env_file"; do
    grep -q "$D" "$f" && fail "$f contains the heredoc marker $D"
done
put() {  # file -> a heredoc that writes it (quoted marker: nothing expands; newline ensured)
    echo "cat > ~/s16-smoke/$2 <<'$D'"
    tr -d '\r' < "$1" | sed -e '$a\'
    echo "$D"
}
{
    echo "# paste all of this into the CloudShell VPC environment; it writes ~/s16-smoke/ and runs the smoke"
    echo "rm -rf ~/s16-smoke && mkdir -p ~/s16-smoke/99-libs ~/s16-smoke/4b-verify-inside"
    put "$KIT/99-libs/lib.sh" 99-libs/lib.sh
    put "$KIT/4b-verify-inside/smoke.sh" 4b-verify-inside/smoke.sh
    put "$env_file" "$env_name"
    echo "CLOUDSHELL=1 bash ~/s16-smoke/4b-verify-inside/smoke.sh ~/s16-smoke/$env_name"
} > "$out/smoke-paste.txt"
ok "$(wc -l < "$out/smoke-paste.txt") lines"

say "next"
echo "   CloudShell:     upload $out/build.tar.gz; tar xzf build.tar.gz"
echo "                   CLOUDSHELL=1 bash $(basename "$KIT")/2-build/build-push.sh $env_name <tag> repo"
echo "   CloudShell VPC: open $out/smoke-paste.txt, copy all, paste"
