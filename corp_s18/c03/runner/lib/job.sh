run_job() {
    local name="$1"; shift
    local conf="jobs/$name.conf" t sql
    [ -f "$conf" ] || die "no $conf"
    local DESC="" QUERY="" OUT="" NEEDS="" SETTINGS=""
    . "$conf"
    dates "$@"
    start_log "job_$name"

    [ -n "$QUERY" ] && [ -f "queries/$QUERY" ] || die "$conf: QUERY=queries/$QUERY not found"
    [ -n "$OUT" ] || die "$conf: OUT is empty"
    guard_name "$OUT"

    say "job $name: $DESC"
    say "query queries/$QUERY -> $TMP_DB.$OUT; created $FROM..$TO; snapshot $SNAP_DT"

    if [ -n "$DRY" ]; then
        say "dry run: no beeline; NEEDS ($NEEDS) and whether $OUT exists are not checked"
    else
    for t in $NEEDS; do
        table_exists "$TMP_DB" "$t" || die "needs $TMP_DB.$t: run its job first"
    done
    if table_exists "$TMP_DB" "$OUT"; then
        die "$TMP_DB.$OUT exists already; to rebuild, list it in a cleanup file and run cleanup first"
    fi
    fi

    sql="${LOG%.log}.hql"
    {
        [ -n "$SETTINGS" ] && printf '%s\n' "$SETTINGS"
        echo "CREATE EXTERNAL TABLE $TMP_DB.$OUT"
        echo "STORED AS PARQUET"
        echo "TBLPROPERTIES ('external'='false', 'external.table.purge'='true')"
        echo "AS"
        sed -e 's/;[[:space:]]*$//' "queries/$QUERY"
        echo ";"
    } > "$sql"
    say "generated $sql"

    if [ -n "$DRY" ]; then
        resolve "$sql" > "${sql%.hql}.resolved.hql"
        cat "${sql%.hql}.resolved.hql" | tee -a "$LOG"
        say "dry run done: ${sql%.hql}.resolved.hql (nothing was run)"
        return 0
    fi

    bl -f "$sql" "${HV[@]}" --hivevar from_dt="$FROM" --hivevar to_dt="$TO" \
        || die "job $name failed (see $LOG)"
    say "done. next: ./run.sh $ENV_NAME summary $OUT"
}

run_summary() {
    local t="$1"
    start_log "summary_$t"
    table_exists "$TMP_DB" "$t" || die "$TMP_DB.$t does not exist"
    bl -e "SELECT COUNT(*)                                             AS n_rows,
                  COUNT(DISTINCT DL_DATA_DT)                           AS n_days,
                  MIN(DL_DATA_DT)                                      AS first_day,
                  MAX(DL_DATA_DT)                                      AS last_day,
                  SUM(CASE WHEN SURPRISE_FLAG = 'Y' THEN 1 ELSE 0 END) AS n_y,
                  SUM(CASE WHEN SURPRISE_FLAG = 'N' THEN 1 ELSE 0 END) AS n_n,
                  COUNT(SRC_RDXSRC_CODE)                                  AS n_key_filled
           FROM $TMP_DB.$t;"
}
