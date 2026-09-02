import sqlite3
import pandas as pd

conn = sqlite3.connect("portfolio.db")

total = pd.read_sql("SELECT COUNT(*) AS rows FROM prices", conn)
print(total, "\n")

per_ticker = pd.read_sql("""
    SELECT ticker,
           COUNT(*)   AS rows,
           MIN(date)  AS earliest,
           MAX(date)  AS latest
    FROM prices
    GROUP BY ticker
    ORDER BY ticker
""", conn)
print(per_ticker, "\n")

sample = pd.read_sql("""
    SELECT * FROM prices
    WHERE ticker = 'NVDA'
    ORDER BY date DESC
    LIMIT 5
""", conn)
print(sample)

conn.close()