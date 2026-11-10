#!/usr/bin/env bash
# run.sh --- c03 dev runner: build temp tables from queries, read checks, clean up.
# Draft by the agent, 2026-11-10. Not run yet. Runs where beeline works, from any folder.
#
#   ./run.sh <env> list                          jobs, checks, cleanup lists (no beeline)
#   ./run.sh <env> tables                        do the tables the queries read and the jobs make exist? read only
#   ./run.sh <env> job <name> [--from D] [--to D] [--dry-run]
#                                                jobs/<name>.conf -> ${TMP_DB}.<OUT>; --dry-run: show the SQL, run nothing
#   ./run.sh <env> summary <table>               rows, days, Y / N, keys filled, of ${TMP_DB}.<table>
#   ./run.sh <env> check <nn> [--from D] [--to D]  checks/<nn>_*.sql, read only, result to screen + log
#   ./run.sh <env> cleanup <file>                drop the tables listed in <file>, one by one, each confirmed
#
#   <env>   env/<env>.env (uat, prod ...); copy env/example.env.
#
# Writes only: new tables in ${TMP_DB} named ${PREFIX}*, never an existing one.
# Drops only:  tables in ${TMP_DB} listed by hand in a cleanup file.
# Logs:        logs/<env>/<time>_<what>.log; a job also keeps its generated .hql there.

set -euo pipefail
cd "$(dirname "$0")"

. lib/common.sh
. lib/job.sh
. lib/check.sh
. lib/cleanup.sh
. lib/tables.sh

usage() { sed -n '2,19p' "$0"; exit 1; }

[ $# -ge 2 ] || usage
ENV_NAME="$1"; cmd="$2"; shift 2

if [ "$cmd" = list ]; then list_all; exit 0; fi

load_env "$ENV_NAME"

case "$cmd" in
    tables)  run_tables ;;
    job)     run_job    "${1:?job <name>}"     "${@:2}" ;;
    summary) run_summary "${1:?summary <table>}" ;;
    check)   run_check   "${1:?check <nn>}"     "${@:2}" ;;
    cleanup) run_cleanup "${1:?cleanup <file>}" ;;
    *)       usage ;;
esac
