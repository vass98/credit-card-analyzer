import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

CREDENTIALS_DIR = ROOT / "credentials"
DATA_DIR = ROOT / "data"
STATEMENTS_DIR = DATA_DIR / "statements"
ACCOUNT_STATEMENTS_DIR = DATA_DIR / "account_statements"
DB_PATH = DATA_DIR / "transactions.sqlite3"

GMAIL_CLIENT_SECRET_FILE = CREDENTIALS_DIR / "credentials.json"
GMAIL_TOKEN_FILE = CREDENTIALS_DIR / "token.json"
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ACCOUNT_HOLDER_NAME = os.environ.get("ACCOUNT_HOLDER_NAME", "").strip().lower()
HOUSING_SOCIETY_KEYWORD = os.environ.get("HOUSING_SOCIETY_KEYWORD", "").strip().lower()

# One entry per card. "query" is a Gmail search filter, "password" unlocks
# the statement PDF for that bank.
BANKS = {
    "hdfc": {
        "query": 'from:Emailstatements.cards@hdfcbank.bank.in has:attachment filename:pdf',
        "password": os.environ.get("HDFC_PDF_PASSWORD", ""),
    },
    "icici": {
        "query": '(from:credit_cards@icici.bank.in OR from:credit_cards@icicibank.com) has:attachment filename:pdf',
        "password": os.environ.get("ICICI_PDF_PASSWORD", ""),
    },
    "axis": {
        "query": 'from:cc.statements@axis.bank.in has:attachment filename:pdf',
        "password": os.environ.get("AXIS_PDF_PASSWORD", ""),
    },
}

# Savings/current account statements (not credit cards) -- subject line is
# matched on its static prefix since the month/date range is dynamic.
# "passwords" is a list tried in order (HDFC changed theirs partway through
# the statement history, so both the new and old one are listed).
BANK_ACCOUNTS = {
    "hdfc": {
        "query": 'subject:"HDFC Bank Combined Email Statement" has:attachment filename:pdf',
        "passwords": [
            os.environ.get("HDFC_ACCOUNT_PDF_PASSWORD", ""),
            os.environ.get("HDFC_ACCOUNT_PDF_PASSWORD_OLD", ""),
        ],
    },
    "icici": {
        "query": 'subject:"ICICI Bank Statement" has:attachment filename:pdf',
        "passwords": [os.environ.get("ICICI_ACCOUNT_PDF_PASSWORD", "")],
    },
    "axis": {
        "query": 'subject:"AXIS BANK : Statement" has:attachment filename:pdf',
        "passwords": [os.environ.get("AXIS_ACCOUNT_PDF_PASSWORD", "")],
    },
}
