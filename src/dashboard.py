import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from db import SessionLocal, Transaction, init_db
from describe import describe
from style import GRID, INK_MUTED, INK_PRIMARY, INK_SECONDARY, OTHER_GRAY, SLOTS, STATUS, SURFACE, category_tag, insight_card, stat_tile, style_chart

st.set_page_config(page_title="Credit Card Insights", layout="wide", page_icon="\U0001F4B3")
init_db()

session = SessionLocal()
rows = session.query(Transaction).filter(Transaction.type == "debit").all()
df = pd.DataFrame(
    [{"bank": r.bank, "date": r.date, "merchant": r.merchant, "amount": r.amount, "category": r.category} for r in rows]
)

st.title("Credit Card Spending Insights")

if df.empty:
    st.info("No transactions yet. Run `python src/main.py` first to fetch and parse statements.")
    st.stop()

df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.to_period("M").astype(str)

date_from, date_to = df["date"].min(), df["date"].max()
st.caption(f"Showing data from **{date_from.strftime('%d %b %Y')}** to **{date_to.strftime('%d %b %Y')}**")

# Fixed category -> color mapping, assigned by overall spend rank so it stays
# stable across every chart on the page. Categories past the 8 palette slots
# fold into a shared "Other" gray (never a generated/cycled hue).
category_totals = df.groupby("category")["amount"].sum().sort_values(ascending=False)
top_categories = list(category_totals.index[:8])
category_color = {cat: SLOTS[i] for i, cat in enumerate(top_categories)}


def color_for(cat: str) -> str:
    return category_color.get(cat, OTHER_GRAY)


# --- Stat tiles -------------------------------------------------------
total_spend = df["amount"].sum()
txn_count = len(df)
avg_txn = df["amount"].mean()
top_cat_name, top_cat_amount = category_totals.index[0], category_totals.iloc[0]

tile_colors = [SLOTS[0], SLOTS[2], SLOTS[3], SLOTS[6]]
tiles = [
    ("Total spend", f"₹{total_spend:,.0f}"),
    ("Transactions", f"{txn_count:,}"),
    ("Avg transaction", f"₹{avg_txn:,.0f}"),
    ("Top category", f"{top_cat_name}"),
]
cols = st.columns(4)
for col, (label, value), accent in zip(cols, tiles, tile_colors):
    with col:
        stat_tile(label, value, accent)

st.write("")

# --- Spend by category (single series -> one consistent hue; axis carries
# category identity, so per-bar rainbow coloring would be decorative noise) --
st.subheader("Spend by category")
cat_df = category_totals.reset_index()
cat_df.columns = ["category", "amount"]
cat_df = cat_df.sort_values("amount", ascending=True)

fig_cat = go.Figure(
    go.Bar(
        x=cat_df["amount"],
        y=cat_df["category"],
        orientation="h",
        marker=dict(color=SLOTS[0], line=dict(width=0)),
        text=[f"₹{v:,.0f}" for v in cat_df["amount"]],
        textposition="outside",
        textfont=dict(color=INK_SECONDARY),
        hovertemplate="%{y}: ₹%{x:,.0f}<extra></extra>",
    )
)
fig_cat.update_layout(showlegend=False, bargap=0.35)
fig_cat = style_chart(fig_cat, height=560)
fig_cat.update_xaxes(title=None)
fig_cat.update_yaxes(title=None)
st.plotly_chart(fig_cat, width='stretch')

# --- Monthly trend, split by category (top 8 + Other) ------------------
st.subheader("Monthly trend by category")
df["color_category"] = df["category"].where(df["category"].isin(top_categories), "Other")
trend = df.groupby(["month", "color_category"])["amount"].sum().reset_index()
months = sorted(trend["month"].unique())

series_order = top_categories + (["Other"] if "Other" in trend["color_category"].unique() else [])
fig_trend = go.Figure()
for cat in series_order:
    sub = trend[trend["color_category"] == cat].set_index("month")["amount"].reindex(months, fill_value=0)
    fig_trend.add_trace(
        go.Bar(
            x=months,
            y=sub,
            name=cat,
            marker=dict(color=color_for(cat) if cat != "Other" else OTHER_GRAY),
            hovertemplate=f"{cat}" + " (%{x}): ₹%{y:,.0f}<extra></extra>",
        )
    )
fig_trend.update_layout(barmode="stack")
fig_trend = style_chart(fig_trend, height=420)
st.plotly_chart(fig_trend, width='stretch')

# --- Total spend by year (single series, chronological order -> one
# consistent hue, not per-bar rainbow) -----------------------------------
st.subheader("Total spend by year")
df["year"] = df["date"].dt.year
year_totals = df.groupby("year")["amount"].sum().sort_index()

fig_year = go.Figure(
    go.Bar(
        x=[str(y) for y in year_totals.index],
        y=year_totals.values,
        marker=dict(color=SLOTS[0], line=dict(width=0)),
        text=[f"₹{v:,.0f}" for v in year_totals.values],
        textposition="outside",
        textfont=dict(color=INK_SECONDARY),
        hovertemplate="%{x}: ₹%{y:,.0f}<extra></extra>",
    )
)
fig_year.update_layout(showlegend=False, bargap=0.35)
fig_year = style_chart(fig_year, height=380)
fig_year.update_xaxes(title=None)
fig_year.update_yaxes(title=None)
st.plotly_chart(fig_year, width='stretch')

