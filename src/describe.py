import re

from config import HOUSING_SOCIETY_KEYWORD

# A short, human-readable "what is this transaction" phrase for transaction
# tables. Checked in order: specific merchant keywords first (more useful
# than the category alone), then a generic per-category fallback.
CATEGORY_DESCRIPTIONS = {
    "Groceries": "Grocery shopping",
    "Food & Delivery": "Food delivery",
    "Dining & Restaurants": "Restaurant meal",
    "Alcohol": "Alcohol purchase",
    "Fuel": "Fuel refill",
    "Transport": "Transport fare",
    "Vehicle Purchase": "Vehicle purchase",
    "E-Commerce": "Online shopping",
    "Shopping": "Retail shopping",
    "Subscriptions": "Subscription payment",
    "Entertainment": "Entertainment spend",
    "Health": "Health expense",
    "Insurance": "Insurance payment",
    "Travel": "Travel booking",
    "Housing": "Housing maintenance",
    "Utilities": "Utility bill",
    "Fees & Charges": "Card fee",
    "Loan/EMI Payments": "EMI installment",
    "Miscellaneous": "Card purchase",
}

MERCHANT_DESCRIPTIONS = {
    # Checked first: reward payouts often name several brands in passing
    # ("CASHBACK CREDIT JUL26-FLIPKART:283~UBER_PVR_SWI") -- without this,
    # those would misleadingly match as a purchase at whichever brand
    # happens to appear in the string.
    "cashback": "Cashback credit",
    "swiggy": "Food delivery order",
    "zomato": "Food delivery order",
    "instamart": "Grocery delivery",
    "amazon": "Amazon purchase",
    "flipkart": "Flipkart purchase",
    "myntra": "Fashion shopping",
    "zudio": "Clothing purchase",
    "adidas": "Clothing purchase",
    "decathlon": "Sports gear",
    "netflix": "Video streaming",
    "hotstar": "Video streaming",
    "spotify": "Music streaming",
    "anthropic": "AI subscription",
    "claude sub": "AI subscription",
    "bookmyshow": "Movie ticket",
    "playstation": "Gaming purchase",
    "google play": "App/game purchase",
    "cinepolis": "Movie ticket",
    "policybazaar": "Insurance purchase",
    "agoda": "Hotel booking",
    "mcdonald": "Fast food meal",
    "kfc": "Fast food meal",
    "burger king": "Fast food meal",
    "subway": "Fast food meal",
    "kia motors": "Car booking",
    "shiva scooter agency": "Bike purchase",
    "electricity": "Electricity bill",
    "airtel": "Mobile/DTH bill",
    "jio": "Mobile/internet bill",
    "annual fee": "Annual card fee",
    "joining fee": "Card joining fee",
    "dcc": "Currency conversion fee",
    "processing fee": "Processing fee",
    "amortization": "EMI installment",
    "offus emi": "EMI installment",
    "instant emi": "EMI conversion",
    "gst": "GST charge",
    "igst": "GST charge",
    "medicos": "Pharmacy purchase",
    "diagnostics": "Diagnostic test",
    "hospital": "Hospital expense",
}

if HOUSING_SOCIETY_KEYWORD:
    MERCHANT_DESCRIPTIONS[HOUSING_SOCIETY_KEYWORD] = "Society maintenance"


# Short acronym-like keywords are prone to false-positive substring matches
# inside merged/space-stripped merchant names (e.g. "gst" inside "fillinGSTation"
# from "FILLING"+"STATION" run together). These require word boundaries;
# longer brand-name keywords use plain substring matching, since merchant
# strings routinely merge words with no space at all ("SWIGGYBENGALURU",
# "RELIANCEJIO") and a boundary requirement would miss those.
_STRICT_KEYWORDS = {"gst", "igst", "dcc"}


def describe(merchant: str, category: str) -> str:
    merchant_lower = merchant.lower()
    for keyword, phrase in MERCHANT_DESCRIPTIONS.items():
        if keyword in _STRICT_KEYWORDS:
            if re.search(r"\b" + re.escape(keyword) + r"\b", merchant_lower):
                return phrase
        elif keyword in merchant_lower:
            return phrase
    return CATEGORY_DESCRIPTIONS.get(category, "Card purchase")
