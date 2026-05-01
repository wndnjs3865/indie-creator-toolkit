#!/usr/bin/env python3
"""
Refresh tool metadata from public sources.
- Product Hunt RSS (no API key needed)
- AlternativeTo public pages (rate-limited, polite)

Run weekly via Actions.
"""
import json
import time
from pathlib import Path

import feedparser
import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

PRODUCT_HUNT_RSS = "https://www.producthunt.com/feed"
USER_AGENT = "indie-creator-toolkit/1.0 (research; respectful)"


def refresh_product_hunt(limit=20):
    out = []
    feed = feedparser.parse(PRODUCT_HUNT_RSS)
    for e in feed.entries[:limit]:
        out.append({
            "title": e.get("title", ""),
            "link": e.get("link", ""),
            "summary": (e.get("summary", "") or "")[:300],
            "published": e.get("published", ""),
        })
    return out


def main():
    snapshot = {
        "fetched_at": int(time.time()),
        "product_hunt_recent": refresh_product_hunt(),
    }
    out = DATA / "snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[fetch] {len(snapshot['product_hunt_recent'])} PH items → {out.name}")


if __name__ == "__main__":
    main()
