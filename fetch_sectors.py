"""
Computes sector relative strength vs SPY using the 11 SPDR sector ETFs.
Uses yfinance, which needs no API key.
"""

import yfinance as yf

SECTOR_ETFS = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLE": "Energy",
    "XLV": "Health Care",
    "XLI": "Industrials",
    "XLP": "Consumer Staples",
    "XLY": "Consumer Discretionary",
    "XLU": "Utilities",
    "XLB": "Materials",
    "XLRE": "Real Estate",
    "XLC": "Communication Services",
}

BENCHMARK = "SPY"


def _pct_change(closes, days):
    """% change over the last `days` trading days using a closes Series (newest last)."""
    if len(closes) <= days:
        return None
    return round((closes.iloc[-1] / closes.iloc[-1 - days] - 1) * 100, 2)


def get_sector_snapshot():
    tickers = list(SECTOR_ETFS.keys()) + [BENCHMARK]
    # ~4 months of daily data is enough for 1D/5D/1M/3M windows
    data = yf.download(tickers, period="4mo", interval="1d", progress=False, auto_adjust=True)

    if data.empty:
        raise RuntimeError("yfinance returned no data - check tickers / network.")

    closes = data["Close"]

    spy_1d = _pct_change(closes[BENCHMARK], 1)
    spy_5d = _pct_change(closes[BENCHMARK], 5)
    spy_1m = _pct_change(closes[BENCHMARK], 21)
    spy_3m = _pct_change(closes[BENCHMARK], 63)

    results = []
    for ticker, name in SECTOR_ETFS.items():
        series = closes[ticker].dropna()
        d1 = _pct_change(series, 1)
        d5 = _pct_change(series, 5)
        d21 = _pct_change(series, 21)
        d63 = _pct_change(series, 63)

        results.append(
            {
                "ticker": ticker,
                "name": name,
                "change_1d": d1,
                "change_5d": d5,
                "change_1m": d21,
                "change_3m": d63,
                # relative strength = sector return minus SPY return, same window
                "rel_strength_1d": round(d1 - spy_1d, 2) if d1 is not None and spy_1d is not None else None,
                "rel_strength_5d": round(d5 - spy_5d, 2) if d5 is not None and spy_5d is not None else None,
                "rel_strength_1m": round(d21 - spy_1m, 2) if d21 is not None and spy_1m is not None else None,
                "rel_strength_3m": round(d63 - spy_3m, 2) if d63 is not None and spy_3m is not None else None,
            }
        )

    # rank by 1-month relative strength, strongest first
    results.sort(key=lambda r: (r["rel_strength_1m"] is None, -(r["rel_strength_1m"] or 0)))

    return {
        "benchmark": BENCHMARK,
        "benchmark_change_1d": spy_1d,
        "benchmark_change_5d": spy_5d,
        "benchmark_change_1m": spy_1m,
        "benchmark_change_3m": spy_3m,
        "sectors": results,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(get_sector_snapshot(), indent=2))
