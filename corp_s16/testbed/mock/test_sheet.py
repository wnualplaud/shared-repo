"""Test case workbook for the client, from accounts.json (the mock loaded in UAT, APP_ENV=uatmock).

    python3 mock/test_sheet.py [-o test_cases.xlsx]

Three sheets:
  accounts      one row per account      /rdx_ep1, /rdx_ep2, /rdx_ep3
  transactions  one row per transaction  /rdx_ep4, /rdx_ep5 (the statement
                header's account columns repeated on every row)
  test cases    one row per case: request body, expected status and result

Column order on the data sheets: system (id, test case), source (src_stm_id,
data_dt), the columns in the WHERE, the columns with logic, then the rest in
the API's order; load_ts last. NULL marks a value the store does not have.
Every cell is text, so long ids and amounts keep their digits. Reads no AWS;
needs openpyxl (pip install openpyxl).
"""
import argparse
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

HERE = Path(__file__).resolve().parent
API_SUBTYPE = {"SAVING": "SAVINGS", "CURRENT": "CURRENT", "TERM": "TERM"}  # the store's -> the API's
RANGE = ("2026-10-01T00:00:00+07:00", "2026-10-26T23:59:59+07:00")         # the default date range

# (group, columns); the group colours the header
ACCOUNT_COLUMNS = [
    ("system", ["id", "test case", "visibleInApi"]),
    ("source", ["src_stm_id", "data_dt"]),
    ("where", ["citizenId", "accountId", "accountSubType", "ownerType", "accountOwner", "accountStatus"]),
    ("logic", ["accountName", "accountNameEn", "homeBranch", "homeBranchEn",
               "lastLedgerBalanceAmount", "lastAvailableBalanceAmount", "creditLimit", "openingDate"]),
    ("rest", ["institutionName", "accountType", "lastLedgerBalanceCurrency", "lastAvailableBalanceCurrency",
              "identifier"]),
    ("system", ["load_ts"]),
]
TRANSACTION_COLUMNS = [
    ("system", ["id", "test case"]),
    ("source", ["src_stm_id", "data_dt"]),
    ("where", ["accountId", "accountSubType", "bookingDateTime", "ownerType", "accountOwner", "accountStatus"]),
    ("logic", ["amount", "balance", "valueDateTime", "openingDate", "accountLevelMaturityDate",
               "accountName", "accountNameEn", "homeBranch", "homeBranchEn", "merchantName", "merchantNameEn"]),
    ("rest", [  # statement header, then entry, in the API's order
        "institutionName", "accountType", "lastLedgerBalanceAmount", "lastLedgerBalanceCurrency",
        "lastAvailableBalanceAmount", "lastAvailableBalanceCurrency", "creditLimit",
        "subAccountLevelMaturityDate", "domainCode", "familyCode", "subFamilyCode",
        "proprietaryBankTransactionCode", "proprietaryBankTransactionDescription", "creditDebitIndicator",
        "amountCurrency", "balanceCurrency", "processingBranchCode", "processingBranchDescription",
        "originCode", "originDescription", "transactionId", "transactionRef", "transactionInformation",
        "creditorAccountId", "creditorAccountName", "receivingInstitutionCode", "receivingInstitutionName",
        "debtorAccountId", "debtorAccountName", "sendingInstitutionCode", "sendingInstitutionName"]),
    ("system", ["load_ts"]),
]
CASE_COLUMNS = ["id", "endpoint", "test case", "request body", "expected status", "expected result",
                "data rows", "note / to confirm"]
FILL = {"system": "D9D9D9", "source": "E2EFDA", "where": "DDEBF7", "logic": "FFF2CC", "rest": "FFFFFF"}


# ---------- data ----------
def load(path):
    accounts, transactions = [], []
    for citizen in json.loads(path.read_text(encoding="utf-8")):
        for acc in citizen["accounts"]:
            a = {k: v for k, v in acc.items() if k not in ("transactions", "_note", "accountKey")}
            a.update(citizenId=citizen["citizenId"], identifier="",
                     accountSubType=API_SUBTYPE.get(acc["accountSubType"], acc["accountSubType"]),
                     **{"test case": acc.get("_note", "")})
            a["visibleInApi"] = "Y" if (a["ownerType"], a["accountOwner"], a["accountStatus"]) == (
                "INDIVIDUAL", "SINGLE", "ACTIVE") else "N"
            a["id"] = f"ACC{len(accounts) + 1:02d}"
            accounts.append(a)
            for txn in acc.get("transactions", []):
                t = {**a, **{k: v for k, v in txn.items() if k != "_note"}}  # header repeated, entry over it
                t["test case"] = txn.get("_note", "")
                t["id"] = f"TXN{len(transactions) + 1:02d}"
                transactions.append(t)
    return accounts, transactions


