# T07 UAT Mock Data

Fake data for the stand-in tables in UAT (`ap-southeast-7`). Every id,
name and amount is made up; the 13-digit `citizenId` values only look
like national ids.

```text
mocked/
  load-mock.sh            DynamoDB loader: ./load-mock.sh <items.json>
  athena-run.sh           Athena runner:   ./athena-run.sh <file.sql | "SQL">
  dynamo1/items.json      account list table   (rdxuat_tbl1)
  dynamo2/items.json      account detail table (rdxuat_tbl2)
  athena1/                transaction table    (rdxuat_db1.rdx_tbl3)
    create_database.sql
    create_table.sql
    insert.sql
```

## Run

```bash
cd mocked
./load-mock.sh dynamo1/items.json
./load-mock.sh dynamo2/items.json

# Athena: fill <DATA_BUCKET> in athena1/create_*.sql first
export ATHENA_OUTPUT_LOCATION=s3://<RESULTS_BUCKET>/athena-results/serving-api/
export ATHENA_WORKGROUP=primary          # or our own workgroup
./athena-run.sh athena1/create_database.sql
./athena-run.sh athena1/create_table.sql
./athena-run.sh athena1/insert.sql
./athena-run.sh "SELECT accountId, count(*) FROM rdxuat_db1.rdx_tbl3 GROUP BY accountId"
```

Both scripts default to `AWS_PROFILE=yourdata-uat` and `ap-southeast-7`
and print the target before doing anything. DynamoDB tables must exist
first. `load-mock.sh` writes with `batch-write-item` (max 25 items per
file) and prints the item count; re-running overwrites the same items.
Re-running `insert.sql` adds the rows again.

## dynamo1 / dynamo2

| accountId | subtype | citizen | Tests |
|---|---|---|---|
| `1000000001` | `SAVINGS` | `...001` | TH + EN names, home branch TH + EN, available balance |
| `1000000002` | `SAVINGS` | `...001` | no `accountNameEn` / `homeBranchEn` (language fallback), no `lastAvailable*`, ledger 0 |
| `2000000001` | `CURRENT` | `...001` | negative ledger, `creditLimit` |
| `3000000001` | `TERM` | `...001` | third subtype for the same citizen |
| `1000000003` | `SAVINGS` | `...002` | second citizen; must not appear in citizen 001 results |

Account list with `SAVINGS` for citizen `...001` returns 2 accounts.

- Keys: dynamo1 = `citizenId` + `accountKey` (`<SUBTYPE>#<accountId>`);
  dynamo2 = `accountId` + `accountSubType`.
- Subtype values are uppercase: `CURRENT`, `SAVINGS`, `TERM`.
- Types: `DECIMAL(18,2)` -> `N`, `TIMESTAMP` -> `S` in ISO 8601.
- Attribute names follow the DynamoDB reference (`lastAvailable*`); the
  API response keys keep the spec spelling (`lastAvaliable*`).
- Optional attributes are left out when empty (the app treats missing
  and empty the same).

## athena1

Columns follow the mart reference (columns without a type there are
`string`); Iceberg, partitioned by `data_dt` (the booking date, used for
partition pruning in the date-range filter); no `accountSubType` column,
same as the reference.

| accountId | Rows | Tests |
|---|---|---|
| `1000000001` | 3 (Oct 1, 3, 5) | date range; `merchantName` TH+EN, TH only, none |
| `2000000001` | 1 | negative balance |
| `3000000001` | 1 | `subAccountLevelMaturityDate` set (term deposit) |