# --- Top merchants ------------------------------------------------------
st.subheader("Top merchants")

# Bank statements print the same brand under many different merchant strings
# (payment gateway prefixes, city suffixes, legal entity names, ...). Group
# them under one display name so "Top merchants" reflects the real brand.
MERCHANT_GROUPS = {
    "flipkart": "Flipkart",
    "swiggy": "Swiggy",
}


def display_merchant(merchant: str) -> str:
    m = merchant.lower()
    for keyword, label in MERCHANT_GROUPS.items():
        if keyword in m:
            return label
    return merchant


df["merchant_display"] = df["merchant"].apply(display_merchant)
top_merch = (
    df.groupby(["merchant_display", "category"])["amount"]
    .sum()
    .sort_values(ascending=False)
    .head(20)
    .reset_index()
    .rename(columns={"merchant_display": "merchant"})
)


top_merch_display = top_merch.copy()
top_merch_display["category"] = top_merch_display["category"].apply(lambda c: category_tag(c, color_for(c)))
top_merch_display["amount"] = top_merch_display["amount"].apply(lambda v: f"₹{v:,.0f}")
top_merch_display = top_merch_display.rename(columns={"merchant": "Merchant", "category": "Category", "amount": "Amount"})
st.write(top_merch_display[["Merchant", "Category", "Amount"]].to_html(escape=False, index=False), unsafe_allow_html=True)

st.write("")

# --- By card (donut -- 3 segments, clean part-to-whole) -----------------
st.subheader("By card")
bank_totals = df.groupby("bank")["amount"].sum().sort_values(ascending=False)
bank_labels = [b.upper() for b in bank_totals.index]
fig_bank = go.Figure(
    go.Pie(
        labels=bank_labels,
        values=bank_totals.values,
        hole=0.55,
        marker=dict(colors=SLOTS[: len(bank_totals)], line=dict(color=SURFACE, width=2)),
        textinfo="label+percent",
        textfont=dict(color=INK_PRIMARY),
        hovertemplate="%{label}: ₹%{value:,.0f}<extra></extra>",
    )
)
fig_bank = style_chart(fig_bank, height=380)
fig_bank.update_layout(legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05))
st.plotly_chart(fig_bank, width='stretch')

# --- All transactions -----------------------------------------------------
st.subheader("All transactions")
all_txns = df.sort_values("date", ascending=False)[["date", "bank", "merchant", "category", "amount"]].copy()
all_txns.insert(3, "description", [describe(m, c) for m, c in zip(all_txns["merchant"], all_txns["category"])])
all_txns["date"] = all_txns["date"].dt.strftime("%Y-%m-%d")
all_txns["amount"] = all_txns["amount"].round(2)
st.dataframe(all_txns, width='stretch', hide_index=True)

# --- Smart insights: patterns mined from the actual data, not category
# totals restated as advice. Each card below was checked against the real
# numbers before being written -- see the numbers themselves for the "why".
st.write("")
st.subheader("Smart insights")
st.caption("Patterns mined from your transaction history -- not generic advice.")

df["year"] = df["date"].dt.year
current_month = df["month"].max()  # likely partial -- excluded from monthly averages below

# 1. Year-over-year trend in ROUTINE spend -- one-off big-ticket purchases
# (a scooter, a car booking) are excluded so this reflects habitual card
# use, not lumpy one-time events. The current (likely partial) month is
# also excluded so it doesn't drag the latest year's average down unfairly.
recurring = df[df["category"] != "Vehicle Purchase"]
recurring_full = recurring[recurring["month"] != current_month]
if not recurring_full.empty:
    yearly_avg = recurring_full.groupby("year").apply(lambda g: g["amount"].sum() / g["month"].nunique(), include_groups=False)
    if len(yearly_avg) >= 2:
        latest_year, prev_year = yearly_avg.index[-1], yearly_avg.index[-2]
        latest_val, prev_val = yearly_avg.iloc[-1], yearly_avg.iloc[-2]
        pct = (latest_val - prev_val) / prev_val * 100 if prev_val else 0
        trend_str = "  ".join(f"{y}: ₹{v:,.0f}/mo" for y, v in yearly_avg.items())
        insight_card(
            STATUS["critical"] if pct > 20 else (STATUS["good"] if pct < 0 else STATUS["warning"]),
            f"Routine monthly spend is {'up' if pct >= 0 else 'down'} {abs(pct):.0f}% vs {prev_year}",
            f"Excluding one-off purchases (vehicle bookings etc.), your average monthly spend by year: {trend_str}. "
            f"{latest_year} is running at ₹{latest_val:,.0f}/month"
            + (", the highest of any year here -- worth knowing before it becomes the new normal." if latest_val == yearly_avg.max() else "."),
        )

