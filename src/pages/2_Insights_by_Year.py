import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from db import SessionLocal, Transaction, init_db
from describe import describe
from style import GRID, INK_MUTED, INK_PRIMARY, INK_SECONDARY, OTHER_GRAY, SLOTS, STATUS, SURFACE, category_tag, insight_card, stat_tile, style_chart

st.set_page_config(page_title="Insights by Year", layout="wide", page_icon="\U0001F4C5")
init_db()

st.title("Insights by Year")

session = SessionLocal()
rows = session.query(Transaction).filter(Transaction.type == "debit").all()
df = pd.DataFrame(
    [{"bank": r.bank, "date": r.date, "merchant": r.merchant, "amount": r.amount, "category": r.category} for r in rows]
)

if df.empty:
    st.info("No transactions yet. Run `python src/main.py` first to fetch and parse statements.")
    st.stop()

df["date"] = pd.to_datetime(df["date"])
df["year"] = df["date"].dt.year
df["month_num"] = df["date"].dt.month

MERCHANT_GROUPS = {"flipkart": "Flipkart", "swiggy": "Swiggy"}


def display_merchant(merchant: str) -> str:
    m = merchant.lower()
    for keyword, label in MERCHANT_GROUPS.items():
        if keyword in m:
            return label
    return merchant


df["merchant_display"] = df["merchant"].apply(display_merchant)

available_years = sorted(df["year"].unique(), reverse=True)
selected_year = st.selectbox("Which year do you want insights for?", available_years, index=0)

year_df = df[df["year"] == selected_year].copy()
prior_df = df[df["year"] == selected_year - 1]

# Fixed category -> color mapping for THIS year's data, same rank-based
# assignment scheme as the main dashboard.
category_totals = year_df.groupby("category")["amount"].sum().sort_values(ascending=False)
top_categories = list(category_totals.index[:8])
category_color = {cat: SLOTS[i] for i, cat in enumerate(top_categories)}


def color_for(cat: str) -> str:
    return category_color.get(cat, OTHER_GRAY)


is_current_year = selected_year == pd.Timestamp.today().year
if is_current_year:
    st.caption(f"{selected_year} data so far (year in progress) -- {len(year_df)} transactions.")
else:
    st.caption(f"{len(year_df)} transactions in {selected_year}.")

# --- Stat tiles -------------------------------------------------------
total_spend = year_df["amount"].sum()
txn_count = len(year_df)
avg_txn = year_df["amount"].mean() if txn_count else 0
top_cat_name = category_totals.index[0] if not category_totals.empty else "--"

prior_total = prior_df["amount"].sum()
yoy_label = "vs prior year"
if prior_total:
    yoy_pct = (total_spend - prior_total) / prior_total * 100
    yoy_value = f"{'+' if yoy_pct >= 0 else ''}{yoy_pct:.0f}%"
else:
    yoy_value = "n/a"

tile_colors = [SLOTS[0], SLOTS[2], SLOTS[3], SLOTS[6]]
tiles = [
    ("Total spend", f"₹{total_spend:,.0f}"),
    ("Transactions", f"{txn_count:,}"),
    ("Avg transaction", f"₹{avg_txn:,.0f}"),
    (yoy_label, yoy_value),
]
cols = st.columns(4)
for col, (label, value), accent in zip(cols, tiles, tile_colors):
    with col:
        stat_tile(label, value, accent)

st.write("")

if year_df.empty:
    st.info(f"No transactions recorded for {selected_year}.")
    st.stop()

# --- Spend by category, this year only -----------------------------------
st.subheader(f"Spend by category -- {selected_year}")
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
fig_cat = style_chart(fig_cat, height=min(560, 120 + 40 * len(cat_df)))
fig_cat.update_xaxes(title=None)
fig_cat.update_yaxes(title=None)
st.plotly_chart(fig_cat, width="stretch")

# --- Monthly breakdown within the year, split by category ----------------
st.subheader(f"Monthly breakdown -- {selected_year}")
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
year_df["color_category"] = year_df["category"].where(year_df["category"].isin(top_categories), "Other")
trend = year_df.groupby(["month_num", "color_category"])["amount"].sum().reset_index()
months_present = sorted(trend["month_num"].unique())
month_labels = [MONTH_NAMES[m - 1] for m in months_present]

series_order = top_categories + (["Other"] if "Other" in trend["color_category"].unique() else [])
fig_trend = go.Figure()
for cat in series_order:
    sub = trend[trend["color_category"] == cat].set_index("month_num")["amount"].reindex(months_present, fill_value=0)
    fig_trend.add_trace(
        go.Bar(
            x=month_labels,
            y=sub,
            name=cat,
            marker=dict(color=color_for(cat) if cat != "Other" else OTHER_GRAY),
            hovertemplate=f"{cat}" + " (%{x}): ₹%{y:,.0f}<extra></extra>",
        )
    )
