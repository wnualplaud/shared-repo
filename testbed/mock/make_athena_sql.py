"""Stand-in exporter (api r06): accounts.json -> out/<table>.insert.sql, .delete.sql.

Agent-written, like make_dynamodb_items.py; the general exporter belongs
to testbed r02. The SQL holds what loading means, so the executor
(ops/local/jobs/athena-run-sql.sh) only runs files:
- insert: rows whose key (schema "key") is not in the table yet, so it
  can run again, and rows added later go in without doubling the rest;
  a changed row with the same key is not updated (delete, then insert).
- delete: every mock row (schema "mock_marker"), to start over.
One statement a file, no trailing `;` (Athena runs one at a time);
the database keeps `${ENV}` for envsubst.

    python3 mock/make_athena_sql.py
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA_DIR = HERE.parent / "schema"
OUT_DIR = HERE / "out"
TABLES = ["rdx_tbl3"]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def transaction_rows(accounts, schema):
    # one row per transaction; account columns from the parent level,
    # the transaction's own win on a shared name (data_dt: booking date here)
    cols = [c["name"] for c in schema["columns"]]
    for citizen in accounts:
        for acc in citizen["accounts"]:
            for txn in acc.get("transactions", []):
                ctx = {**acc, **txn}
                yield {c: ctx.get(c) for c in cols}


def literal(value, column):
    if value is None:
        return f"CAST(NULL AS {column['sql_type']})"
    fmt = column.get("format")
    if fmt == "decimal":
        return f"DECIMAL '{value}'"
    if fmt == "date-time":
        # ISO 8601 with offset, as in accounts.json; Athena keeps it as UTC
        return f"CAST(from_iso8601_timestamp('{value}') AS {column['sql_type']})"
    return "'" + str(value).replace("'", "''") + "'"


def insert_sql(schema, rows):
    table = f"{schema['database']}.{schema['table']}"
    names = [c["name"] for c in schema["columns"]]
    values = ",\n".join(
        "    (" + ", ".join(literal(r[c["name"]], c) for c in schema["columns"]) + ")"
        for r in rows
    )
    key = " AND ".join(f"t.{k} = v.{k}" for k in schema["key"])
    return (
        f"INSERT INTO {table} ({', '.join(names)})\n"
        f"SELECT {', '.join('v.' + n for n in names)}\n"
        f"FROM (VALUES\n{values}\n) AS v ({', '.join(names)})\n"
        f"WHERE NOT EXISTS (SELECT 1 FROM {table} t WHERE {key})\n"
    )


def delete_sql(schema):
    table = f"{schema['database']}.{schema['table']}"
    where = " AND ".join(f"{k} = '{v}'" for k, v in schema["mock_marker"].items())
    return f"DELETE FROM {table} WHERE {where}\n"


def main():
    accounts = read_json(HERE / "accounts.json")
    OUT_DIR.mkdir(exist_ok=True)
    for t in TABLES:
        schema = read_json(SCHEMA_DIR / f"{t}.json")
        rows = list(transaction_rows(accounts, schema))
        missing = [k for k in schema["key"] for r in rows if r[k] is None]
        if missing:
            raise SystemExit(f"{t}: rows without a key value ({', '.join(sorted(set(missing)))})")
        for kind, sql in [("insert", insert_sql(schema, rows)), ("delete", delete_sql(schema))]:
            out = OUT_DIR / f"{t}.{kind}.sql"
            out.write_text(sql, encoding="utf-8")
            print(out.relative_to(HERE.parent), len(rows) if kind == "insert" else "", kind)


if __name__ == "__main__":
    main()
