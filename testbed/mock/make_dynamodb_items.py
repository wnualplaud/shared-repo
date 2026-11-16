"""Stand-in exporter (api r06): accounts.json -> out/<table>.items.json.

Agent-written so the user can start on the insert side; the general
exporter (grain, column source level, aliases) belongs to testbed r02.
Output is `aws dynamodb batch-write-item --request-items` form, one
request (<= 25 items) per file; the table name keeps `${ENV}` for envsubst.

    python mock/make_dynamodb_items.py
"""

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA_DIR = HERE.parent / "schema"
OUT_DIR = HERE / "out"
# file name -> table name, written out whole (redact.py replaces whole names only)
TABLES = {
    "rdx_tbl1": "rdx${ENV}_tbl1",
    "rdx_tbl2": "rdx${ENV}_tbl2",
}
MAX_ITEMS = 25  # BatchWriteItem limit per request
TYPED_VALUE = re.compile(r'\{\n\s+"([SN])": ("(?:[^"\\]|\\.)*")\n\s+\}')


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def account_rows(accounts, schema):
    # both tables are one row per account; citizenId comes from the parent level
    cols = [c["name"] for c in schema["columns"]]
    for citizen in accounts:
        for acc in citizen["accounts"]:
            ctx = {"citizenId": citizen["citizenId"], **acc}
            yield {c: ctx[c] for c in cols}


def to_item(row, schema):
    item = {}
    for c in schema["columns"]:
        value = row[c["name"]]
        if value is None:
            continue  # DynamoDB: a null is an absent attribute
        kind = "N" if c.get("format") == "decimal" else "S"
        item[c["name"]] = {kind: value}
    return item


def render(request):
    # indented JSON, but each typed value on one line: "name": {"S": "value"}
    text = json.dumps(request, ensure_ascii=False, indent=2)
    text = TYPED_VALUE.sub(r'{"\1": \2}', text)
    return text + "\n"


def main():
    accounts = read_json(HERE / "accounts.json")
    OUT_DIR.mkdir(exist_ok=True)
    for t, table in TABLES.items():
        schema = read_json(SCHEMA_DIR / f"{t}.json")
        items = [to_item(r, schema) for r in account_rows(accounts, schema)]
        if len(items) > MAX_ITEMS:
            raise SystemExit(f"{t}: {len(items)} items, more than one request ({MAX_ITEMS}); split first")
        request = {table: [{"PutRequest": {"Item": i}} for i in items]}
        out = OUT_DIR / f"{t}.items.json"
        out.write_text(render(request), encoding="utf-8")
        print(out.relative_to(HERE.parent), len(items), "items")


if __name__ == "__main__":
    main()
