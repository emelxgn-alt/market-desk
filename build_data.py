"""
Orchestrates all fetchers and writes a single combined data/dashboard.json
that the static dashboard (index.html) reads.

Each section is wrapped in try/except so that one failing data source
(e.g. FRED being down) doesn't take out the whole dashboard - it just shows
an error badge for that section instead of a blank page.
"""

import json
import os
import sys
import traceback
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from fetch_macro import get_macro_snapshot
from fetch_sectors import get_sector_snapshot
from fetch_movers import get_movers_snapshot

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "dashboard.json")


def _safe_run(label, fn):
    try:
        return {"ok": True, "data": fn()}
    except Exception as e:
        print(f"[build_data] {label} failed: {e}", file=sys.stderr)
        traceback.print_exc()
        return {"ok": False, "error": str(e)}


def main():
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "macro": _safe_run("macro", get_macro_snapshot),
        "sectors": _safe_run("sectors", get_sector_snapshot),
        "movers": _safe_run("movers", get_movers_snapshot),
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote {OUTPUT_PATH}")

    # Exit non-zero only if EVERYTHING failed, so a partial success still
    # commits a useful dashboard.json in CI.
    if not any(section["ok"] for section in (payload["macro"], payload["sectors"], payload["movers"])):
        sys.exit(1)


if __name__ == "__main__":
    main()