# 2. Food delivery -- check whether it's a new habit, how weekend orders
# compare to weekday ones, and how much bleeds out in sub-₹300 orders.
fd = df[df["category"] == "Food & Delivery"].copy()
if not fd.empty:
    latest_fd_year = fd["year"].max()
    latest_total = fd[fd["year"] == latest_fd_year]["amount"].sum()
    latest_count = len(fd[fd["year"] == latest_fd_year])
    prior_total = fd[fd["year"] < latest_fd_year]["amount"].sum()
    full_months_latest = df[(df["year"] == latest_fd_year) & (df["month"] != current_month)]["month"].nunique() or 1
    run_rate = latest_total / full_months_latest

    fd["is_weekend"] = fd["date"].dt.dayofweek >= 5
    weekend_avg = fd.loc[fd["is_weekend"], "amount"].mean()
    weekday_avg = fd.loc[~fd["is_weekend"], "amount"].mean()
    small = fd[fd["amount"] < 300]

    if prior_total == 0:
        opener = f"This category didn't exist before {latest_fd_year} -- ₹0 in earlier years, now ₹{latest_total:,.0f} ({latest_count} orders)."
    else:
        opener = f"₹{latest_total:,.0f} in {latest_fd_year} across {latest_count} orders (₹{prior_total:,.0f} in prior years)."

    weekend_ratio = f"{weekend_avg / weekday_avg:.1f}x" if weekday_avg else "n/a"
    insight_card(
        STATUS["serious"],
        f"Food delivery is running at ₹{run_rate:,.0f}/month",
        f"{opener} Weekend orders average ₹{weekend_avg:,.0f} vs ₹{weekday_avg:,.0f} on weekdays "
        f"({weekend_ratio} bigger). {len(small)} orders were under ₹300, totaling ₹{small['amount'].sum():,.0f} -- "
        "batching those into fewer, larger orders cuts the delivery/platform fee paid per meal.",
    )

# 3. Whichever single *discretionary* category is the most consistent
# year-over-year spend driver -- essentials (fuel, utilities, health,
# insurance, housing) are excluded since "spend less on fuel" isn't
# actionable the way "spend less on shopping" is.
ESSENTIAL_CATEGORIES = ["Fuel", "Utilities", "Health", "Insurance", "Housing", "Vehicle Purchase", "Loan/EMI Payments", "Groceries"]
recurring_cats = df[~df["category"].isin(ESSENTIAL_CATEGORIES)]
years_span = sorted(recurring_cats["year"].unique())
if len(years_span) >= 2:
    by_year_cat = recurring_cats.groupby(["category", "year"])["amount"].sum().unstack(fill_value=0)
    recent_years = years_span[-3:] if len(years_span) >= 3 else years_span
    consistency = by_year_cat[recent_years].min(axis=1)  # the floor across recent years
    top_consistent = consistency.sort_values(ascending=False).index[0]
    if consistency[top_consistent] > 0:
        per_year = ", ".join(f"{y}: ₹{by_year_cat.loc[top_consistent, y]:,.0f}" for y in recent_years)
        insight_card(
            STATUS["warning"],
            f"{top_consistent} is your most consistent recurring cost",
            f"It shows up every year without fail: {per_year}. Total across all data: "
            f"₹{category_totals.get(top_consistent, 0):,.0f}. Because it's steady rather than a one-off, "
            "small percentage cuts here compound more than one-time savings elsewhere.",
        )

# 4. EMI: how expensive is the credit actually, and is more being financed
# over time (easy to lose track of total spend when it's spread out).
loan_df = df[df["category"] == "Loan/EMI Payments"]
if not loan_df.empty:
    is_interest = loan_df["merchant"].str.lower().str.contains("interest")
    interest_total = loan_df[is_interest]["amount"].sum()
    principal_total = loan_df[~is_interest]["amount"].sum()
    markup_pct = interest_total / principal_total * 100 if principal_total else 0
    loan_by_year = loan_df.groupby("year")["amount"].sum()
    if len(loan_by_year) >= 2:
        yoy = "  ".join(f"{y}: ₹{v:,.0f}" for y, v in loan_by_year.items())
        insight_card(
            STATUS["good"] if markup_pct < 3 else STATUS["warning"],
            f"EMI credit itself is cheap ({markup_pct:.1f}% markup) -- but you're financing more each year",
            f"Only ₹{interest_total:,.0f} in interest on ₹{principal_total:,.0f} financed, so the EMI conversions "
            f"aren't costing much extra. But the amount financed has grown: {yoy}. Spreading purchases into "
            "installments makes each one feel smaller, which can hide how much total spend is actually growing "
            "(see the trend above).",
        )

# 5. Fees & charges -- flagged for completeness, but sized honestly.
fees_total = category_totals.get("Fees & Charges", 0.0)
if fees_total > 50:
    insight_card(
        STATUS["good"] if fees_total < total_spend * 0.01 else STATUS["warning"],
        f"₹{fees_total:,.0f} in card fees & charges",
        "GST on charges, processing fees, and finance charges. "
        + (
            "This is a small fraction of your total spend -- not where your money is actually going."
            if fees_total < total_spend * 0.01
            else "Worth checking your statements for late-payment or interest charges specifically -- those are the avoidable part."
        ),
    )
