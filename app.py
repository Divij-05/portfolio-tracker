import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

BENCHMARK = "SPY"

st.set_page_config(page_title="Portfolio Tracker", layout="wide")


@st.cache_data
def load_data():
    conn = sqlite3.connect("portfolio.db")
    prices = pd.read_sql("SELECT ticker, date, close, volume FROM prices", conn)
    conn.close()
    prices["date"] = pd.to_datetime(prices["date"])
    holdings = pd.read_csv("holdings.csv")
    return prices, holdings


def positions_only(holdings):
    return holdings[holdings["ticker"] != BENCHMARK]


def portfolio_value(prices, holdings):
    merged = prices.merge(positions_only(holdings), on="ticker")
    merged["position_value"] = merged["close"] * merged["shares"]
    return (
        merged.groupby("date")["position_value"]
        .sum()
        .reset_index()
        .rename(columns={"position_value": "value"})
    )


def normalise(series):
    return series / series.iloc[0] * 100


prices, holdings = load_data()

st.title("Portfolio Tracker")

# --- Sidebar: date range ---
min_date = prices["date"].min().date()
max_date = prices["date"].max().date()

start, end = st.sidebar.slider(
    "Date range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD",
)

prices = prices[(prices["date"].dt.date >= start) & (prices["date"].dt.date <= end)]

# --- Headline metrics ---
daily = portfolio_value(prices, holdings)
latest = daily["value"].iloc[-1]
first = daily["value"].iloc[0]
pct = (latest - first) / first * 100

latest_prices = prices.sort_values("date").groupby("ticker")["close"].last()
current = positions_only(holdings).copy()
current["price"] = current["ticker"].map(latest_prices)
current["value"] = current["price"] * current["shares"]
current["cost"] = current["cost_basis"] * current["shares"]
current["pnl"] = current["value"] - current["cost"]

c1, c2, c3 = st.columns(3)
c1.metric("Portfolio value", f"${latest:,.0f}")
c2.metric("Change over period", f"{pct:+.2f}%")
c3.metric("Unrealised P&L", f"${current['pnl'].sum():,.0f}")

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(
    ["Value", "Benchmark", "Allocation", "Single stock"]
)

with tab1:
    fig = px.line(daily, x="date", y="value", title="Portfolio value over time")
    st.plotly_chart(fig, width='stretch')

with tab2:
    bench = (
        prices[prices["ticker"] == BENCHMARK][["date", "close"]]
        .sort_values("date")
        .reset_index(drop=True)
    )
    combined = pd.DataFrame({
        "date": daily["date"],
        "Portfolio": normalise(daily["value"]),
        BENCHMARK: normalise(bench["close"]),
    }).melt(id_vars="date", var_name="series", value_name="index_value")

    fig = px.line(
        combined, x="date", y="index_value", color="series",
        title=f"Portfolio vs {BENCHMARK} (rebased to 100)",
    )
    st.plotly_chart(fig, width='stretch')

with tab3:
    by_sector = current.groupby("sector")["value"].sum().reset_index()
    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            px.pie(by_sector, values="value", names="sector", title="By sector", hole=0.4),
            width='stretch',
        )
    with right:
        st.plotly_chart(
            px.bar(
                current.sort_values("value"),
                x="value", y="ticker", orientation="h", title="By holding",
            ),
            width='stretch',
        )
    st.dataframe(
        current[["ticker", "sector", "shares", "cost_basis", "price", "value", "pnl"]]
        .sort_values("value", ascending=False),
        width='stretch',
        hide_index=True,
    )

with tab4:
    ticker = st.selectbox("Ticker", sorted(prices["ticker"].unique()))
    one = prices[prices["ticker"] == ticker].sort_values("date").copy()
    one["MA50"] = one["close"].rolling(50).mean()
    one["MA200"] = one["close"].rolling(200).mean()

    fig = px.line(
        one.melt(
            id_vars="date",
            value_vars=["close", "MA50", "MA200"],
            var_name="series",
            value_name="price",
        ),
        x="date", y="price", color="series", title=f"{ticker} price and moving averages",
    )
    st.plotly_chart(fig, width='stretch')