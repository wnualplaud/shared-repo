run_check() {
    local code="$1"; shift
    local f files=()
    for f in checks/"$code"*.sql; do [ -e "$f" ] && files+=("$f"); done
    [ ${#files[@]} -gt 0 ] || die "no checks/${code}*.sql"
    dates "$@"
    start_log "check_$code"

    for f in "${files[@]}"; do
        if sed 's/--.*//' "$f" | grep -Eiq '\b(create|insert|drop|alter|truncate|delete|update|msck|load)\b'; then
            die "$f has a write statement; checks are read only"
        fi
    done

    for f in "${files[@]}"; do
        say "==== $(basename "$f" .sql); created $FROM..$TO; snapshot $DL_DATA_DT"
        sed -n '1,/^$/p' "$f" | tee -a "$LOG"
        bl -f "$f" "${HV[@]}" --hivevar from_dt="$FROM" --hivevar to_dt="$TO" \
            || die "check $f failed (see $LOG)"
    done
}