def visible(a):
    return a["visibleInApi"] == "Y"


def by_account(accounts, account_id):
    return next(a for a in accounts if a["accountId"] == account_id)


def in_range(transactions, account_id, start, end):
    # times are all +07:00 text, so string order is time order
    return [t for t in transactions if t["accountId"] == account_id and start <= t["bookingDateTime"] <= end]


# ---------- cases ----------
def body(**kw):
    kw.setdefault("language", "TH")
    kw.setdefault("auxiliaryReferenceId", "TC")
    return kw


def cases(accounts, transactions):
    out = []

    def add(cid, endpoint, note, req, status, result, rows="", ask=""):
        out.append([cid, endpoint, note, json.dumps(req, ensure_ascii=False), str(status), result, rows, ask])

    def ids(rows):
        return ", ".join(r["id"] for r in rows)

    # /rdx_ep1
    def listed(citizen, sub):
        return [a for a in accounts if a["citizenId"] == citizen and visible(a)
                and (sub == "ALL" or a["accountSubType"] == sub)]

    def list_case(cid, note, citizen, sub, language="TH", ask=""):
        rows = listed(citizen, sub)
        req = body(citizenId=citizen, accountSubType=sub, language=language)
        if rows:
            add(cid, "/rdx_ep1", note, req, 200,
                f"{len(rows)} accounts: " + ", ".join(r["accountId"] for r in rows), ids(rows), ask)
        else:
            add(cid, "/rdx_ep1", note, req, 404, "No accounts found", "", ask)

    list_case("L01", "SAVINGS ของ citizen ที่มีหลายบัญชี: บัญชีร่วม (JOINT) ไม่แสดง", "1234567890001", "SAVINGS")
    list_case("L02", "ภาษา EN: accountName เป็นชื่อ EN", "1234567890001", "SAVINGS", "EN")
    list_case("L03", "CURRENT ภาษา EN แต่บัญชีไม่มีชื่อ EN: ได้ชื่อ TH แทน", "1234567890001", "CURRENT", "EN")
    list_case("L04", "ALL: ทุก subtype ของ citizen (SAVINGS, CURRENT, TERM)", "1234567890001", "ALL")
    list_case("L05", "citizen คนที่สอง: นิติบุคคล (JURISTIC) ไม่แสดง, ไม่มีบัญชีของ citizen อื่นปน",
              "1234567890002", "ALL")
    list_case("L06", "citizen ที่มีแต่บัญชีร่วม: ไม่มีบัญชีให้แสดง", "1234567890003", "SAVINGS")
    list_case("L07", "citizen ที่มี SAVINGS 3 บัญชี", "1234567890004", "SAVINGS")
    list_case("L08", "citizen ที่ไม่มีในระบบ", "0000000000000", "SAVINGS")
    add("L09", "/rdx_ep1", "language ที่ไม่รองรับ",
        body(citizenId="1234567890001", accountSubType="SAVINGS", language="JP"), 400,
        "Unsupported language")
    add("L10", "/rdx_ep1", "ไม่ส่ง accountSubType (field บังคับ)",
        {"citizenId": "1234567890001", "language": "TH", "auxiliaryReferenceId": "TC"}, 400,
        "reject (ยังไม่รองรับ: ตอนนี้ได้ 500)")

    # /rdx_ep2
    def account_case(cid, note, account_id, sub, language="TH", ask=""):
        a = by_account(accounts, account_id)
        req = body(accountId=account_id, accountSubType=sub, language=language)
        if visible(a) and a["accountSubType"] == sub:
            name = a["accountNameEn"] if language == "EN" and a["accountNameEn"] else a["accountName"]
            branch = a["homeBranchEn"] if language == "EN" and a["homeBranchEn"] else a["homeBranch"]
            add(cid, "/rdx_ep2", note, req, 200, f"accountName {name}; homeBranch {branch}", a["id"], ask)
        else:
            add(cid, "/rdx_ep2", note, req, 404, "Account not found", a["id"], ask)

    account_case("A01", "บัญชีปกติ ภาษา TH", "1234567001", "SAVINGS")
    account_case("A02", "บัญชีปกติ ภาษา EN", "1234567001", "SAVINGS", "EN")
    account_case("A03", "ไม่มีชื่อ/สาขา EN: ได้ TH แทน", "1234567002", "CURRENT", "EN")
    account_case("A04", "บัญชี TERM", "1234567004", "TERM")
    account_case("A05", "บัญชีร่วม (JOINT)", "1234567003", "SAVINGS")
    account_case("A06", "นิติบุคคล (JURISTIC)", "1234567006", "SAVINGS")
    account_case("A07", "subtype ไม่ตรงกับบัญชี", "1234567001", "CURRENT")
    add("A08", "/rdx_ep2", "accountId ที่ไม่มีในระบบ", body(accountId="0000000000", accountSubType="SAVINGS"),
        404, "Account not found")

    # /rdx_ep3
    def balance_case(cid, note, account_id, sub, ask=""):
        a = by_account(accounts, account_id)
        req = body(accountId=account_id, accountSubType=sub)
        if visible(a):
            amt = lambda v: v if v is not None else "0.00"
            add(cid, "/rdx_ep3", note, req, 200,
                f"ledger {amt(a['lastLedgerBalanceAmount'])}; available {amt(a['lastAvailableBalanceAmount'])}; "
                f"creditLimit {amt(a['creditLimit'])} (ทศนิยม 2 ตำแหน่งเสมอ)", a["id"], ask)
        else:
            add(cid, "/rdx_ep3", note, req, 404, "Account not found", a["id"], ask)

    balance_case("B01", "ยอดปกติ", "1234567001", "SAVINGS")
    balance_case("B02", "ยอด ledger ติดลบ, มีวงเงิน, ไม่มียอด available", "1234567002", "CURRENT",
                 "ข้อ 75: available / creditLimit ที่ไม่มีค่า ส่ง 0.00 (ตอนนี้) หรือ null?")
    balance_case("B03", "ยอด 0", "1234567010", "SAVINGS")
    balance_case("B04", "ยอดสูงสุดของ DECIMAL(18,2): ตัวเลขต้องครบทุกหลัก ไม่ปัด", "1234567011", "SAVINGS")
    balance_case("B05", "บัญชีร่วม (JOINT)", "1234567003", "SAVINGS")

    # /rdx_ep4 and /rdx_ep5
    def txn_case(cid, endpoint, note, account_id, sub, start=RANGE[0], end=RANGE[1], language="TH", ask=""):
        a = by_account(accounts, account_id)
        rows = in_range(transactions, account_id, start, end) if visible(a) else []
        req = body(accountId=account_id, accountSubType=sub, language=language,
                   fromBookingDateTime=start, toBookingDateTime=end)
        if rows:
            extra = (f"; header: {a['accountName'] if language == 'TH' else a['accountNameEn'] or a['accountName']},"
                     f" numberofTotalItems {len(rows)}") if endpoint == "/rdx_ep5" else ""
            add(cid, endpoint, note, req, 200,
                f"{len(rows)} entries: " + ", ".join(r["transactionId"] for r in rows) + extra, ids(rows), ask)
        else:
            add(cid, endpoint, note, req, 404, "No transactions found" if visible(a) else "Account not found",
                a["id"], ask)

    txn_case("T01", "/rdx_ep4", "หลายรายการในช่วง: จำนวนเงินทศนิยม 2 ตำแหน่ง, เวลาเป็น +07:00", "1234567001", "SAVINGS")
    txn_case("T02", "/rdx_ep4", "รายการ 00:10 น. เวลาไทย: ต้องอยู่ในวันที่ 5 ไม่ใช่วันที่ 4",
             "1234567001", "SAVINGS", "2026-10-05T00:00:00+07:00", "2026-10-05T23:59:59+07:00")
    txn_case("T03", "/rdx_ep4", "รายการหลังวันสิ้นสุดช่วง (27 ต.ค.) ไม่รวม", "1234567009", "SAVINGS")
    txn_case("T04", "/rdx_ep4", "รายการ 00:00 น. พอดี ที่ต้นช่วง", "1234567007", "TERM",
             "2026-10-15T00:00:00+07:00", "2026-10-15T23:59:59+07:00")
    txn_case("T05", "/rdx_ep4", "บัญชี TERM ที่ไม่มีรายการ", "1234567004", "TERM")
    txn_case("T06", "/rdx_ep4", "ช่วงที่ไม่มีรายการ", "1234567001", "SAVINGS",
             "2026-09-01T00:00:00+07:00", "2026-09-15T23:59:59+07:00")
    txn_case("T07", "/rdx_ep4", "บัญชีร่วม (JOINT) แม้มีรายการ", "1234567003", "SAVINGS")
    add("T08", "/rdx_ep4", "ไม่ส่งช่วงวันที่ (field บังคับ)", body(accountId="1234567001", accountSubType="SAVINGS"),
        400, "reject (ยังไม่รองรับ: ตอนนี้ได้ 500)")

    s_ask = ("ข้อ 79: statementId เราสร้างเป็น UUID ต่อ request; ข้อ 80: creationDateTime = เวลาที่ API ตอบ "
             "(+07:00). ถูกต้องไหม?")
    txn_case("S01", "/rdx_ep5", "statement ปกติ: header + entries, startDateTime/endDateTime = ช่วงที่ส่ง",
             "1234567001", "SAVINGS", ask=s_ask)
    txn_case("S02", "/rdx_ep5", "ภาษา EN: ชื่อบัญชีและสาขาใน header เป็น EN", "1234567001", "SAVINGS", language="EN")
    txn_case("S03", "/rdx_ep5", "CURRENT: ยอด ledger ติดลบ, creditLimit ใน header", "1234567002", "CURRENT",
             ask="ข้อ 75 เหมือน B02")
    txn_case("S04", "/rdx_ep5", "TERM ที่มีรายการ: accountLevelMaturityDate ใน header", "1234567007", "TERM")
    txn_case("S05", "/rdx_ep5", "บัญชีที่ไม่มีรายการในช่วง", "1234567004", "TERM")
    txn_case("S06", "/rdx_ep5", "บัญชีร่วม (JOINT)", "1234567003", "SAVINGS")
    return out


