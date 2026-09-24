import re
from datetime import datetime
from pathlib import Path

from parse_statement import extract_tables_try_passwords, extract_text_try_passwords


def _to_iso(date_str: str, sep: str) -> str:
    fmt = f"%d{sep}%m{sep}%Y"
    return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")


# HDFC: explicit Withdrawals/Deposits columns, one of the two is always 0.00.
# "01/06/2026 UPI-JOHN SMITH-... 70,000.00 0.00 6,080.20"
_HDFC_LINE = re.compile(
    r"^(\d{2}/\d{2}/\d{4})\s+(.*?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s*$"
)


def parse_hdfc_account(pdf_path: Path, passwords: list[str]) -> list[dict]:
    text = extract_text_try_passwords(pdf_path, passwords)
    transactions = []
    for line in text.splitlines():
        m = _HDFC_LINE.match(line.strip())
        if not m:
            continue
        date, narration, withdrawal, deposit, balance = m.groups()
        w = float(withdrawal.replace(",", ""))
        d = float(deposit.replace(",", ""))
        transactions.append(
            {
                "date": _to_iso(date, "/"),
                "narration": narration.strip(),
                "amount": w if w > 0 else d,
                "type": "debit" if w > 0 else "credit",
                "balance": float(balance.replace(",", "")),
            }
        )
    return transactions


# ICICI: narration is split across lines before/after the anchor line, which
# holds date + amount + running balance only. Direction (debit/credit) isn't
# marked -- it's inferred from whether the balance rose or fell.
_ICICI_LINE = re.compile(r"^(\d{2}-\d{2}-\d{4})(.*?)\s*([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s*$")
_ICICI_OPENING = re.compile(r"B/F\s+([\d,]+\.\d{2})")


def parse_icici_account(pdf_path: Path, passwords: list[str]) -> list[dict]:
    text = extract_text_try_passwords(pdf_path, passwords)
    opening_match = _ICICI_OPENING.search(text)
    if not opening_match:
        return []
    prev_balance = float(opening_match.group(1).replace(",", ""))

    lines = [l.strip() for l in text.splitlines()]
    transactions = []
    for i, line in enumerate(lines):
        m = _ICICI_LINE.match(line)
        if not m:
            continue
        date, inline_narration, amount, balance = m.groups()
        # The payee name/UPI details for this row are on the 1-2 lines just
        # before the date+amount+balance anchor (a PDF-layout artifact, not
        # an ordering choice) -- collect those rather than only whatever
        # happens to share the anchor's own line, which is often nothing.
        pre_lines = [l for l in lines[max(0, i - 2) : i] if l and not _ICICI_LINE.match(l)]
        narration = " ".join(pre_lines + ([inline_narration.strip()] if inline_narration.strip() else []))
        amount_f = float(amount.replace(",", ""))
        balance_f = float(balance.replace(",", ""))
        transactions.append(
            {
                "date": _to_iso(date, "-"),
                "narration": narration.strip(),
                "amount": amount_f,
                "type": "credit" if balance_f > prev_balance else "debit",
                "balance": balance_f,
            }
        )
        prev_balance = balance_f
    return transactions


# Axis: parsed from the PDF's actual table structure rather than raw text.
# Two statement template eras coexist in the history:
#   older -- ['date', None, narration, withdrawal, deposit, balance, other, None]
#   newer -- ['date', narration, withdrawal, deposit, balance, other]  (often
#            with deposit/balance left blank -- the newer template doesn't
#            always populate a running balance per row)
# Stripping None cells unifies both into the same 6-column shape, so a single
# withdrawal-or-deposit check (not a balance-delta) gives the direction --
# which also means it works even on rows with no balance figure at all.
_AXIS_DATE = re.compile(r"^\d{2}-\d{2}-\d{4}$")


def parse_axis_account(pdf_path: Path, passwords: list[str]) -> list[dict]:
    rows = extract_tables_try_passwords(pdf_path, passwords)
    transactions = []
    for row in rows:
        cells = [c for c in row if c is not None]
        if len(cells) < 5 or not _AXIS_DATE.match((cells[0] or "").strip()):
            continue
        date, narration, withdrawal, deposit = cells[0], cells[1], cells[2], cells[3]
        balance = cells[4] if len(cells) > 4 else ""
        withdrawal, deposit, balance = withdrawal.strip(), deposit.strip(), balance.strip()
        if not withdrawal and not deposit:
            continue
        transactions.append(
            {
                "date": _to_iso(date.strip(), "-"),
                "narration": (narration or "").replace("\n", " ").strip(),
                "amount": float((withdrawal or deposit).replace(",", "")),
                "type": "debit" if withdrawal else "credit",
                "balance": float(balance.replace(",", "")) if balance else None,
            }
        )
    return transactions


ACCOUNT_PARSERS = {
    "hdfc": parse_hdfc_account,
    "icici": parse_icici_account,
    "axis": parse_axis_account,
}
