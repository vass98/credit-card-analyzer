import re
from datetime import datetime

# A tolerant prefix absorbs stray text that PDF extraction sometimes merges
# onto a transaction row (e.g. pie-chart percentage labels like "66% ").
_JUNK_PREFIX = r"^(?:.*?\s)?"

# HDFC: "15/02/2026| 18:20 WHISKEY JUNCTION GAUTAM BUDDH C 1,050.00 l"
# A "+" directly before the amount marks a credit (payment/refund); its
# absence marks a debit (purchase). Reward-point deltas like "+ 152" can
# appear mid-description and are not the direction marker.
_HDFC_LINE = re.compile(
    _JUNK_PREFIX
    + r"(\d{2}/\d{2}/\d{4})\|\s*\d{2}:\d{2}\s+(.*?)\s*([+-]?)\s*C\s*([\d,]+\.\d{2})\s*l\s*$"
)

# ICICI: "21/08/2022 6510445708 SOME STORE ANYTOWN IN 28 1,377.21"
# columns: date, serial no, description, reward points, amount, optional CR
_ICICI_LINE = re.compile(
    _JUNK_PREFIX
    + r"(\d{2}/\d{2}/\d{4})\s+\d+\s+(.*?)\s+\S+\s+([\d,]+\.\d{2})(?:\s+(CR))?\s*$"
)

# Axis: "14/01/2026 PYU*SWIGGY FOOD,BANGALORE FOOD PRODUCTS 250.00 Dr 10.00 Cr"
# columns: date, description, amount, Dr/Cr, cashback amount, Dr/Cr
_AXIS_LINE = re.compile(
    _JUNK_PREFIX
    + r"(\d{2}/\d{2}/\d{4})\s+(.*?)\s+([\d,]+\.\d{2})\s+(Dr|Cr)\s+[\d,]+\.\d{2}\s+(?:Dr|Cr)\s*$"
)


def _ddmmyyyy_to_iso(date_str: str) -> str:
    return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")


def parse_hdfc(text: str) -> list[dict]:
    transactions = []
    for line in text.splitlines():
        m = _HDFC_LINE.match(line.strip())
        if not m:
            continue
        date, description, sign, amount = m.groups()
        transactions.append(
            {
                "date": _ddmmyyyy_to_iso(date),
                "merchant": description.strip() or "Unknown",
                "amount": float(amount.replace(",", "")),
                "type": "credit" if sign == "+" else "debit",
            }
        )
    return transactions


def parse_icici(text: str) -> list[dict]:
    # Everything from here on is an "active EMI / loan" recap table, not the
    # transaction ledger -- its rows (e.g. "Merchant EMI 28/12/2023 28/02/2024
    # 3 4,359.00 2 2,983.79 1,491.89") coincidentally match the transaction
    # line shape and would otherwise be parsed as bogus transactions.
    text = text.split("EMI / PERSONAL LOAN ON CREDIT CARDS")[0]

    transactions = []
    for line in text.splitlines():
        m = _ICICI_LINE.match(line.strip())
        if not m:
            continue
        date, description, amount, cr = m.groups()
        transactions.append(
            {
                "date": _ddmmyyyy_to_iso(date),
                "merchant": description.strip() or "Unknown",
                "amount": float(amount.replace(",", "")),
                "type": "credit" if cr == "CR" else "debit",
            }
        )
    return transactions


def parse_axis(text: str) -> list[dict]:
    transactions = []
    for line in text.splitlines():
        m = _AXIS_LINE.match(line.strip())
        if not m:
            continue
        date, description, amount, direction = m.groups()
        transactions.append(
            {
                "date": _ddmmyyyy_to_iso(date),
                "merchant": description.strip() or "Unknown",
                "amount": float(amount.replace(",", "")),
                "type": "credit" if direction == "Cr" else "debit",
            }
        )
    return transactions


PARSERS = {
    "hdfc": parse_hdfc,
    "icici": parse_icici,
    "axis": parse_axis,
}
