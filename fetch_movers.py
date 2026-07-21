"""
Finds the day's top gainers and losers within the S&P 500.

Note on "overnight": this script runs once a day on a schedule (see the GitHub
Actions workflow), so it reports the most recently completed session's move,
not live pre-market data. If you want true pre-market movers you'd need a
paid real-time data feed (e.g. FactSet, if/when you get API access) and a
more frequent schedule - the free-tier daily-refresh version below still
gives you a very useful "what moved and by how much" view every morning.
"""

import io
import pandas as pd
import requests
import yfinance as yf

SP500_LIST_URL = (
    "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
)

MIN_AVG_DOLLAR_VOLUME = 5_000_000  # filters out illiquid names so movers are meaningful
TOP_N = 10


def _get_sp500_tickers():
    resp = requests.get(SP500_LIST_URL, timeout=20)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    # yfinance uses '-' instead of '.' for tickers like BRK.B
    tickers = df["Symbol"].str.replace(".", "-", regex=False).tolist()
    name_map = dict(zip(tickers, df["Security"]))
    return tickers, name_map


def get_movers_snapshot():
    tickers, name_map = _get_sp500_tickers()

    data = yf.download(tickers, period="1mo", interval="1d", progress=False, auto_adjust=True, group_by="column")
    closes = data["Close"]
    volumes = data["Volume"]

    rows = []
    for ticker in tickers:
        try:
            c = closes[ticker].dropna()
            v = volumes[ticker].dropna()
            if len(c) < 2:
                continue
            pct = (c.iloc[-1] / c.iloc[-2] - 1) * 100
            avg_dollar_vol = (c.tail(20) * v.tail(20)).mean()
            if pd.isna(avg_dollar_vol) or avg_dollar_vol < MIN_AVG_DOLLAR_VOLUME:
                continue
            rows.append(
                {
                    "ticker": ticker,
                    "name": name_map.get(ticker, ticker),
                    "last_close": round(float(c.iloc[-1]), 2),
                    "change_pct": round(float(pct), 2),
                    "avg_dollar_volume_m": round(float(avg_dollar_vol) / 1_000_000, 1),
                }
            )
        except Exception:
            continue

    rows.sort(key=lambda r: r["change_pct"], reverse=True)
    gainers = rows[:TOP_N]
    losers = rows[-TOP_N:][::-1]

    as_of = str(closes.index[-1].date()) if len(closes.index) else None

    return {"as_of": as_of, "gainers": gainers, "losers": losers}


if __name__ == "__main__":
    import json

    print(json.dumps(get_movers_snapshot(), indent=2))
