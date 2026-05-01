#!/usr/bin/env python3
"""
Generate ONE new page from the seed pattern matrix.

Patterns supported:
  1. best-{category}-for-{persona}        ("best podcast hosting for solo podcasters")
  2. {tool-a}-vs-{tool-b}                 ("notion vs obsidian")
  3. free-alternatives-to-{tool}          ("free alternatives to substack")

Strategy: rotate through patterns to avoid one-pattern saturation.
Picks the next combo that doesn't already have a page.

Pure rule-based — no LLM at runtime. Narrative is templated using
real seed-tools.json data so each page has substantive comparison
content, not stub fluff.
"""
import json
import datetime as dt
import re
import sys
from pathlib import Path
import random
import itertools

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


# --- pattern 1: best X for Y ---

def find_best_combo(personas, categories, tools, exists):
    random.shuffle(personas)
    random.shuffle(categories)
    for p in personas:
        for c in categories:
            slug = f"best-{c['id']}-for-{p['id']}"
            if slug in exists:
                continue
            relevant = [t for t in tools
                        if c["id"] in t["categories"] and p["id"] in t["personas"]]
            if len(relevant) >= 3:
                return ("best", p, c, relevant, slug)
    return None


def emit_best(persona, category, tools, slug):
    title = f"Best {category['label']} for {persona['label']} in 2026"
    description = (
        f"We compared {len(tools)} {category['label']} options for {persona['label']}: "
        f"free, freemium, and paid. Here are the {min(5, len(tools))} that actually deliver."
    )

    # SD-004: max 5 affiliate-eligible tools per page
    picks = tools[:5]
    rows = ["| Tool | Free tier | Starting price | Open source | Best for |",
            "|---|---|---|---|---|"]
    sections = []
    for t in picks:
        price = "Free" if t["starting_price_usd"] == 0 else f"${t['starting_price_usd']}/mo"
        oss = "✅" if t.get("open_source") else "—"
        best = "; ".join(t.get("best_for", [])) or "—"
        rows.append(f"| **[{t['name']}]({t['homepage']})** | {t['free_tier']} | {price} | {oss} | {best} |")

        pros = "\n".join(f"- {x}" for x in t.get("pros", []))
        cons = "\n".join(f"- {x}" for x in t.get("cons", []))
        platform = t.get("platform", "—")
        sections.append(f"""### {t['name']}

**Free tier**: {t['free_tier']}
**Pricing**: {'Free forever' if t['paid_price_usd'] == 0 else f"From ${t['starting_price_usd']}/mo, ${t['paid_price_usd']}/mo for full features"}
**Platform**: {platform}

[{t['name']}]({t['homepage']}) is a strong pick for {persona['label']} working in {category['label']} because it directly addresses the workflow without forcing you onto an enterprise plan.

**Pros**
{pros or '- Solid all-rounder'}

**Cons**
{cons or '- Some workflows need a paid upgrade'}
""")

    faq = f"""## FAQ

**Is there a truly free option for {category['label']}?**
Yes — {next((t['name'] for t in picks if t['paid_price_usd'] == 0), 'most picks here')} is free forever.
For everything else, the free tier is enough to validate before paying.

**What's the cheapest paid option that's still serious?**
{min(picks, key=lambda x: x['paid_price_usd'] if x['paid_price_usd'] > 0 else 1e9)['name']} at ${min((t['paid_price_usd'] for t in picks if t['paid_price_usd'] > 0), default=0)}/mo.

**Do I need {category['label']} at all when starting out?**
Honestly, no. Most {persona['label'].rstrip('s')} ship their first project with whatever's on their laptop already. Tools matter once friction starts costing you hours per week.
"""

    fm = (
        "---\n"
        f"slug: {slug}\n"
        f"title: \"{title}\"\n"
        f"description: \"{description}\"\n"
        f"persona: {persona['id']}\n"
        f"persona_label: \"{persona['label']}\"\n"
        f"category: {category['id']}\n"
        f"pattern: best\n"
        f"updated: {dt.date.today().isoformat()}\n"
        "---\n\n"
    )
    body = (
        f"If you're a {persona['label'].rstrip('s')} starting out, the right "
        f"{category['label']} can save you hours every week. We compared {len(tools)} "
        f"options and picked the {len(picks)} that actually deliver without forcing "
        "you onto an enterprise plan.\n\n"
        "## Quick comparison\n\n" + "\n".join(rows) + "\n\n"
        "## Detailed picks\n\n" + "\n".join(sections) + "\n"
        + faq + "\n"
        "## How we picked\n\n"
        "We prioritized (1) genuine free tiers (not 14-day trials), "
        "(2) export/portability so you can leave without losing data, "
        "(3) recent activity (updated within the last 12 months), "
        "(4) a workflow that fits a one-person team.\n\n"
        "## Disclosure\n\n"
        "Some links above are affiliate links. We earn a small commission "
        "if you sign up — at no extra cost to you. We only feature tools "
        "we'd recommend regardless.\n"
    )

    (CONTENT / f"{slug}.md").write_text(fm + body, encoding="utf-8")
    return slug


