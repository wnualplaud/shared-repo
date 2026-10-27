"""Mock rows for the two DynamoDB tables the API reads.

    python3 mock_dynamo.py <env> [--dry-run] [--keep-old] [--institution NAME] [--random N] [--seed S]

<env> picks the tables (dev, uat, ...). By default every row whose
src_stm_id is MOCK is deleted first (the old S12 stand-ins and earlier runs
of this script); rows from anyone else are never touched. Then the fixed
cases below are written, plus N random citizens with --random.

Run where boto3 has credentials for the target account (CloudShell: as is;
elsewhere: AWS_PROFILE and AWS_DEFAULT_REGION set). --dry-run reads only.
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


def cid(n):
    """citizenId, 13 digits: 123456789 + 4-digit number."""
    return f"123456789{n:04d}"


def acc(n):
    """accountId, 10 digits: 1234567 + 3-digit number."""
    return f"1234567{n:03d}"


# citizenId, accountId, subtype, ownerType, accountOwner, note (Thai, shown to testers), overrides
CASES = [
    (cid(1), acc(1), "SAVING", "INDIVIDUAL", "SINGLE", "บัญชีปกติ: มีชื่อและสาขาทั้ง TH และ EN", {}),
    (cid(1), acc(2), "CURRENT", "INDIVIDUAL", "SINGLE", "ไม่มีชื่อและสาขา EN (ขอ EN จะได้ TH แทน), ยอด ledger ติดลบ, มีวงเงิน, ไม่มียอด available",
     {"en": False, "ledger": "-2500.00", "available": None, "credit": "50000.00"}),
    (cid(1), acc(3), "SAVING", "INDIVIDUAL", "JOINT", "บัญชีร่วม (JOINT): API ไม่แสดง, ไม่อยู่ใน list, ยิงตรงได้ 404", {}),
    (cid(1), acc(4), "TERM", "INDIVIDUAL", "SINGLE", "บัญชี TERM ของ citizen เดียวกัน", {"ledger": "100000.00"}),
    (cid(1), acc(5), "SAVING", "INDIVIDUAL", "SINGLE", "SAVING บัญชีที่สองของ citizen เดียวกัน: list SAVING ได้ 2 บัญชี", {}),
    (cid(2), acc(6), "SAVING", "JURISTIC", "SINGLE", "นิติบุคคล (JURISTIC): API ไม่แสดง, ไม่อยู่ใน list, ยิงตรงได้ 404", {}),
    (cid(2), acc(7), "TERM", "INDIVIDUAL", "SINGLE", "citizen คนที่สอง: ต้องไม่เห็นบัญชีของ citizen คนแรกปนมา", {}),
    (cid(3), acc(8), "SAVING", "INDIVIDUAL", "JOINT", "citizen ที่มีแต่บัญชีร่วม: list ได้ว่าง (200)", {}),
    (cid(4), acc(9), "SAVING", "INDIVIDUAL", "SINGLE", "SAVING หลายบัญชีของ citizen เดียว (1/3)", {}),
    (cid(4), acc(10), "SAVING", "INDIVIDUAL", "SINGLE", "SAVING หลายบัญชีของ citizen เดียว (2/3), ยอด 0", {"ledger": "0.00", "available": "0.00"}),
    (cid(4), acc(11), "SAVING", "INDIVIDUAL", "SINGLE", "SAVING หลายบัญชีของ citizen เดียว (3/3), ยอดสูงสุดของ DECIMAL(18,2)",
     {"ledger": "9999999999999999.99", "available": "9999999999999999.99"}),
]

SUBTYPES = ["SAVING"] * 6 + ["CURRENT"] * 3 + ["TERM"]
OWNERS = [("INDIVIDUAL", "SINGLE")] * 8 + [("INDIVIDUAL", "JOINT"), ("JURISTIC", "SINGLE")]
BRANCHES = [("สาขาสีลม", "Silom Branch"), ("สาขาสาทร", "Sathorn Branch"), ("สาขาบางนา", "Bangna Branch")]


def items(citizen, account, subtype, owner_type, owner, opts, institution, rng):
    """One list row and one detail row for one account."""
    en = opts.get("en", True)
    branch, branch_en = BRANCHES[int(account) % len(BRANCHES)]
    common = {
        "institutionName": institution,
        "accountId": account,
        "accountSubType": subtype,
        "accountStatus": "ACTIVE",  # the mart writes ACTIVE only
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

    row = {**common, "citizenId": citizen, "accountKey": f"{subtype}#{account}"}
    return row, detail


def random_cases(n, rng):
    out, a = [], 101
    for i in range(n):
        citizen = cid(1001 + i)
        for _ in range(rng.randint(1, 3)):
            owner_type, owner = rng.choice(OWNERS)
            out.append((citizen, acc(a), rng.choice(SUBTYPES), owner_type, owner, "สุ่ม", {}))
            a += 1
    return out


def build(institution, n_random, seed):
    """(list row, detail row, note) per account; the same arguments give the same rows."""
    rng = random.Random(seed)
    cases = CASES + random_cases(n_random, rng)
    return [items(c, a, s, ot, o, opts, institution, rng) + (note,) for c, a, s, ot, o, note, opts in cases]


def add_common_args(ap):
    ap.add_argument("--institution", default="MOCK BANK", help="institutionName on every row")
    ap.add_argument("--random", type=int, default=0, help="extra random citizens")
    ap.add_argument("--seed", type=int, default=27)


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
    add_common_args(ap)
    args = ap.parse_args()

    db = boto3.resource("dynamodb")
    account = boto3.client("sts").get_caller_identity()["Account"]
    list_t = db.Table(LIST_TABLE.replace("<env>", args.env))
    dtl_t = db.Table(DTL_TABLE.replace("<env>", args.env))
    mode = "DRY RUN, nothing written" if args.dry_run else "WRITING"
    print(f"account ...{account[-4:]}  region {db.meta.client.meta.region_name}  {mode}")
    print(f"tables {list_t.name}, {dtl_t.name}")

    if not args.keep_old:
        for t, keys in ((list_t, ["citizenId", "accountKey"]), (dtl_t, ["accountId", "accountSubType"])):
            gone, kept = delete_mock(t, keys, args.dry_run)
            print(f"  {t.name}: delete {gone} MOCK rows, keep {kept} other rows")

    rows = build(args.institution, args.random, args.seed)
    if not args.dry_run:
        with list_t.batch_writer() as lb, dtl_t.batch_writer() as db_:
            for row, detail, _ in rows:
                lb.put_item(Item=row)
                db_.put_item(Item=detail)
    print(f"  put {len(rows)} list rows, {len(rows)} detail rows, institutionName {args.institution!r}\n")

    print(f"{'citizenId':<14} {'accountId':<11} {'subtype':<8} {'owner':<20} note")
    for row, d, note in rows:
        print(f"{row['citizenId']:<14} {d['accountId']:<11} {d['accountSubType']:<8} {d['ownerType'] + '/' + d['accountOwner']:<20} {note}")


if __name__ == "__main__":
    main()
