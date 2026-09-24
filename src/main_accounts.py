from datetime import datetime

from sqlalchemy.exc import IntegrityError

from account_parsers import ACCOUNT_PARSERS
from categorize_account import categorize_account
from config import BANK_ACCOUNTS
from db import AccountTransaction, SessionLocal, init_db
from fetch_statements import fetch_all_account_statements


def run():
    init_db()
    statements_by_bank = fetch_all_account_statements()
    session = SessionLocal()

    added, skipped = 0, 0
    for bank, pdf_paths in statements_by_bank.items():
        passwords = BANK_ACCOUNTS[bank]["passwords"]
        for pdf_path in pdf_paths:
            print(f"Parsing {pdf_path.name} ...")
            try:
                transactions = ACCOUNT_PARSERS[bank](pdf_path, passwords)
            except Exception as e:
                print(f"  skipped ({e})")
                continue

            for txn in transactions:
                record = AccountTransaction(
                    bank=bank,
                    date=datetime.strptime(txn["date"], "%Y-%m-%d").date(),
                    narration=txn["narration"],
                    amount=float(txn["amount"]),
                    type=txn["type"],
                    category=categorize_account(txn["narration"]),
                    balance=txn.get("balance"),
                )
                session.add(record)
                try:
                    session.commit()
                    added += 1
                except IntegrityError:
                    session.rollback()
                    skipped += 1

    print(f"Done. Added {added} new account transactions, skipped {skipped} duplicates.")


if __name__ == "__main__":
    run()