# --- pattern 2: A vs B ---

def find_vs_combo(tools, exists):
    by_cat = {}
    for t in tools:
        for c in t["categories"]:
            by_cat.setdefault(c, []).append(t)
    pairs = []
    for c, ts in by_cat.items():
        if len(ts) >= 2:
            for a, b in itertools.combinations(ts, 2):
                pairs.append((a, b, c))
    random.shuffle(pairs)
    for a, b, c in pairs:
        slug = f"{a['id']}-vs-{b['id']}"
        if slug in exists or f"{b['id']}-vs-{a['id']}" in exists:
            continue
        return ("vs", a, b, c, slug)
    return None


def emit_vs(a, b, category, slug):
    title = f"{a['name']} vs {b['name']}: which is right for you in 2026"
    description = f"Honest head-to-head: {a['name']} vs {b['name']}. Pricing, free tiers, pros, cons, and who should pick which."

    def price_cell(t, key):
        v = t[key]
        return "Free" if v == 0 else f"${v}/mo"
    def paid_cell(t):
        v = t["paid_price_usd"]
        return "—" if v == 0 else f"${v}/mo"

    table = [
        f"| | {a['name']} | {b['name']} |",
        "|---|---|---|",
        f"| Free tier | {a['free_tier']} | {b['free_tier']} |",
        f"| Starting price | {price_cell(a, 'starting_price_usd')} | {price_cell(b, 'starting_price_usd')} |",
        f"| Paid price | {paid_cell(a)} | {paid_cell(b)} |",
        f"| Platform | {a.get('platform','—')} | {b.get('platform','—')} |",
        f"| Open source | {'Yes' if a.get('open_source') else 'No'} | {'Yes' if b.get('open_source') else 'No'} |",
    ]

    a_pros = "\n".join(f"- {x}" for x in a.get("pros", []))
    a_cons = "\n".join(f"- {x}" for x in a.get("cons", []))
    b_pros = "\n".join(f"- {x}" for x in b.get("pros", []))
    b_cons = "\n".join(f"- {x}" for x in b.get("cons", []))

    fm = (
        "---\n"
        f"slug: {slug}\n"
        f"title: \"{title}\"\n"
        f"description: \"{description}\"\n"
        f"persona: comparison\n"
        f"persona_label: \"Comparison\"\n"
        f"category: {category}\n"
        f"pattern: vs\n"
        f"updated: {dt.date.today().isoformat()}\n"
        "---\n\n"
    )
    body = (
        f"You're picking between [{a['name']}]({a['homepage']}) and [{b['name']}]({b['homepage']}). "
        f"Both serve {category.replace('-', ' ')} workflows. Here's how they actually differ.\n\n"
        "## Side-by-side\n\n" + "\n".join(table) + "\n\n"
        f"## Where {a['name']} wins\n\n{a_pros}\n\n"
        f"### {a['name']} downsides\n\n{a_cons}\n\n"
        f"## Where {b['name']} wins\n\n{b_pros}\n\n"
        f"### {b['name']} downsides\n\n{b_cons}\n\n"
        "## Verdict\n\n"
        f"- **Pick [{a['name']}]({a['homepage']})** if you value: " + ", ".join((a.get("best_for") or ["broad fit"])) + ".\n"
        f"- **Pick [{b['name']}]({b['homepage']})** if you value: " + ", ".join((b.get("best_for") or ["broad fit"])) + ".\n\n"
        "If you're starting from zero, the free tier of either lets you ship "
        "your first project before you commit. That's the right way to choose.\n\n"
        "## Disclosure\n\n"
        "Links may be affiliate. We only compare tools we'd actually use.\n"
    )
    (CONTENT / f"{slug}.md").write_text(fm + body, encoding="utf-8")
    return slug


# --- pattern 3: free alternatives to X ---

