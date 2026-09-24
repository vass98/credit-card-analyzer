import re
from datetime import datetime


def _parse_amount(s: str) -> float:
    return float(s.replace(",", ""))


def _parse_date(s: str, fmt: str) -> "datetime.date":
    return datetime.strptime(s, fmt).date()


def hdfc_summary(text: str) -> dict | None:
    period = re.search(r"Billing Period (\d{1,2} \w+, \d{4}) - (\d{1,2} \w+, \d{4})", text)
    total_due = re.search(r"RECEIVED \(Current Billing Cycle\)\s*\n_\s*C([\d,]+\.\d{2})", text)
    min_due = re.search(r"MINIMUM DUE DUE DATE\s*\nC([\d,]+\.\d{2}) (\d{1,2} \w+, \d{4})", text)
    if not (period and total_due and min_due):
        return None
    return {
        "period_start": _parse_date(period.group(1), "%d %b, %Y"),
        "period_end": _parse_date(period.group(2), "%d %b, %Y"),
        "total_due": _parse_amount(total_due.group(1)),
        "min_due": _parse_amount(min_due.group(1)),
        "due_date": _parse_date(min_due.group(2), "%d %b, %Y"),
    }


def icici_summary(text: str) -> dict | None:
    period = re.search(r"Statement period\s*:\s*(\w+ \d{1,2}, \d{4}) to (\w+ \d{1,2}, \d{4})", text)
    due_date = re.search(r"PAYMENT DUE DATE\s*\n(\w+ \d{1,2}, \d{4})", text)
    total_due = re.search(r"Total Amount due\s*\n`([\d,]+\.\d{2})", text)
    min_due = re.search(r"Minimum Amount due.*\n`([\d,]+\.\d{2})", text)
    if not (period and due_date and total_due and min_due):
        return None
    return {
        "period_start": _parse_date(period.group(1), "%B %d, %Y"),
        "period_end": _parse_date(period.group(2), "%B %d, %Y"),
        "total_due": _parse_amount(total_due.group(1)),
        "min_due": _parse_amount(min_due.group(1)),
        "due_date": _parse_date(due_date.group(1), "%B %d, %Y"),
    }


def axis_summary(text: str) -> dict | None:
    m = re.search(
        r"([\d,]+\.\d{2}) Dr ([\d,]+\.\d{2}) Dr (\d{2}/\d{2}/\d{4}) - (\d{2}/\d{2}/\d{4}) (\d{2}/\d{2}/\d{4}) \d{2}/\d{2}/\d{4}",
        text,
    )
    if not m:
        return None
    total_due, min_due, period_start, period_end, due_date = m.groups()
    return {
        "period_start": _parse_date(period_start, "%d/%m/%Y"),
        "period_end": _parse_date(period_end, "%d/%m/%Y"),
        "total_due": _parse_amount(total_due),
        "min_due": _parse_amount(min_due),
        "due_date": _parse_date(due_date, "%d/%m/%Y"),
    }


SUMMARY_PARSERS = {
    "hdfc": hdfc_summary,
    "icici": icici_summary,
    "axis": axis_summary,
}
