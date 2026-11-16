"""Exporter: mock/accounts.json -> DynamoDB batch-write-item files.

Picks each table's columns from the nested records and writes
mock/out/<table>.items.json (`aws dynamodb batch-write-item --request-items`).
"""

import json
from pathlib import Path


# 1. read schema/<table>.json (columns, types, key)
HERE = Path(__file__).parent
SCHEMA_DIR = HERE.parent / "schema"
TABLES = ["rdx_tbl1", "rdx_tbl2"]

def read_schema(table):
    return json.loads((SCHEMA_DIR / f"{table}.json").read_text())


# 2. read accounts.json

ACCOUNTS_FILE = HERE / "accounts.json"

def read_accounts():
    return json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))


# 3. walk the nesting: rows of rdx_tbl1, rows of rdx_tbl2

def pick_rows(accounts, schema):
    
    cols = [c["name"] for c in schema["columns"]]
    rows = []

    for citizen in accounts:
        


# 4. a row -> DynamoDB's typed form


# 5. write mock/out/<table>.items.json



def main():
    
    accounts = read_accounts()
    print("citizens", len(accounts), "accounts", sum(len(c["accounts"]) for c in accounts))

    for table in TABLES:
        schema = read_schema(table)
        print(table, len(schema["columns"]), schema["key"])


if __name__=="__main__":
    main()