# ---------- workbook ----------
def write_sheet(ws, groups, rows):
    columns = [c for _, cols in groups for c in cols]
    ws.append(columns)
    col = 1
    for group, cols in groups:
        for _ in cols:
            cell = ws.cell(row=1, column=col)
            cell.font = Font(bold=True)
            cell.fill = PatternFill("solid", fgColor=FILL[group])
            col += 1
    null_font = Font(italic=True, color="808080")
    for r in rows:
        ws.append(["NULL" if r.get(c, "") is None else str(r.get(c, "")) for c in columns])
        for cell in ws[ws.max_row]:
            cell.number_format = "@"
            if cell.value == "NULL":
                cell.font = null_font
    for i, c in enumerate(columns, 1):
        width = max(len(c), *(len(str(ws.cell(row=n, column=i).value or "")) for n in range(2, ws.max_row + 1)))
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = min(width + 2, 60)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("-o", "--out", default="test_cases.xlsx")
    p.add_argument("--accounts", default=str(HERE / "accounts.json"))
    args = p.parse_args()

    accounts, transactions = load(Path(args.accounts))
    wb = Workbook()
    ws = wb.active
    ws.title = "test cases"
    write_sheet(ws, [("system", CASE_COLUMNS)], [dict(zip(CASE_COLUMNS, c)) for c in cases(accounts, transactions)])
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "D2"
    for title, groups, rows, freeze in [("accounts", ACCOUNT_COLUMNS, accounts, "D2"),
                                        ("transactions", TRANSACTION_COLUMNS, transactions, "C2")]:
        ws = wb.create_sheet(title)
        write_sheet(ws, groups, rows)
        ws.freeze_panes = freeze
    wb.save(args.out)
    print(f"{args.out}: {len(accounts)} accounts, {len(transactions)} transactions, "
          f"{wb['test cases'].max_row - 1} test cases")


if __name__ == "__main__":
    main()
