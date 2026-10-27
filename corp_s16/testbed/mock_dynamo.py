"""Mock rows for the two DynamoDB tables the API reads.

    python3 mock_dynamo.py <env> [--dry-run] [--keep-old] [--random N] [--seed S]

<env> picks the tables (dev, uat, ...). By default every row whose
src_stm_id is MOCK is deleted first (the old S12 stand-ins and earlier runs
of this script); rows from anyone else are never touched. Then the fixed
cases below are written, plus N random citizens with --random.

Run where boto3 has credentials for the target account (CloudShell: as is;
elsewhere: AWS_PROFILE and AWS_REGION set). --dry-run reads only.
"""
import argparse
import random
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr

LIST_TABLE = "rdx<env>_tbl1"
DTL_TABLE = "rdx<env>_tbl2"
MARK = "MOCK"
LOAD_TS = "2026-10-27T00:00:00"
DATA_DT = "2026-10-27"

# citizenId, accountId, subtype, ownerType, accountOwner, what it covers, overrides
CASES = [
    ("9990000000001", "9990000001", "SAVING", "INDIVIDUAL", "SINGLE", "happy path: TH + EN name and branch", {}),
    ("9990000000001", "9990000002", "CURRENT", "INDIVIDUAL", "SINGLE", "no EN name or branch (TH fallback), negative ledger, credit limit, no available",
     {"en": False, "ledger": "-2500.00", "available": None, "credit": "50000.00"}),
    ("9990000000001", "9990000003", "SAVING", "INDIVIDUAL", "JOINT", "JOINT: filtered out everywhere", {}),
    ("9990000000001", "9990000004", "TERM", "INDIVIDUAL", "SINGLE", "third subtype for one citizen", {"ledger": "100000.00"}),
    ("9990000000001", "9990000005", "SAVING", "INDIVIDUAL", "SINGLE", "status not ACTIVE (the app does not filter on status)", {"status": "INACTIVE"}),
    ("9990000000002", "9990000006", "SAVING", "JURISTIC", "SINGLE", "JURISTIC: filtered out everywhere", {}),
    ("9990000000002", "9990000007", "TERM", "INDIVIDUAL", "SINGLE", "second citizen: must not leak into the first", {}),
    ("9990000000003", "9990000008", "SAVING", "INDIVIDUAL", "JOINT", "citizen with no eligible account: empty list", {}),
    ("9990000000004", "9990000009", "SAVING", "INDIVIDUAL", "SINGLE", "several accounts of one subtype (1 of 3)", {}),
    ("9990000000004", "9990000010", "SAVING", "INDIVIDUAL", "SINGLE", "several accounts of one subtype (2 of 3), zero balance", {"ledger": "0.00", "available": "0.00"}),
    ("9990000000004", "9990000011", "SAVING", "INDIVIDUAL", "SINGLE", "several accounts of one subtype (3 of 3), largest DECIMAL(18,2)",
     {"ledger": "9999999999999999.99", "available": "9999999999999999.99"}),
    (None, "9990000012", "CURRENT", "INDIVIDUAL", "SINGLE", "detail only, in no citizen's list", {}),
]

SUBTYPES = ["SAVING"] * 6 + ["CURRENT"] * 3 + ["TERM"]
OWNERS = [("INDIVIDUAL", "SINGLE")] * 8 + [("INDIVIDUAL", "JOINT"), ("JURISTIC", "SINGLE")]
BRANCHES = [("สาขาสีลม", "Silom Branch"), ("สาขาสาทร", "Sathorn Branch"), ("สาขาบางนา", "Bangna Branch")]


