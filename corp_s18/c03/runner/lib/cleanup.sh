run_cleanup() {
    local list="$1" line db tbl n ans
    [ -f "$list" ] || die "no $list"
    start_log "cleanup_$(basename "$list")"

    while IFS= read -r line <&3; do
        line="${line%%#*}"
        line="$(tr -d '[:space:]' <<<"$line")"
        [ -z "$line" ] && continue

        db="${line%%.*}"; tbl="${line#*.}"
        if [ "$db" = "$line" ];          then say "skip $line: write it as <db>.<table>"; continue; fi
        if [ "${db,,}" != "${TMP_DB,,}" ]; then say "skip $line: not in $TMP_DB";          continue; fi
        if ! table_exists "$db" "$tbl";  then say "skip $line: does not exist";           continue; fi

        say "---- $line"
        bl -e "DESCRIBE FORMATTED $line;" | grep -Ei 'Location|Table Type|external.table.purge' || true
        n=$(bl_value "SELECT COUNT(*) FROM $line;") || n="?"
        say "rows: $n"

        read -r -p "drop $line and its files? type the table name to confirm: " ans
        if [ "${ans,,}" = "${tbl,,}" ]; then
            bl -e "ALTER TABLE $line SET TBLPROPERTIES ('external.table.purge'='true');
                   DROP TABLE $line;" || die "drop $line failed (see $LOG)"
            say "dropped $line"
        else
            say "kept $line"
        fi
    done 3< "$list"
}
