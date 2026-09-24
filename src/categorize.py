from config import HOUSING_SOCIETY_KEYWORD

# Checked in order, first match wins -- specific merchant/loan keywords are
# listed before generic fallbacks like the bare "emi" catch-all so an "EMI
# AMAZON ..." line resolves to Shopping rather than Loan/EMI Payments.
KEYWORD_CATEGORIES = {
    # Groceries (checked before "swiggy" so Instamart doesn't fall under
    # Food & Delivery)
    "instamart": "Groceries",
    "bigbasket": "Groceries",
    "blinkit": "Groceries",
    "zepto": "Groceries",
    "dmart": "Groceries",
    "reliance retail": "Groceries",
    "reliance fresh": "Groceries",
    "gujarat cooperative mil": "Groceries",  # Amul's parent co-op

    # Food delivery
    "swiggy": "Food & Delivery",
    "zomato": "Food & Delivery",
    "bundl technologies": "Food & Delivery",  # Swiggy's legal entity name

    # Dining & restaurants
    "mcdonald": "Dining & Restaurants",
    "kfc": "Dining & Restaurants",
    "burger king": "Dining & Restaurants",
    "subway": "Dining & Restaurants",
    "keventers": "Dining & Restaurants",
    "connaught plaza": "Dining & Restaurants",  # KFC/Pizza Hut corporate name
    "sapphire foods": "Dining & Restaurants",  # KFC/Pizza Hut franchisee
    "haldiram": "Dining & Restaurants",
    "cheetal grand": "Dining & Restaurants",
    "krishna foods": "Dining & Restaurants",
    "irish house": "Dining & Restaurants",
    "qba restaurant": "Dining & Restaurants",
    "nighthouse cafe": "Dining & Restaurants",
    "tonic house": "Dining & Restaurants",
    "mannat haveli": "Dining & Restaurants",
    "madhushala": "Dining & Restaurants",
    "whiskey junction": "Dining & Restaurants",
    "the3aces": "Dining & Restaurants",
    "flying dutchman": "Dining & Restaurants",
    "laidback cafe": "Dining & Restaurants",
    "swagath": "Dining & Restaurants",
    "noida social": "Dining & Restaurants",
    "bottle lab": "Dining & Restaurants",
    "moga daana paani": "Dining & Restaurants",
    "vaango": "Dining & Restaurants",

    # Alcohol
    "liquor": "Alcohol",
    "wine shop": "Alcohol",
    "wine and m": "Alcohol",

    # Fuel
    "fuels": "Fuel",
    "filling": "Fuel",  # covers "filling station" and PDF-layout truncations like "fillin"
    "service stat": "Fuel",
    "petroleum": "Fuel",
    "petrol pump": "Fuel",
    "reliance bp": "Fuel",
    "smart point": "Fuel",
    "shaheed major anurag": "Fuel",  # confirmed: this is a petrol pump

    # Transport
    "uber": "Transport",
    "ola": "Transport",
    "irctc": "Transport",
    "nmrc": "Transport",
    "national highways": "Transport",

    # Vehicle purchase (as opposed to routine running costs like fuel)
    "shiva scooter agency": "Vehicle Purchase",
    "kia motors": "Vehicle Purchase",

    # E-Commerce
    "amazon": "E-Commerce",
    "flipkart": "E-Commerce",

    # Shopping (general retail, apparel, electronics)
    "myntra": "Shopping",
    "zudio": "Shopping",
    "life style internation": "Shopping",
    "aditya birla fashion": "Shopping",
    "adidas": "Shopping",
    "decathlon": "Shopping",

    # Subscriptions
    "netflix": "Subscriptions",
    "spotify": "Subscriptions",
    "hotstar": "Subscriptions",
    "anthropic": "Subscriptions",
    "claude sub": "Subscriptions",

    # Entertainment
    "bookmyshow": "Entertainment",
    "playstation": "Entertainment",
    "google play": "Entertainment",
    "cinepolis": "Entertainment",

    # Health
    "apollo": "Health",
    "pharmacy": "Health",
    "hospital": "Health",
    "medicos": "Health",
    "diagnostics": "Health",
    "1mghealthcare": "Health",

    # Insurance
    "policybazaar": "Insurance",

    # Travel
    "agoda": "Travel",

    # Utilities
    "electricity": "Utilities",
    "airtel": "Utilities",
    "jio": "Utilities",

    # Fees, interest, and other card charges
    "annual fee": "Fees & Charges",
    "joining fee": "Fees & Charges",
    "processing fee": "Fees & Charges",
    "dcc markup": "Fees & Charges",
    "dcc fee": "Fees & Charges",
    "reward redemption": "Fees & Charges",
    "igst": "Fees & Charges",
    "gst": "Fees & Charges",

    # Loan / EMI installments with no identifiable underlying merchant
    "amortization": "Loan/EMI Payments",
    "offus emi": "Loan/EMI Payments",
    "emi principal": "Loan/EMI Payments",
    "emi interest": "Loan/EMI Payments",
    "emi processing fee": "Loan/EMI Payments",
    "instant emi": "Loan/EMI Payments",
    "emi ": "Loan/EMI Payments",  # fallback for any other "EMI <merchant>" line
}

# Set HOUSING_SOCIETY_KEYWORD in .env (e.g. your apartment complex/RWA name)
# to catch its maintenance-fee debits under Housing.
if HOUSING_SOCIETY_KEYWORD:
    KEYWORD_CATEGORIES[HOUSING_SOCIETY_KEYWORD] = "Housing"


def categorize(merchant: str) -> str:
    merchant_lower = merchant.lower()
    for keyword, category in KEYWORD_CATEGORIES.items():
        if keyword in merchant_lower:
            return category
    return "Miscellaneous"
