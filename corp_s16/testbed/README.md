# deliverables/testbed

Mock data for the tables the API reads. Written by the agent (prelim
mode, user 2026-10-27); the testbed package (tables + Athena + data) is
designed later.

## mock_dynamo.py

Deletes every row marked `src_stm_id = MOCK` in the two DynamoDB tables
(the old S12 stand-ins and earlier runs), then writes a fixed set of
cases: subtypes `SAVING` / `CURRENT` / `TERM`, owner filter (`JOINT`,
`JURISTIC`), TH fallback, negative / zero / largest balance, credit
limit, missing available balance, a citizen with no eligible account,
several accounts of one subtype, a detail row in no list. Ids start
with `999`; names are `ทดสอบ <accountId>` / `TEST <accountId>`; amounts
are `N` (as `Decimal`). Rows from anyone else are never touched.

```bash
python3 mock_dynamo.py uat --dry-run      # shows what it would delete and write; reads only
python3 mock_dynamo.py uat                # delete MOCK rows, write the cases
python3 mock_dynamo.py uat --random 5     # plus 5 random citizens (--seed fixes them)
python3 mock_dynamo.py uat --keep-old     # write without deleting first
```

Where: CloudShell in the UAT account (python3 and boto3 are there; the
region is the session's). Elsewhere: `AWS_PROFILE` and `AWS_REGION` set,
and `pip install boto3`. It prints the last 4 digits of the account
first: check them before a real run.

Tried on the personal account's `dev` tables (2026-10-27): delete + write
twice gives the same rows; the app's PartiQL returns `9990000001` and
`9990000005` for citizen `...0001` `SAVING#`, nothing for `...0003`.

Not covered: `/rdx_ep4` (Athena in UAT not known yet).

Note: DynamoDB stores numbers without trailing zeros (`-2500.00` comes
back as `-2500`); for the decimal toy.
