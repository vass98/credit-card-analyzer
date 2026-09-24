import pandas as pd
import streamlit as st

from db import SessionLocal, Statement, Transaction, init_db
from describe import describe
from style import SLOTS, stat_tile

st.set_page_config(page_title="Current Bills", layout="wide", page_icon="\U0001F9FE")
init_db()

BANK_LABELS = {"hdfc": "HDFC Diners Privilege", "axis": "Axis Flipkart", "icici": "ICICI"}

st.title("Current Bills")
st.caption(
    "Each card's most recently generated statement -- the total due, minimum due, and "
    "due date are the bank's own printed figures, not something computed from transactions."
)

session = SessionLocal()
statement_rows = session.query(Statement).all()
if not statement_rows:
    st.info(
        "No statement summaries found yet. Run `python src/main.py` to fetch and parse "
        "statements (this also backfills bill totals for any statements already downloaded)."
    )
    st.stop()

stmt_df = pd.DataFrame(
    [{"bank": s.bank, "period_start": s.period_start, "period_end": s.period_end, "due_date": s.due_date, "total_due": s.total_due, "min_due": s.min_due} for s in statement_rows]
)
stmt_df["period_end"] = pd.to_datetime(stmt_df["period_end"])
stmt_df["period_start"] = pd.to_datetime(stmt_df["period_start"])
stmt_df["due_date"] = pd.to_datetime(stmt_df["due_date"])

txn_rows = session.query(Transaction).all()
txn_df = pd.DataFrame(
    [{"bank": t.bank, "date": t.date, "merchant": t.merchant, "amount": t.amount, "type": t.type, "category": t.category} for t in txn_rows]
)
txn_df["date"] = pd.to_datetime(txn_df["date"])

# Latest statement per bank = the one with the most recent period_end.
latest = stmt_df.sort_values("period_end").groupby("bank").tail(1).set_index("bank")

# --- Combined summary across all 3 cards ---------------------------------
combined_total_due = latest["total_due"].sum()
combined_min_due = latest["min_due"].sum()
cols = st.columns(3)
with cols[0]:
    stat_tile("Combined total due", f"₹{combined_total_due:,.0f}", SLOTS[0])
with cols[1]:
    stat_tile("Combined minimum due", f"₹{combined_min_due:,.0f}", SLOTS[2])
with cols[2]:
    stat_tile("Cards with a statement", f"{len(latest)} / 3", SLOTS[3])

st.write("")

# --- Per-card breakdown ----------------------------------------------------
for i, bank in enumerate(sorted(latest.index, key=lambda b: latest.loc[b, "period_end"], reverse=True)):
    row = latest.loc[bank]
    st.subheader(BANK_LABELS.get(bank, bank.upper()))
    st.caption(
        f"Billing cycle: {row['period_start'].strftime('%d %b %Y')} → {row['period_end'].strftime('%d %b %Y')}  |  "
        f"Due date: {row['due_date'].strftime('%d %b %Y')}"
    )

    stat_cols = st.columns(2)
    with stat_cols[0]:
        stat_tile("Total amount due", f"₹{row['total_due']:,.0f}", SLOTS[i % len(SLOTS)])
    with stat_cols[1]:
        stat_tile("Minimum amount due", f"₹{row['min_due']:,.0f}", SLOTS[2])

    window = txn_df[
        (txn_df["bank"] == bank) & (txn_df["date"] >= row["period_start"]) & (txn_df["date"] <= row["period_end"])
    ].sort_values("date", ascending=False)

    if window.empty:
        st.info("No individual transactions parsed for this cycle.")
    else:
        display_df = window[["date", "merchant", "category", "type", "amount"]].copy()
        display_df.insert(2, "description", [describe(m, c) for m, c in zip(display_df["merchant"], display_df["category"])])
        display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
        display_df["amount"] = display_df["amount"].round(2)
        display_df = display_df.rename(
            columns={"date": "Date", "merchant": "Merchant", "description": "Description", "category": "Category", "type": "Type", "amount": "Amount"}
        )
        st.dataframe(display_df, width="stretch", hide_index=True)

    st.write("")