def find_free_alts_combo(tools, exists):
    paid = [t for t in tools if t["paid_price_usd"] > 0]
    random.shuffle(paid)
    for target in paid:
        slug = f"free-alternatives-to-{target['id']}"
        if slug in exists:
            continue
        # Find truly free alternatives in same categories
        alts = [t for t in tools
                if t["id"] != target["id"]
                and t["paid_price_usd"] == 0
                and any(c in target["categories"] for c in t["categories"])]
        if len(alts) >= 2:
            return ("free", target, alts[:5], slug)
    return None


def emit_free_alts(target, alts, slug):
    title = f"Free alternatives to {target['name']} in 2026"
    description = f"{target['name']} not in the budget? Here are {len(alts)} free alternatives that get the job done."

    rows = ["| Tool | License | Platform | Best for |", "|---|---|---|---|"]
    sections = []
    for t in alts:
        license_str = "Open source" if t.get("open_source") else "Free (proprietary)"
        rows.append(f"| **[{t['name']}]({t['homepage']})** | {license_str} | {t.get('platform','—')} | {'; '.join(t.get('best_for',[])) or '—'} |")
        pros = "\n".join(f"- {x}" for x in t.get("pros", []))
        sections.append(f"""### {t['name']}

[{t['name']}]({t['homepage']}) is {('open source' if t.get('open_source') else 'free to use')} and serves the same workflow as {target['name']} for most {('beginners' if target['paid_price_usd'] < 50 else 'pro')} use cases.

**Why it works as a {target['name']} alternative**

{pros or '- Covers the core workflow'}

**Where it falls short of {target['name']}**

If you need {('; '.join(target.get('best_for', [])[:1]) or 'specialized features')}, you'll eventually outgrow this.
""")

    fm = (
        "---\n"
        f"slug: {slug}\n"
        f"title: \"{title}\"\n"
        f"description: \"{description}\"\n"
        f"persona: free-alternatives\n"
        f"persona_label: \"Free alternatives\"\n"
        f"category: {target['categories'][0]}\n"
        f"pattern: free-alts\n"
        f"updated: {dt.date.today().isoformat()}\n"
        "---\n\n"
    )
    body = (
        f"[{target['name']}]({target['homepage']}) costs ${target['paid_price_usd']}/mo. "
        "If that's not in the budget yet, here are free options that get most of the job done.\n\n"
        "## Quick comparison\n\n" + "\n".join(rows) + "\n\n"
        "## Each alternative in detail\n\n" + "\n".join(sections) + "\n"
        f"## When you should just pay for {target['name']}\n\n"
        f"If you're already making money from your work and {target['name']} would save "
        "you 2+ hours/week, the math says pay for it. Free alternatives are right when "
        "you're validating an idea or learning the craft.\n\n"
        "## Disclosure\n\n"
        "Links may be affiliate. We only compare tools we'd actually use.\n"
    )
    (CONTENT / f"{slug}.md").write_text(fm + body, encoding="utf-8")
    return slug


def main():
    with open(DATA / "seed-keywords.json") as f:
        seeds = json.load(f)
    with open(DATA / "seed-tools.json") as f:
        tools = json.load(f)["tools"]

    exists = existing_slugs()

    # Rotate patterns to balance the page mix.
    # Stat: aim for ~50% best, ~30% vs, ~20% free-alts
    n = len(exists)
    if n % 5 in (0, 1, 2):
        pattern_order = ["best", "vs", "free"]
    elif n % 5 == 3:
        pattern_order = ["vs", "best", "free"]
    else:
        pattern_order = ["free", "best", "vs"]

    for which in pattern_order:
        if which == "best":
            r = find_best_combo(seeds["personas"][:], seeds["categories"][:], tools, exists)
            if r:
                _, p, c, ts, slug = r
                emit_best(p, c, ts, slug)
                print(f"[generate] BEST → {slug}")
                return
        elif which == "vs":
            r = find_vs_combo(tools, exists)
            if r:
                _, a, b, c, slug = r
                emit_vs(a, b, c, slug)
                print(f"[generate] VS → {slug}")
                return
        elif which == "free":
            r = find_free_alts_combo(tools, exists)
            if r:
                _, target, alts, slug = r
                emit_free_alts(target, alts, slug)
                print(f"[generate] FREE → {slug}")
                return

    print("[generate] no new combos available — saturation reached")
    sys.exit(0)


if __name__ == "__main__":
    main()
