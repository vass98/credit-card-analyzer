# Set in .env -- narrations mentioning the account holder's own name (partial
# match, e.g. "JOHN SMIT" for "JOHN SMITH") indicate a transfer between the
# user's own accounts at different banks, not a payment to someone else.
from config import ACCOUNT_HOLDER_NAME as OWN_NAME

# Checked in order, first match wins.
ACCOUNT_KEYWORD_CATEGORIES = {
    "salary": "Salary",
    "interest paid": "Interest Credited",
    "interest credited": "Interest Credited",
    "cc billpay": "Credit Card Bill Payment",
    "cred club": "Credit Card Bill Payment",
    "cred ccbp": "Credit Card Bill Payment",
    "cash wdl": "ATM Withdrawal",
    "atm": "ATM Withdrawal",
    "indmoney": "Investment",
    "zerodha": "Investment",
    "groww": "Investment",
    "google play": "Entertainment",
    "playstore": "Entertainment",
    "blinkit": "Groceries",
    "bigbasket": "Groceries",
    "zepto": "Groceries",
    "swiggy": "Food & Delivery",
    "zomato": "Food & Delivery",
    "kfc": "Dining & Restaurants",
    "burger king": "Dining & Restaurants",
    "mcdonald": "Dining & Restaurants",
    "hotel": "Dining & Restaurants",
    "kebab": "Dining & Restaurants",
    "amazon": "E-Commerce",
    "blue dart": "E-Commerce",
    "flipkart": "E-Commerce",
    "airtel": "Utilities",
    "jio": "Utilities",
    "electricity": "Utilities",
    "/monthl/": "Rent/Recurring Payment",
}


def categorize_account(narration: str) -> str:
    n = narration.lower()
    if OWN_NAME and OWN_NAME in n:
        return "Self Transfer"
    for keyword, category in ACCOUNT_KEYWORD_CATEGORIES.items():
        if keyword in n:
            return category
    if "upi" in n or "neft" in n or "imps" in n or "rtgs" in n:
        return "Personal Transfer"
    return "Miscellaneous"
