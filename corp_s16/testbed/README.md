# deliverables/testbed

Mock data for the tables the API reads. Written by the agent (prelim
mode, user 2026-10-27); the testbed package (tables + Athena + data) is
designed later.

## mock_dynamo.py

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
python3 mock_dynamo.py uat --dry-run --institution <name>   # what it would delete and write; reads only
python3 mock_dynamo.py uat --institution <name>             # delete MOCK rows, write the cases
python3 mock_dynamo.py uat --institution <name> --random 5  # plus 5 random citizens (--seed fixes them)
python3 mock_dynamo.py uat --keep-old                       # write without deleting first
```

Where: CloudShell in the UAT account (python3 and boto3 are there).
Elsewhere: `AWS_PROFILE` and `AWS_DEFAULT_REGION` set, `aws sso login`,
and `pip install boto3`. It prints the last 4 digits of the account
first: check them before a real run.

Tried on the personal account's `dev` tables (2026-10-27): the first run
deleted the old set (12 detail rows, 11 list rows), a second run gives
the same 11 + 11; the app's PartiQL returns `1234567001` and
`1234567005` for citizen `1234567890001` `SAVING#`.

## mock_sheet.py

The same rows as one Excel sheet for testers: one account per row, the
API's field names as columns (request keys, then what decides whether
the API returns the row, names, account, balance, system columns),
`visibleInApi` (`N` for `JOINT` / `JURISTIC`), and a Thai note last.
Every cell is text, so long ids and amounts keep their digits. Reads no
AWS; needs `openpyxl`.

```bash
python3 mock_sheet.py --institution <name> -o mock_accounts.xlsx
```

Give it the same `--institution` / `--random` / `--seed` as the
`mock_dynamo.py` run, so the random balances and dates match.

Not covered: `/rdx_ep4` (Athena in UAT not known yet).

Note: DynamoDB stores numbers without trailing zeros (`-2500.00` comes
back as `-2500`), so an API amount can differ in form from the sheet;
for the decimal toy.
