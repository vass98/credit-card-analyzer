from datetime import datetime

from sqlalchemy.exc import IntegrityError

from bank_parsers import PARSERS
from categorize import categorize
from config import BANKS
from db import SessionLocal, Statement, Transaction, init_db
from fetch_statements import fetch_all_statements
from parse_statement import extract_text
from statement_summary import SUMMARY_PARSERS


def run():
    init_db()
    statements_by_bank = fetch_all_statements()
    session = SessionLocal()

    added, skipped = 0, 0
    statements_added, statements_skipped = 0, 0
    for bank, pdf_paths in statements_by_bank.items():
        password = BANKS[bank]["password"]
        for pdf_path in pdf_paths:
            print(f"Parsing {pdf_path.name} ...")
            try:
                text = extract_text(pdf_path, password)
            except Exception as e:
                print(f"  skipped ({e})")
                continue
            transactions = PARSERS[bank](text)

            for txn in transactions:
                record = Transaction(
                    bank=bank,
                    date=datetime.strptime(txn["date"], "%Y-%m-%d").date(),
                    merchant=txn["merchant"],
                    amount=float(txn["amount"]),
                    type=txn["type"],
                    category=categorize(txn["merchant"]),
                )
                session.add(record)
                try:
                    session.commit()
                    added += 1
                except IntegrityError:
                    session.rollback()
                    skipped += 1

            summary = SUMMARY_PARSERS[bank](text)
            if summary:
                session.add(Statement(bank=bank, **summary))
                try:
                    session.commit()
                    statements_added += 1
                except IntegrityError:
                    session.rollback()
                    statements_skipped += 1

    print(f"Done. Added {added} new transactions, skipped {skipped} duplicates.")
    print(f"Statements: added {statements_added}, skipped {statements_skipped} duplicates.")


if __name__ == "__main__":
    run()
