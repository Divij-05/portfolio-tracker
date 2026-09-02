import sqlite3
import pandas as pd
import plotly.express as px

BENCHMARK = "SPY"


def load_prices(conn):
    df = pd.read_sql("SELECT ticker, date, close FROM prices", conn)
    df["date"] = pd.to_datetime(df["date"])
    return df


def build_portfolio_value(prices, holdings):
    """Daily total value of the holdings, excluding the benchmark."""
    positions = holdings[holdings["ticker"] != BENCHMARK]

    merged = prices.merge(positions, on="ticker")
    merged["position_value"] = merged["close"] * merged["shares"]

    daily = (
        merged.groupby("date")["position_value"]
        .sum()
        .reset_index()
        .rename(columns={"position_value": "value"})
    )
    return daily


def normalise(series):
    """Rebase a series so it starts at 100."""
    return series / series.iloc[0] * 100


def compare_to_benchmark(prices, holdings):
    portfolio = build_portfolio_value(prices, holdings)

    benchmark = (
        prices[prices["ticker"] == BENCHMARK][["date", "close"]]
        .rename(columns={"close": "value"})
        .sort_values("date")
        .reset_index(drop=True)
    )

    combined = pd.DataFrame({
        "date": portfolio["date"],
        "Portfolio": normalise(portfolio["value"]),
        BENCHMARK: normalise(benchmark["value"]),
    })

    return combined.melt(
        id_vars="date",
        var_name="series",
        value_name="index_value",
    )


def main():
    conn = sqlite3.connect("portfolio.db")
    prices = load_prices(conn)
    conn.close()

    holdings = pd.read_csv("holdings.csv")

    comparison = compare_to_benchmark(prices, holdings)

    finals = comparison.groupby("series")["index_value"].last()
    for name, value in finals.items():
        print(f"{name:<10} {value - 100:+.2f}%")

    fig = px.line(
        comparison,
        x="date",
        y="index_value",
        color="series",
        title=f"Portfolio vs {BENCHMARK} (both rebased to 100)",
        labels={"date": "Date", "index_value": "Index (start = 100)", "series": ""},
    )
    fig.show()


if __name__ == "__main__":
    main()