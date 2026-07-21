"""
Pulls key macro indicators from FRED (Federal Reserve Economic Data).
FRED has a free API - get a key in 30 seconds at https://fred.stlouisfed.org/docs/api/api_key.html
The key is read from the FRED_API_KEY environment variable (set as a GitHub Actions secret).
"""

import os
import requests

FRED_API_KEY = os.environ.get("FRED_API_KEY")
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# series_id -> (display name, units)
SERIES = {
    "DGS10": ("10Y Treasury Yield", "%"),
    "DGS2": ("2Y Treasury Yield", "%"),
    "T10Y2Y": ("10Y-2Y Spread", "pp"),
    "FEDFUNDS": ("Fed Funds Rate", "%"),
    "CPIAUCSL": ("CPI (YoY)", "%"),
    "UNRATE": ("Unemployment Rate", "%"),
    "VIXCLS": ("VIX", ""),
    "DTWEXBGS": ("US Dollar Index (Broad)", ""),
}


def _fetch_series(series_id, limit=15):
    """Return the most recent non-null observations for a FRED series, newest first."""
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": limit,
    }
    resp = requests.get(FRED_BASE, params=params, timeout=20)
    resp.raise_for_status()
    obs = resp.json().get("observations", [])
    # FRED uses "." for missing values
    clean = [o for o in obs if o["value"] != "."]
    return clean


def get_macro_snapshot():
    if not FRED_API_KEY:
        raise RuntimeError(
            "FRED_API_KEY is not set. Get a free key at "
            "https://fred.stlouisfed.org/docs/api/api_key.html and add it as a "
            "GitHub Actions secret named FRED_API_KEY."
        )

    results = []
    for series_id, (name, units) in SERIES.items():
        try:
            obs = _fetch_series(series_id)
            if not obs:
                continue
            latest = obs[0]
            value = float(latest["value"])

            # CPI is an index level, not a rate -> convert to YoY % change
            if series_id == "CPIAUCSL" and len(obs) >= 13:
                # observations are monthly and sorted desc, so index 12 is ~1 year prior
                year_ago = float(obs[12]["value"])
                value = round((value - year_ago) / year_ago * 100, 2)

            prior_value = None
            if len(obs) > 1 and series_id != "CPIAUCSL":
                prior_value = float(obs[1]["value"])

            change = round(value - prior_value, 3) if prior_value is not None else None

            results.append(
                {
                    "id": series_id,
                    "name": name,
                    "units": units,
                    "value": round(value, 3),
                    "change": change,
                    "as_of": latest["date"],
                }
            )
        except Exception as e:
            results.append({"id": series_id, "name": name, "error": str(e)})

    return results


if __name__ == "__main__":
    import json

    print(json.dumps(get_macro_snapshot(), indent=2))
