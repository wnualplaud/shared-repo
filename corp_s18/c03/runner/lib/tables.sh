table_refs() {
    local q
    for q in queries/*.sql; do
        sed 's/--.*//' "$q" | resolve \
            | grep -oE '(FROM|JOIN)[[:space:]]+`?[A-Za-z0-9_]+`?\.`?[A-Za-z0-9_]+`?' \
            | awk '{print $2}' | tr -d '`' | sort -u \
            | sed "s|\$| $(basename "$q" .sql)|"
    done
}

run_tables() {
    start_log tables
    local refs outs db t used list kind miss=0
    refs=$(table_refs)
    outs=$(for c in jobs/*.conf; do ( OUT=""; . "$c"; echo "$TMP_DB.$OUT $(basename "$c" .conf)" ); done)

    say "sources: what queries/*.sql read (snapshot partitions not checked)"
    say "temp: what jobs/*.conf make in $TMP_DB"
    printf '%-6s %-8s %-60s %s\n' kind status table "used by / made by" | tee -a "$LOG"

    for db in $( { echo "$refs"; echo "$outs"; } | awk '{split($1,a,"."); print tolower(a[1])}' | sort -u); do
        if ! list=$(bl_value "SHOW TABLES IN $db;"); then
            say "cannot list $db (no such database, or no right to it; see $LOG)"
            list=""; miss=1
        fi
        list=$(tr -d ' \r' <<<"$list" | tr '[:upper:]' '[:lower:]')

        for t in $( { echo "$refs"; echo "$outs"; } | awk -v d="$db" '{split($1,a,"."); if (tolower(a[1])==d) print tolower(a[2])}' | sort -u); do
            if [[ "$db" == "${TMP_DB,,}" && "$t" == "${PREFIX,,}"* ]]; then kind=temp; else kind=source; fi
            used=$( { echo "$refs"; echo "$outs"; } | awk -v n="$db.$t" 'tolower($1)==n {print $2}' | sort -u | paste -sd, -)
            if grep -qx "$t" <<<"$list"; then
                printf '%-6s %-8s %-60s %s\n' "$kind" ok "$db.$t" "$used" | tee -a "$LOG"
            elif [ "$kind" = temp ]; then
                printf '%-6s %-8s %-60s %s\n' "$kind" "not yet" "$db.$t" "$used" | tee -a "$LOG"
            else
                printf '%-6s %-8s %-60s %s\n' "$kind" MISSING "$db.$t" "$used" | tee -a "$LOG"
                miss=1
            fi
        done
    done

    [ "$miss" = 0 ] && say "all source tables exist" || say "some source table or database is missing (above)"
    return "$miss"
}
