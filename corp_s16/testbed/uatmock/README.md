# testbed/uatmock

Our own mock stores in UAT (`ap-southeast-7`) for api r06 c11, so the
app can be deployed and smoke-tested before the mart loads its tables.
`APP_ENV=uatmock` names both stores; the rewire to the real ones is
`APP_ENV` (and `ATHENA_DATABASE`) back to `uat` (work-inventory G13).

| Store | Made here |
|---|---|
| DynamoDB | `rdxuatmock_tbl2`, `_rdx_tbl1`, 11 mock accounts (`../mock/out/*.items.json`) |
| Athena | database `rdxuatmock_db1`, Iceberg `rdx_tbl3` at `s3://rdxorg-rdx-uat-share/yourdata-api-mock/iceberg/rdxuatmock_db1/rdx_tbl3/`, 20 mock rows (`../mock/out/rdx_tbl3.insert.sql`) |
| Task role `rdx-uat-ecs-task-role` | inline policy `yourdata-api-uatmock`: DynamoDB read on the two tables, S3 read under `yourdata-api-mock/` (the prefix is not a Lake Formation registered location, as the mart's `gold/` is not: files are read with IAM rights) |
| Lake Formation | the task role: `DESCRIBE` on the database, `SELECT`, `DESCRIBE` on the table |

The same mock (`../mock/accounts.json`) as `lab`, so local results and
UAT results can be compared. Why each choice: api r06 README, c11.

## Run

Where: the UAT account's CloudShell (the user; never from the agent's
machine). Each writing step asks `yes` first and prints the account's
last 4 digits: check them.

1. On your side, zip `deliverables/testbed/` (the script needs
   `tables/` and `mock/out/` beside `uatmock/`); in CloudShell, Actions
   -> Upload file, then:

   ```bash
   unzip -o testbed.zip -d ~/c11 && cd ~/c11/testbed/uatmock   # adjust to the zip's layout
   ```

2. Step by step, pasting each result before the next:

   ```bash
   bash c11.sh check      # read only
   bash c11.sh dynamodb   # expect: ACTIVE, {}, items: 11 (each table)
   bash c11.sh policy     # expect: yourdata-api-uatmock among 7 policies
   bash c11.sh athena     # expect: 3 x SUCCEEDED, rows, accounts: 20 ...
   bash c11.sh grants     # expect: ok
   bash c11.sh verify     # read only: the whole picture
   ```

3. To remove everything: `bash c11.sh undo`.

If a step fails: stop, paste the message. Re-running `dynamodb` after a
partial run fails on "table already exists"; `athena`'s insert can run
again (it skips rows already there).

## Then

api r06 c12: deploy with `APP_ENV=uatmock`,
`ATHENA_DATABASE=rdxuatmock_db1`, smoke all five.
