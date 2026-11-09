run_check() {
    local nn="$1"; shift
    local f
    f=$(ls checks/"$nn"_*.sql 2>/dev/null | head -1) || true
    [ -n "$f" ] || die "no checks/${nn}_*.sql"
    dates "$@"
    start_log "check_$(basename "$f" .sql)"

    if sed 's/--.*//' "$f" | grep -Eiq '\b(create|insert|drop|alter|truncate|delete|update|msck|load)\b'; then
        die "$f has a write statement; checks are read only"
    fi

    say "check $f; created $FROM..$TO; snapshot $SNAP_DT"
    bl -f "$f" "${HV[@]}" --hivevar from_dt="$FROM" --hivevar to_dt="$TO" \
        || die "check failed (see $LOG)"
}