def items(citizen, account, subtype, owner_type, owner, opts, rng):
    """One list row (None when citizen is None) and one detail row for one account."""
    en = opts.get("en", True)
    branch, branch_en = BRANCHES[int(account) % len(BRANCHES)]
    common = {
        "institutionName": "MOCK BANK",
        "accountId": account,
        "accountSubType": subtype,
        "accountStatus": opts.get("status", "ACTIVE"),
        "accountName": f"ทดสอบ {account}",
        "ownerType": owner_type,
        "accountOwner": owner,
        "src_stm_id": MARK,
        "load_ts": LOAD_TS,
        "data_dt": DATA_DT,
    }
    if en:
        common["accountNameEn"] = f"TEST {account}"

    ledger = opts.get("ledger", f"{rng.uniform(0, 500000):.2f}")
    available = opts.get("available", ledger)
    detail = {
        **common,
        "accountType": "DEPOSIT",
        "openingDate": f"20{rng.randint(15, 25)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}T00:00:00",
        "homeBranch": branch,
        "lastLedgerBalanceAmount": Decimal(ledger),  # N; boto3 refuses float
        "lastLedgerBalanceCurrency": "THB",
    }
    if en:
        detail["homeBranchEn"] = branch_en
    if available is not None:
        detail["lastAvailableBalanceAmount"] = Decimal(available)
        detail["lastAvailableBalanceCurrency"] = "THB"
    if opts.get("credit"):
        detail["creditLimit"] = Decimal(opts["credit"])

    row = None
    if citizen:
        row = {**common, "citizenId": citizen, "accountKey": f"{subtype}#{account}"}
    return row, detail


def random_cases(n, rng):
    out, acct = [], 9990000100
    for i in range(n):
        citizen = f"99900000{1000 + i:05d}"
        for _ in range(rng.randint(1, 3)):
            owner_type, owner = rng.choice(OWNERS)
            out.append((citizen, str(acct), rng.choice(SUBTYPES), owner_type, owner, "random", {}))
            acct += 1
    return out


def delete_mock(table, keys, dry):
    """Delete every row marked MOCK; returns (deleted, kept)."""
    scan = {"FilterExpression": Attr("src_stm_id").eq(MARK), "ProjectionExpression": ", ".join(keys)}
    marked = []
    while True:
        page = table.scan(**scan)
        marked += page["Items"]
        if "LastEvaluatedKey" not in page:
            break
        scan["ExclusiveStartKey"] = page["LastEvaluatedKey"]
    total = table.scan(Select="COUNT")["Count"]  # first page only; enough for these small tables
    if not dry:
        with table.batch_writer() as batch:
            for key in marked:
                batch.delete_item(Key=key)
    return len(marked), total - len(marked)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("env")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--keep-old", action="store_true", help="do not delete the MOCK rows first")
    ap.add_argument("--random", type=int, default=0, help="extra random citizens")
    ap.add_argument("--seed", type=int, default=27)
    args = ap.parse_args()

    db = boto3.resource("dynamodb")
    acct = boto3.client("sts").get_caller_identity()["Account"]
    list_t = db.Table(LIST_TABLE.replace("<env>", args.env))
    dtl_t = db.Table(DTL_TABLE.replace("<env>", args.env))
    mode = "DRY RUN, nothing written" if args.dry_run else "WRITING"
    print(f"account ...{acct[-4:]}  region {db.meta.client.meta.region_name}  {mode}")
    print(f"tables {list_t.name}, {dtl_t.name}")

    if not args.keep_old:
        for t, keys in ((list_t, ["citizenId", "accountKey"]), (dtl_t, ["accountId", "accountSubType"])):
            gone, kept = delete_mock(t, keys, args.dry_run)
            print(f"  {t.name}: delete {gone} MOCK rows, keep {kept} other rows")

    rng = random.Random(args.seed)
    cases = CASES + random_cases(args.random, rng)
    rows = [items(c, a, s, ot, o, opts, rng) + (why,) for c, a, s, ot, o, why, opts in cases]
    if not args.dry_run:
        with list_t.batch_writer() as lb, dtl_t.batch_writer() as db_:
            for row, detail, _ in rows:
                if row:
                    lb.put_item(Item=row)
                db_.put_item(Item=detail)
    print(f"  put {sum(1 for r, _, _ in rows if r)} list rows, {len(rows)} detail rows\n")

    print(f"{'citizenId':<14} {'accountId':<11} {'subtype':<8} {'owner':<20} covers")
    for (row, d, why) in rows:
        cid = row["citizenId"] if row else "-"
        print(f"{cid:<14} {d['accountId']:<11} {d['accountSubType']:<8} {d['ownerType'] + '/' + d['accountOwner']:<20} {why}")


if __name__ == "__main__":
    main()
