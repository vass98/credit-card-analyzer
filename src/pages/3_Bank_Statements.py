import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from db import AccountTransaction, SessionLocal, init_db
from style import GRID, INK_MUTED, INK_PRIMARY, INK_SECONDARY, SLOTS, SURFACE, stat_tile, style_chart

st.set_page_config(page_title="Bank Statements", layout="wide", page_icon="\U0001F3E6")
init_db()

st.title("Bank Statements")
st.caption("Savings/current account activity -- separate from credit card spend shown on the other pages.")

BANK_LABELS = {"hdfc": "HDFC Savings", "icici": "ICICI Savings", "axis": "Axis Savings (closed)"}
# Income-side categories don't belong in an "expense" breakdown, and Self
# Transfer is money moving between the user's own accounts -- neither
# inflates real spend nor real income.
INCOME_CATEGORIES = {"Salary", "Interest Credited"}
NON_EXPENSE_CATEGORIES = INCOME_CATEGORIES | {"Self Transfer"}

session = SessionLocal()
rows = session.query(AccountTransaction).all()
df = pd.DataFrame(
    [{"bank": r.bank, "date": r.date, "narration": r.narration, "amount": r.amount, "type": r.type, "category": r.category, "balance": r.balance} for r in rows]
)

if df.empty:
    st.info("No account statements parsed yet. Run `python src/main_accounts.py` first.")
    st.stop()

df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.to_period("M").astype(str)

available_banks = [b for b in ["hdfc", "icici", "axis"] if b in df["bank"].unique()]
selected_bank = st.selectbox("Which account?", available_banks, format_func=lambda b: BANK_LABELS.get(b, b.upper()))

bank_df = df[df["bank"] == selected_bank].sort_values("date").copy()
is_closed = selected_bank == "axis"
last_date = bank_df["date"].max()

if is_closed:
    st.warning(f"This account was closed. Last statement activity: {last_date.strftime('%d %b %Y')}.")

# --- Stat tiles -------------------------------------------------------
balance_rows = bank_df[bank_df["balance"].notna()]
latest_balance = balance_rows.iloc[-1]["balance"] if not balance_rows.empty else None

expense_df = bank_df[(bank_df["type"] == "debit") & (~bank_df["category"].isin(NON_EXPENSE_CATEGORIES))]
# Income includes Salary/Interest Credited -- only Self Transfer (money
# moving between the user's own accounts, not real external income) is
# excluded here.
income_df = bank_df[(bank_df["type"] == "credit") & (bank_df["category"] != "Self Transfer")]
self_transfer_df = bank_df[bank_df["category"] == "Self Transfer"]

tiles = [
    ("Latest known balance" if not is_closed else "Balance at closure", f"₹{latest_balance:,.0f}" if latest_balance is not None else "n/a"),
    ("Total income (excl. transfers)", f"₹{income_df['amount'].sum():,.0f}"),
    ("Total expense (excl. transfers)", f"₹{expense_df['amount'].sum():,.0f}"),
    ("Self-transfers (in/out of own accounts)", f"₹{self_transfer_df['amount'].sum():,.0f}"),
]
cols = st.columns(4)
for col, (label, value), accent in zip(cols, tiles, [SLOTS[0], SLOTS[2], SLOTS[7], SLOTS[3]]):
    with col:
        stat_tile(label, value, accent)

st.write("")

# --- Balance over time (only points where a balance was actually printed) --
if not balance_rows.empty:
    st.subheader("Balance over time")
    fig_bal = go.Figure(
        go.Scatter(
            x=balance_rows["date"],
            y=balance_rows["balance"],
            mode="lines",
            line=dict(color=SLOTS[0], width=2),
            hovertemplate="%{x|%d %b %Y}: ₹%{y:,.0f}<extra></extra>",
        )
    )
    fig_bal = style_chart(fig_bal, height=340)
    st.plotly_chart(fig_bal, width="stretch")

# --- Monthly income vs expense -------------------------------------------
st.subheader("Monthly income vs expense")
monthly_income = income_df.groupby("month")["amount"].sum()
monthly_expense = expense_df.groupby("month")["amount"].sum()
months = sorted(set(monthly_income.index) | set(monthly_expense.index))

fig_ie = go.Figure()
fig_ie.add_trace(
    go.Bar(
        x=months,
        y=[monthly_income.get(m, 0) for m in months],
        name="Income",
        marker=dict(color=SLOTS[2]),
        hovertemplate="Income (%{x}): ₹%{y:,.0f}<extra></extra>",
    )
)
fig_ie.add_trace(
    go.Bar(
        x=months,
        y=[monthly_expense.get(m, 0) for m in months],
        name="Expense",
        marker=dict(color=SLOTS[7]),
        hovertemplate="Expense (%{x}): ₹%{y:,.0f}<extra></extra>",
    )
)
fig_ie.update_layout(barmode="group")
fig_ie = style_chart(fig_ie, height=380)
st.plotly_chart(fig_ie, width="stretch")

# --- Spend by category (expense side only) ---------------------------------
st.subheader("Spend by category")
if expense_df.empty:
    st.info("No expense transactions in this account.")
else:
    cat_totals = expense_df.groupby("category")["amount"].sum().sort_values(ascending=True)
    fig_cat = go.Figure(
        go.Bar(
            x=cat_totals.values,
            y=cat_totals.index,
            orientation="h",
            marker=dict(color=SLOTS[0], line=dict(width=0)),
            text=[f"₹{v:,.0f}" for v in cat_totals.values],
            textposition="outside",
            textfont=dict(color=INK_SECONDARY),
            hovertemplate="%{y}: ₹%{x:,.0f}<extra></extra>",
        )
    )
    fig_cat.update_layout(showlegend=False, bargap=0.35)
    fig_cat = style_chart(fig_cat, height=min(520, 120 + 40 * len(cat_totals)))
    fig_cat.update_xaxes(title=None)
    fig_cat.update_yaxes(title=None)
    st.plotly_chart(fig_cat, width="stretch")

# --- Transactions -----------------------------------------------------
st.subheader("Transactions")
txns_display = bank_df.sort_values("date", ascending=False)[["date", "narration", "category", "type", "amount", "balance"]].copy()
txns_display["date"] = txns_display["date"].dt.strftime("%Y-%m-%d")
txns_display["amount"] = txns_display["amount"].round(2)
txns_display["balance"] = txns_display["balance"].apply(lambda v: f"₹{v:,.0f}" if pd.notna(v) else "--")
txns_display = txns_display.rename(
    columns={"date": "Date", "narration": "Narration", "category": "Category", "type": "Type", "amount": "Amount", "balance": "Balance"}
)
st.dataframe(txns_display, width="stretch", hide_index=True)
