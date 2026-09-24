from pathlib import Path

import pdfplumber
import pikepdf


def extract_text(pdf_path: Path, password: str) -> str:
    """Unlock a password-protected statement PDF and return its raw text."""
    unlocked_path = pdf_path.with_suffix(".unlocked.pdf")

    with pikepdf.open(pdf_path, password=password) as pdf:
        pdf.save(unlocked_path)

    try:
        with pdfplumber.open(unlocked_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    finally:
        unlocked_path.unlink(missing_ok=True)

    return text


def extract_tables(pdf_path: Path, password: str) -> list[list]:
    """Unlock a PDF and return every table row across all pages, as pdfplumber
    finds them -- used where raw-text extraction can't be trusted to keep
    columns (e.g. amount vs. balance) apart."""
    unlocked_path = pdf_path.with_suffix(".unlocked.pdf")

    with pikepdf.open(pdf_path, password=password) as pdf:
        pdf.save(unlocked_path)

    try:
        rows = []
        with pdfplumber.open(unlocked_path) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables():
                    rows.extend(table)
    finally:
        unlocked_path.unlink(missing_ok=True)

    return rows


def extract_tables_try_passwords(pdf_path: Path, passwords: list[str]) -> list[list]:
    last_error = None
    for password in passwords:
        if not password:
            continue
        try:
            return extract_tables(pdf_path, password)
        except pikepdf.PasswordError as e:
            last_error = e
    raise last_error or pikepdf.PasswordError(f"no usable password for {pdf_path}")


def extract_text_try_passwords(pdf_path: Path, passwords: list[str]) -> str:
    """Try each password in order (e.g. a bank that changed its statement
    password partway through the history) -- raises the last error if none
    of them unlock the file."""
    last_error = None
    for password in passwords:
        if not password:
            continue
        try:
            return extract_text(pdf_path, password)
        except pikepdf.PasswordError as e:
            last_error = e
    raise last_error or pikepdf.PasswordError(f"no usable password for {pdf_path}")
