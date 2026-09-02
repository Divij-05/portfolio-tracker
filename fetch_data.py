import yfinance as yf
import pandas as pd
import sqlite3


def load_holdings(path="holdings.csv"):
    """Read the holdings file and return it as a DataFrame."""
    return pd.read_csv(path)


def fetch_and_store(period="1y"):
    holdings = load_holdings()
    tickers = holdings["ticker"].tolist()

    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()

    for ticker in tickers:
        print(f"Fetching {ticker}...", end=" ")

        data = yf.download(ticker, period=period, progress=False, auto_adjust=True)

        if data.empty:
            print("no data returned, skipping.")
            continue

        # yfinance returns multi-level columns when given a list;
        # flatten them so row access is predictable.
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        rows = []
        for date, row in data.iterrows():
            rows.append((
                ticker,
                date.strftime("%Y-%m-%d"),
                float(row["Open"]),
                float(row["High"]),
                float(row["Low"]),
                float(row["Close"]),
                int(row["Volume"]),
            ))

        cursor.executemany("""
            INSERT OR IGNORE INTO prices
                (ticker, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, rows)

        print(f"{len(rows)} rows.")

    conn.commit()
    conn.close()
    print("\nDone. Data written to portfolio.db")


if __name__ == "__main__":
    fetch_and_store()