fig_trend.update_layout(barmode="stack")
fig_trend = style_chart(fig_trend, height=400)
st.plotly_chart(fig_trend, width="stretch")

# --- Top merchants this year -----------------------------------------------
st.subheader(f"Top merchants -- {selected_year}")
top_merch = (
    year_df.groupby(["merchant_display", "category"])["amount"]
    .sum()
    .sort_values(ascending=False)
    .head(15)
    .reset_index()
    .rename(columns={"merchant_display": "merchant"})
)
top_merch_display = top_merch.copy()
top_merch_display["category"] = top_merch_display["category"].apply(lambda c: category_tag(c, color_for(c)))
top_merch_display["amount"] = top_merch_display["amount"].apply(lambda v: f"₹{v:,.0f}")
top_merch_display = top_merch_display.rename(columns={"merchant": "Merchant", "category": "Category", "amount": "Amount"})
st.write(top_merch_display[["Merchant", "Category", "Amount"]].to_html(escape=False, index=False), unsafe_allow_html=True)

st.write("")

# --- Transactions this year -------------------------------------------
st.subheader(f"Transactions -- {selected_year}")
txns_display = year_df.sort_values("date", ascending=False)[["date", "bank", "merchant", "category", "amount"]].copy()
txns_display.insert(3, "description", [describe(m, c) for m, c in zip(txns_display["merchant"], txns_display["category"])])
txns_display["date"] = txns_display["date"].dt.strftime("%Y-%m-%d")
txns_display["amount"] = txns_display["amount"].round(2)
txns_display = txns_display.rename(
    columns={"date": "Date", "bank": "Bank", "merchant": "Merchant", "description": "Description", "category": "Category", "amount": "Amount"}
)
st.dataframe(txns_display, width="stretch", hide_index=True)

# --- Notable this year --------------------------------------------------
st.write("")
st.subheader(f"Notable in {selected_year}")

# 1. Category that grew or shrank the most vs the prior year, if one exists.
if not prior_df.empty:
    this_by_cat = year_df.groupby("category")["amount"].sum()
    prior_by_cat = prior_df.groupby("category")["amount"].sum()
    all_cats = set(this_by_cat.index) | set(prior_by_cat.index)
    deltas = pd.Series({c: this_by_cat.get(c, 0) - prior_by_cat.get(c, 0) for c in all_cats})
    biggest_up = deltas.sort_values(ascending=False).index[0]
    if deltas[biggest_up] > 0:
        insight_card(
            STATUS["critical"] if deltas[biggest_up] > total_spend * 0.1 else STATUS["warning"],
            f"{biggest_up} rose the most vs {selected_year - 1}",
            f"₹{prior_by_cat.get(biggest_up, 0):,.0f} → ₹{this_by_cat.get(biggest_up, 0):,.0f}, "
            f"up ₹{deltas[biggest_up]:,.0f}.",
        )
    biggest_down = deltas.sort_values().index[0]
    if deltas[biggest_down] < 0:
        insight_card(
            STATUS["good"],
            f"{biggest_down} fell the most vs {selected_year - 1}",
            f"₹{prior_by_cat.get(biggest_down, 0):,.0f} → ₹{this_by_cat.get(biggest_down, 0):,.0f}, "
            f"down ₹{abs(deltas[biggest_down]):,.0f}.",
        )

# 2. Biggest single transaction of the year.
biggest_txn = year_df.loc[year_df["amount"].idxmax()]
insight_card(
    STATUS["warning"],
    f"Biggest single transaction: ₹{biggest_txn['amount']:,.0f}",
    f"{biggest_txn['merchant']} on {biggest_txn['date'].strftime('%d %b %Y')} "
    f"({biggest_txn['category']}, {biggest_txn['bank'].upper()} card).",
)

# 3. Most frequent merchant this year.
freq = year_df.groupby("merchant_display").agg(count=("amount", "size"), total=("amount", "sum")).sort_values("count", ascending=False)
if not freq.empty:
    top_freq_merchant = freq.index[0]
    insight_card(
        STATUS["good"],
        f"Most frequent merchant: {top_freq_merchant}",
        f"{int(freq.loc[top_freq_merchant, 'count'])} transactions totaling ₹{freq.loc[top_freq_merchant, 'total']:,.0f} "
        f"-- about once every {365 / freq.loc[top_freq_merchant, 'count']:.0f} days.",
    )

# 4. Categories that are new this year (didn't exist in any prior year).
all_prior_years_df = df[df["year"] < selected_year]
new_categories = set(year_df["category"].unique()) - set(all_prior_years_df["category"].unique())
if new_categories and not all_prior_years_df.empty:
    for cat in sorted(new_categories, key=lambda c: -category_totals.get(c, 0))[:3]:
        insight_card(
            STATUS["serious"],
            f"{cat} is a new category this year",
            f"₹{category_totals.get(cat, 0):,.0f} spent -- this didn't show up in any earlier year of data.",
        )
