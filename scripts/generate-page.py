#!/usr/bin/env python3
"""
Generate one new page from the seed pattern matrix.
Run by GitHub Actions daily-page.yml workflow.

Strategy: pick a persona × category combo that has no existing page,
emit a Markdown stub with the data table pre-filled. The Claude Code
session (or human) flesh out narrative paragraphs in a follow-up commit.

This file is intentionally LLM-free at runtime — pure rule-based.
The narrative is a templated placeholder + data table from seed-tools.json.
That keeps zero-dependency at runtime and avoids paid API calls.
"""
import json
import datetime as dt
import re
import sys
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
DATA = ROOT / "data"


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return s.strip("-")


def existing_slugs():
    return {p.stem for p in CONTENT.glob("*.md")}


def pick_combo(personas, categories, tools, exists):
    """Find a persona × category combo without an existing page."""
    random.shuffle(personas)
    random.shuffle(categories)
    for p in personas:
        for c in categories:
            slug = f"best-{c['id']}-for-{p['id']}"
            if slug in exists:
                continue
            # Need at least 2 tools tagged with this persona+category
            relevant = [t for t in tools
                        if c["id"] in t["categories"] and p["id"] in t["personas"]]
            if len(relevant) >= 2:
                return p, c, relevant, slug
    return None


def emit_page(persona, category, tools, slug):
    title = f"Best {category['label']} for {persona['label']} in 2026"
    description = (
        f"We compared {len(tools)} {category['label']} options for "
        f"{persona['label']} — free, freemium, and paid. Here's what we recommend."
    )

    rows = ["| Tool | Free tier | Starting price | Best for |", "|---|---|---|---|"]
    body_sections = []
    for t in tools[:5]:  # SD-004: max 5 affiliate links
        price = ("Free" if t["starting_price_usd"] == 0
                 else f"${t['starting_price_usd']}/mo")
        best = "; ".join(t.get("best_for", [])) or "—"
        rows.append(f"| **[{t['name']}]({t['homepage']})** | {t['free_tier']} | {price} | {best} |")

        body_sections.append(f"""### {t['name']}

**Free tier**: {t['free_tier']}
**Pricing**: {'Free forever' if t['paid_price_usd'] == 0 else f"From ${t['starting_price_usd']}/mo, ${t['paid_price_usd']}/mo for full features"}

[{t['name']}]({t['homepage']}) is a strong pick for {persona['label']} because it directly addresses the {category['label']} workflow without the bloat of larger suites. {('It is fully free and open source.' if t['paid_price_usd'] == 0 else 'The free tier is generous enough to validate before paying.')}
""")

    fm = (
        "---\n"
        f"slug: {slug}\n"
        f"title: \"{title}\"\n"
        f"description: \"{description}\"\n"
        f"persona: {persona['id']}\n"
        f"persona_label: \"{persona['label']}\"\n"
        f"category: {category['id']}\n"
        f"updated: {dt.date.today().isoformat()}\n"
        "---\n\n"
    )

    body = (
        f"# {title}\n\n"
        f"If you're a {persona['label'].rstrip('s')} starting out, the right "
        f"{category['label']} can save you hours every week. We compared "
        f"{len(tools)} options and picked the {min(5, len(tools))} that actually deliver "
        "without forcing you onto an enterprise plan.\n\n"
        "## Quick comparison\n\n"
        + "\n".join(rows)
        + "\n\n## Detailed look\n\n"
        + "\n".join(body_sections)
        + "\n\n## How we picked\n\n"
        "We prioritized (1) genuine free tiers (not 14-day trials), "
        "(2) export/portability so you can leave without losing data, "
        "(3) recent activity (updated within the last 12 months).\n\n"
        "## Disclosure\n\n"
        "Some links above are affiliate links. We earn a small commission "
        "if you sign up — at no extra cost to you. We only feature tools "
        "we'd recommend regardless.\n"
    )

    out = CONTENT / f"{slug}.md"
    out.write_text(fm + body, encoding="utf-8")
    print(f"[generate] wrote {out.name}")
    return slug


def main():
    with open(DATA / "seed-keywords.json") as f:
        seeds = json.load(f)
    with open(DATA / "seed-tools.json") as f:
        tools = json.load(f)["tools"]

    exists = existing_slugs()
    combo = pick_combo(seeds["personas"], seeds["categories"], tools, exists)
    if not combo:
        print("[generate] no new combos available — all covered")
        sys.exit(0)
    persona, category, relevant_tools, slug = combo
    emit_page(persona, category, relevant_tools, slug)


if __name__ == "__main__":
    main()
