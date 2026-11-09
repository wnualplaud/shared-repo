say() { echo "[$(date +%H:%M:%S)] $*" | tee -a "${LOG:-/dev/null}"; }
die() { echo "ERROR: $*" | tee -a "${LOG:-/dev/null}" >&2; exit 1; }

load_env() {
    local f="env/$1.env" v
    [ -f "$f" ] || die "no $f (copy env/example.env to $f and fill it)"
    . "$f"
    for v in BEELINE_ARGS ENV DBDWENV SNAP_DT FROM_DT TO_DT TMP_DB PREFIX; do
        [ -n "${!v:-}" ] || die "$f: $v is empty"
    done
    [[ "${TMP_DB,,}" == *_tmp_db ]] || die "$f: TMP_DB must be a *_tmp_db database (is $TMP_DB)"
    if [ -n "${HIVE_INIT:-}" ] && [ ! -r "$HIVE_INIT" ]; then die "HIVE_INIT not readable: $HIVE_INIT"; fi

    eval "BL_BASE=($BEELINE_ARGS)"
    HV=(--hivevar environment="$ENV" --hivevar env="$ENV" --hivevar dbdwenv="$DBDWENV" --hivevar snap_dt="$SNAP_DT"
        --hivevar tmp_db="$TMP_DB" --hivevar prefix="$PREFIX")
    LOG_DIR="logs/$1"; mkdir -p "$LOG_DIR"
}

start_log() { LOG="$LOG_DIR/$(date +%Y%m%d_%H%M%S)_$1.log"; say "log: $LOG"; }

bl() {
    local init=()
    [ -n "${HIVE_INIT:-}" ] && init=(-i "$HIVE_INIT")
    beeline "${BL_BASE[@]}" ${init[@]+"${init[@]}"} --silent=true --showHeader=true \
        --outputformat=tsv2 "$@" </dev/null 2>&1 | tee -a "$LOG"
    return "${PIPESTATUS[0]}"
}

bl_value() {
    beeline "${BL_BASE[@]}" --silent=true --showHeader=false --outputformat=tsv2 \
        -e "$1" </dev/null 2>>"$LOG"
}

table_exists() {
    local out
    out=$(bl_value "SHOW TABLES IN $1 LIKE '${2,,}';") || die "could not list tables in $1 (see $LOG)"
    tr -d ' \r' <<<"$out" | grep -qix "$2"
}

guard_name() {
    [[ "${1^^}" == "${PREFIX^^}"* ]] || die "table $1 does not start with $PREFIX"
}

dates() {
    FROM="$FROM_DT"; TO="$TO_DT"
    while [ $# -gt 0 ]; do
        case "$1" in
            --from) FROM="${2:?--from <yyyy-mm-dd>}"; shift 2 ;;
            --to)   TO="${2:?--to <yyyy-mm-dd>}";     shift 2 ;;
            *)      die "unknown option $1" ;;
        esac
    done
}

list_all() {
    local c
    echo "jobs (jobs/*.conf):"
    for c in jobs/*.conf; do
        [ -e "$c" ] || continue
        ( DESC=""; OUT=""; NEEDS=""; . "$c"
          printf '  %-24s -> %-22s needs: %-20s %s\n' "$(basename "$c" .conf)" "$OUT" "${NEEDS:--}" "$DESC" )
    done
    echo "checks (checks/*.sql):"
    for c in checks/*.sql;  do [ -e "$c" ] && echo "  $(basename "$c" .sql)"; done
    echo "cleanup lists (cleanup/*):"
    for c in cleanup/*;     do [ -e "$c" ] && echo "  $c"; done
    return 0
}
