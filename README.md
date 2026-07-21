# Market Desk

A personal macro / sector / movers dashboard that refreshes itself every weekday morning
via GitHub Actions and is hosted for free on GitHub Pages.

**Live sections:**
- **Macro** — 10Y/2Y yields, yield curve spread, Fed funds rate, CPI (YoY), unemployment, VIX, dollar index (via FRED)
- **Sector relative strength** — the 11 SPDR sector ETFs vs SPY, over 1D/5D/1M/3M windows
- **Movers** — top S&P 500 gainers/losers from the most recently completed session
- **Themes** — a manual notes section you edit by hand (no clean free data source for "narrative")

---

## 1. Get a free FRED API key

Macro data comes from the Federal Reserve's FRED database (free, no cost, no card required).

1. Go to https://fred.stlouisfed.org/docs/api/api_key.html
2. Create an account, request an API key — it's issued instantly.
3. Copy the key, you'll need it in step 3 below.

Sector and mover data use `yfinance` (Yahoo Finance), which needs no key at all.

## 2. Create the GitHub repo

1. On github.com, click **New repository**. Name it whatever you like (e.g. `market-desk`).
   Keep it **Public** (required for free GitHub Pages, unless you have GitHub Pro/Team).
2. Upload all the files from this folder into that repo (drag-and-drop on the GitHub
   web UI works fine — no command line needed).

## 3. Add your FRED key as a secret

1. In your repo: **Settings → Secrets and variables → Actions → New repository secret**.
2. Name: `FRED_API_KEY`. Value: the key from step 1.
3. Save.

## 4. Turn on GitHub Pages

1. **Settings → Pages**.
2. Under "Build and deployment", set **Source: Deploy from a branch**.
3. Branch: `main`, folder: `/ (root)`. Save.
4. GitHub will give you a URL like `https://yourusername.github.io/market-desk/` —
   that's your dashboard.

## 5. Run it once manually

You don't have to wait for the schedule:

1. Go to the **Actions** tab in your repo.
2. Click **Daily dashboard refresh** in the left sidebar.
3. Click **Run workflow → Run workflow**.
4. Wait ~1-2 minutes, refresh the Actions tab until it shows a green check.
5. Visit your Pages URL — you should see live data.

After this, it runs automatically every weekday at 11:15 UTC (~7:15am ET, before the
US market opens) and commits the refreshed `data/dashboard.json` itself — nothing more
to do.

---

## Repo structure

```
market-desk/
├── .github/workflows/daily-update.yml   # the daily scheduler (GitHub Actions)
├── scripts/
│   ├── fetch_macro.py     # pulls FRED series
│   ├── fetch_sectors.py   # pulls sector ETF prices, computes relative strength
│   ├── fetch_movers.py    # pulls S&P 500 prices, finds top gainers/losers
│   └── build_data.py      # runs all three, writes data/dashboard.json
├── data/dashboard.json    # the generated data file the page reads (auto-updated)
├── index.html             # the dashboard itself (static HTML/CSS/JS, no build step)
├── requirements.txt
└── README.md
```

## Running it locally (optional)

If you ever want to test changes on your own machine before pushing:

```bash
pip install -r requirements.txt
export FRED_API_KEY=your_key_here
python scripts/build_data.py
# then open index.html directly in a browser, or run:
python -m http.server 8000
# and visit http://localhost:8000
```

## Known limitations / things worth knowing

- **"Movers" is prior-session, not true overnight/pre-market.** Since this runs once a
  day, it reports the most recently completed trading session's move. True pre-market
  data generally needs a paid real-time feed. If you ever get FactSet API/developer
  access (rather than just the Workstation app), that's the natural upgrade path — FactSet's
  data is much richer and this fetcher could be swapped out for a FactSet call without
  touching anything else in the pipeline.
- **TradingView isn't used for automated pulls.** Its standard subscription doesn't
  offer a programmatic API for this kind of use — it's better kept as a manual lookup
  tool alongside this dashboard rather than a data source for it.
- **Free-tier data (Yahoo Finance via yfinance) is "good enough," not institutional-grade.**
  It occasionally has minor delays or gaps. Fine for a personal daily gut-check;
  not something to build a trading algorithm's execution logic on.
- **Themes has no automated feed.** Edit the `THEMES` array near the bottom of
  `index.html` by hand whenever you want to jot down what you're watching.

## Extending it

Some natural next steps once the basics are working:
- Add more macro series (just add entries to the `SERIES` dict in `fetch_macro.py`)
- Track a custom watchlist instead of/alongside the S&P 500 in `fetch_movers.py`
- Add a historical chart (store each day's `dashboard.json` instead of overwriting it)
- Swap in FactSet data if/when you get API access
