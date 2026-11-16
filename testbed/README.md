# deliverables/testbed

The tables the API reads, built as in UAT, and mock data for them
(testbed r02, 2026-10-29). Run per env (`lab`, `dev`, `uat`; the env
fills the `<env>` in each table name).

| Folder | Holds |
|---|---|
| `tables/` | creating the tables as in UAT (DynamoDB, the Iceberg `rdx_tbl3`) |
| `mock/` | mock rows for them, one set of accounts; `mock_dynamo.py`, `mock_sheet.py` written by the agent (prelim mode, user 2026-10-27) |
| `uatmock/` | our own mock stores in UAT (`APP_ENV=uatmock`): `c11.sh` (create, verify, undo; run in CloudShell), api r06 c11 |

Run from this folder (`python3 mock/mock_dynamo.py ...`).

## mock/mock_dynamo.py

Deletes every row marked `src_stm_id = MOCK` in the two DynamoDB tables
(the old S12 stand-ins and earlier runs), then writes a fixed set of
11 accounts, each with a list row and a detail row: subtypes `SAVING` /
`CURRENT` / `TERM`, owner filter (`JOINT`, `JURISTIC`), TH fallback,
negative / zero / largest balance, credit limit, missing available
balance, a citizen with no eligible account, several accounts of one
subtype. Rows from anyone else are never touched.

- Ids: citizenId `123456789` + 4 digits (`1234567890001`), accountId
  `1234567` + 3 digits (`1234567001`); random cases from `...1001` /
  `...101`.
- Every row `ACTIVE` (the mart writes `ACTIVE` only); names
  `ทดสอบ <accountId>` / `TEST <accountId>`; amounts `N` (as `Decimal`).
- `institutionName` comes from `--institution` (default `MOCK BANK`);
  the real value is given on the command line, so it is not in this
  file.

```bash
python3 mock/mock_dynamo.py uat --dry-run --institution <name>   # what it would delete and write; reads only
python3 mock/mock_dynamo.py uat --institution <name>             # delete MOCK rows, write the cases
python3 mock/mock_dynamo.py uat --institution <name> --random 5  # plus 5 random citizens (--seed fixes them)
python3 mock/mock_dynamo.py uat --keep-old                       # write without deleting first
```

Where: CloudShell in the UAT account (python3 and boto3 are there).
Elsewhere: `AWS_PROFILE` and `AWS_DEFAULT_REGION` set, `aws sso login`,
and `pip install boto3`. It prints the last 4 digits of the account
first: check them before a real run.

Tried on the personal account's `dev` tables (2026-10-27; that env is
`lab` since 2026-10-29, the tables not yet renamed): the first run
deleted the old set (12 detail rows, 11 list rows), a second run gives
the same 11 + 11; the app's PartiQL returns `1234567001` and
`1234567005` for citizen `1234567890001` `SAVING#`.

## mock/test_sheet.py

The test case workbook for the client, from `mock/accounts.json` (the
mock in UAT under `APP_ENV=uatmock`, api r06 c11). Sheets: `test cases`
(request body, expected status and result, data rows, what to
confirm), `accounts` (one row per account: `/rdx_ep1`, `/rdx_ep2`,
`/rdx_ep3`), `transactions` (one row per transaction, the statement
header repeated: `/rdx_ep4`, `/rdx_ep5`). Data columns: system,
source (`src_stm_id`, `data_dt`), WHERE, logic, then the rest in the
API's order; `load_ts` last; `NULL` where the store has no value. The
expected results are worked out from the same rules as the code
(visible = `INDIVIDUAL` / `SINGLE` / `ACTIVE`, the date range in Thai
time). Reads no AWS; needs `openpyxl`.

```bash
python3 mock/test_sheet.py -o test_cases.xlsx
```

## mock/mock_sheet.py

The same rows as one Excel sheet for testers: one account per row.
Columns: `test case` (a Thai note), `visibleInApi` (`N` for `JOINT` /
`JURISTIC`), the keys to send, then the details by importance (names
and branch, account, amounts), system columns last; field columns use
the API's names; `accountKey` is left out.
Every cell is text, so long ids and amounts keep their digits. Reads no
AWS; needs `openpyxl`.

```bash
python3 mock/mock_sheet.py --institution <name> -o mock_accounts.xlsx
```

Give it the same `--institution` / `--random` / `--seed` as the
`mock_dynamo.py` run, so the random balances and dates match.

Not covered yet: `/rdx_ep4`, `/rdx_ep5` (Athena; testbed r02).

Note: DynamoDB stores numbers without trailing zeros (`-2500.00` comes
back as `-2500`), so an API amount can differ in form from the sheet;
for the decimal toy.
