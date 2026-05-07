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


_LOGO_CLASSES = ["b1", "b2", "b3", "b4", "b5", "b6"]
_BEST_BADGES = ["badge-best", "badge-pro", "badge-popular", "badge-budget", "badge-free"]


def _badge_for_tool(t, idx):
    """Pick a badge based on tool attributes + position in list."""
    if idx == 0:
        return ("badge-best", "Top pick")
    if t.get("open_source"):
        return ("badge-free", "Open source")
    if t["paid_price_usd"] == 0:
        return ("badge-free", "Free")
    if t["paid_price_usd"] >= 25:
        return ("badge-pro", "Pro")
    if t["paid_price_usd"] <= 13:
        return ("badge-budget", "Budget")
    return ("badge-popular", "Popular")


def _yes_no(b):
    return '<span class="yes">✓</span>' if b else '<span class="no">✗</span>'


def emit_best(persona, category, tools, slug):
    title = f"Best {category['label']} for {persona['label']} in 2026"
    picks = tools[:5]
    names_short = ", ".join(t["name"] for t in picks)
    description = (
        f"{names_short} — head-to-head for {persona['label']} who want to ship "
        f"without enterprise overhead."
    )

    top = picks[0]

    # at-a-glance table with badges
    rows = ["| Tool | Free tier | Starting price | Best for | Open source |",
            "|---|---|---|---|---|"]
    for i, t in enumerate(picks):
        cls, label = _badge_for_tool(t, i)
        price = "$0" if t["paid_price_usd"] == 0 else f"${t['paid_price_usd']}/mo"
        free = _yes_no(t["starting_price_usd"] == 0)
        oss = _yes_no(t.get("open_source"))
        best_for = (t.get("best_for") or ["—"])[0]
        rows.append(
            f"| **[{t['name']}]({t['homepage']})** "
            f'<span class="badge {cls}">{label}</span> '
            f"| {free} {t['free_tier']} | {price} | {best_for} | {oss} |"
        )

    # tool cards + pros/cons per tool
    cards = []
    for i, t in enumerate(picks):
        cls, label = _badge_for_tool(t, i)
        logo_cls = _LOGO_CLASSES[i % len(_LOGO_CLASSES)]
        initial = t["name"][0].upper()
        price = "Free forever" if t["paid_price_usd"] == 0 else f"From ${t['paid_price_usd']}/mo"
        free_pill = f"🎁 {t['free_tier']}" if t["starting_price_usd"] == 0 else "💰 paid only"
        platform_pill = f"🌐 {t.get('platform', '—').split(',')[0]}"
        pros_li = "\n".join(f"      <li>{x}</li>" for x in t.get("pros", []))
        cons_li = "\n".join(f"      <li>{x}</li>" for x in t.get("cons", []))
        intro = (
            f"The default recommendation for {persona['label'].lower()}. "
            f"{(t.get('best_for') or ['Solid pick'])[0].capitalize()}."
            if i == 0
            else f"{(t.get('best_for') or ['Solid pick for'])[0].capitalize()} — "
                 f"another option in the {category['label']} space."
        )
        cards.append(f"""<div class="tool-card">
  <div class="logo {logo_cls}">{initial}</div>
  <div class="info">
    <div class="info-top"><h3>{t['name']}</h3><span class="badge {cls}">{label}</span></div>
    <p>{intro}</p>
    <div class="stats">
      <span>💰 {price}</span>
      <span>{free_pill}</span>
      <span>{platform_pill}</span>
    </div>
  </div>
  <a href="{t['homepage']}" class="cta">Try {t['name']} →</a>
</div>

<div class="pros-cons">
  <div class="pros">
    <h4>✓ Strengths</h4>
    <ul>
{pros_li or '      <li>Solid all-rounder</li>'}
    </ul>
  </div>
  <div class="cons">
    <h4>✗ Trade-offs</h4>
    <ul>
{cons_li or '      <li>Some workflows need a paid upgrade</li>'}
    </ul>
  </div>
</div>
""")

    # decision tree
    decision_lines = []
    for t in picks:
        bf = (t.get("best_for") or ["broad fit"])[0]
        decision_lines.append(
            f"- **You want {bf}** → [{t['name']}]({t['homepage']})."
        )

    # quickpick
    quickpick = f"""<div class="quickpick">
  <div class="quickpick-icon">🛠️</div>
  <div class="quickpick-content">
    <h4>Quick pick: <a href="{top['homepage']}">{top['name']}</a></h4>
    <p>Best for 90% of {persona['label'].lower()} in 2026. {top['free_tier']}. Skip the comparison if you want to ship fast — sign up here.</p>
  </div>
</div>"""

    fm = (
        "---\n"
        f"slug: {slug}\n"
        f"title: \"{title}\"\n"
        f"description: \"{description}\"\n"
        f"persona: {persona['id']}\n"
        f"persona_label: \"{persona['label']}\"\n"
        f"category: {category['id']}\n"
        f"pattern: list\n"
        f"updated: {dt.date.today().isoformat()}\n"
        "---\n\n"
    )
    body = (
        f"You ship alone. The last thing you want is a {category['label']} tool built for "
        f"enterprise teams. Below are the {len(picks)} I'd actually recommend to a {persona['label'].rstrip('s').lower()} "
        f"in 2026 — picked for honest pricing, real free tiers, and the ability to *grow with your work*.\n\n"
        + quickpick + "\n\n"
        "## At a glance\n\n" + "\n".join(rows) + "\n\n"
        "## The contenders, ranked\n\n"
        + "\n---\n\n".join(cards) + "\n"
        "## How to choose in under 60 seconds\n\n"
        + "\n".join(decision_lines) + "\n\n"
        "## Honest disclosure\n\n"
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
    description = (
        f"{a['name']} vs {b['name']} head-to-head. Free tiers, pricing, ownership — "
        f"the honest call for {category.replace('-', ' ')} in 2026."
    )

    def yn(b_val):
        return _yes_no(b_val)
    def price_str(t):
        return "Free" if t["paid_price_usd"] == 0 else f"${t['paid_price_usd']}/mo"

    a_cls, a_label = _badge_for_tool(a, 0)
    b_cls, b_label = _badge_for_tool(b, 1)

    quickpick = f"""<div class="quickpick">
  <div class="quickpick-icon">⚖️</div>
  <div class="quickpick-content">
    <h4>Quick pick: <a href="{a['homepage']}">{a['name']}</a> for {(a.get('best_for') or ['most users'])[0]}, <a href="{b['homepage']}">{b['name']}</a> for {(b.get('best_for') or ['specialists'])[0]}</h4>
    <p>Both work in 2026. The right pick depends on whether you value {(a.get('pros') or [''])[0].lower() or 'simplicity'} (pick {a['name']}) or {(b.get('pros') or [''])[0].lower() or 'control'} (pick {b['name']}).</p>
  </div>
</div>"""

    table = [
        f"| | {a['name']} | {b['name']} |",
        "|---|---|---|",
        f"| Free tier | {yn(a['starting_price_usd'] == 0)} {a['free_tier']} | {yn(b['starting_price_usd'] == 0)} {b['free_tier']} |",
        f"| Starting paid | {price_str(a)} | {price_str(b)} |",
        f"| Open source | {yn(a.get('open_source'))} | {yn(b.get('open_source'))} |",
        f"| Platform | {a.get('platform','—').split(',')[0]} | {b.get('platform','—').split(',')[0]} |",
        f"| Best for | {(a.get('best_for') or ['—'])[0]} | {(b.get('best_for') or ['—'])[0]} |",
    ]

    def card(t, idx, cls, label):
        logo_cls = _LOGO_CLASSES[idx % len(_LOGO_CLASSES)]
        initial = t["name"][0].upper()
        price = "Free forever" if t["paid_price_usd"] == 0 else f"From ${t['paid_price_usd']}/mo"
        pros_li = "\n".join(f"      <li>{x}</li>" for x in t.get("pros", []))
        cons_li = "\n".join(f"      <li>{x}</li>" for x in t.get("cons", []))
        return f"""<div class="tool-card">
  <div class="logo {logo_cls}">{initial}</div>
  <div class="info">
    <div class="info-top"><h3>{t['name']}</h3><span class="badge {cls}">{label}</span></div>
    <p>{(t.get('best_for') or ['A solid option'])[0].capitalize()}. {t['free_tier']}.</p>
    <div class="stats">
      <span>💰 {price}</span>
      <span>🌐 {t.get('platform', '—').split(',')[0]}</span>
      <span>{'🆓 Open source' if t.get('open_source') else '🔒 Proprietary'}</span>
    </div>
  </div>
  <a href="{t['homepage']}" class="cta">Try {t['name']} →</a>
</div>

<div class="pros-cons">
  <div class="pros">
    <h4>✓ {t['name']} strengths</h4>
    <ul>
{pros_li or '      <li>Solid all-rounder</li>'}
    </ul>
  </div>
  <div class="cons">
    <h4>✗ {t['name']} trade-offs</h4>
    <ul>
{cons_li or '      <li>Some workflows need workarounds</li>'}
    </ul>
  </div>
</div>"""

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
        f"Both serve {category.replace('-', ' ')} workflows in 2026 — but they differ on pricing, ownership, "
        "and target audience. Here's the honest call.\n\n"
        + quickpick + "\n\n"
        "## At a glance\n\n" + "\n".join(table) + "\n\n"
        "## The contenders\n\n"
        + card(a, 0, a_cls, a_label) + "\n\n---\n\n"
        + card(b, 1, b_cls, b_label) + "\n\n"
        "## How to choose\n\n"
        f"- **Pick [{a['name']}]({a['homepage']})** if you value: " + ", ".join((a.get("best_for") or ["broad fit"])) + ".\n"
        f"- **Pick [{b['name']}]({b['homepage']})** if you value: " + ", ".join((b.get("best_for") or ["broad fit"])) + ".\n\n"
        "If you're starting from zero, both have free tiers — try one for 30 days, "
        "see if it fits your workflow before committing further.\n\n"
        "## Honest disclosure\n\n"
        "Links may be affiliate. Pricing numbers above are publicly listed as of 2026. "
        "We only compare tools we'd use ourselves.\n"
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
    description = (
        f"{target['name']}'s ${target['paid_price_usd']}/mo not in the budget? "
        f"Here are the genuinely-free alternatives that work in 2026."
    )
    top_alt = alts[0]

    quickpick = f"""<div class="quickpick">
  <div class="quickpick-icon">🆓</div>
  <div class="quickpick-content">
    <h4>Quick pick: <a href="{top_alt['homepage']}">{top_alt['name']}</a></h4>
    <p>The closest free tool to {target['name']} for most workflows. {top_alt['free_tier']}. {('Open source' if top_alt.get('open_source') else 'Free for personal use')} — your data outlives any platform.</p>
  </div>
</div>"""

    rows = ["| Tool | License | Platform | Best for |", "|---|---|---|---|"]
    for i, t in enumerate(alts):
        cls, label = _badge_for_tool(t, i)
        license_str = "Open source" if t.get("open_source") else "Free (proprietary)"
        bf = (t.get("best_for") or ["—"])[0]
        rows.append(
            f"| **[{t['name']}]({t['homepage']})** "
            f'<span class="badge {cls}">{label}</span> '
            f"| {license_str} | {t.get('platform','—').split(',')[0]} | {bf} |"
        )

    cards = []
    for i, t in enumerate(alts):
        cls, label = _badge_for_tool(t, i)
        logo_cls = _LOGO_CLASSES[i % len(_LOGO_CLASSES)]
        initial = t["name"][0].upper()
        pros_li = "\n".join(f"      <li>{x}</li>" for x in t.get("pros", []))
        cons_li = "\n".join(f"      <li>{x}</li>" for x in t.get("cons", []))
        intro_blurb = (t.get("best_for") or ["A solid free alternative"])[0].capitalize()
        cards.append(f"""<div class="tool-card">
  <div class="logo {logo_cls}">{initial}</div>
  <div class="info">
    <div class="info-top"><h3>{t['name']}</h3><span class="badge {cls}">{label}</span></div>
    <p>{intro_blurb}. {t['free_tier']}.</p>
    <div class="stats">
      <span>💰 Free</span>
      <span>🌐 {t.get('platform', '—').split(',')[0]}</span>
      <span>{'🆓 Open source' if t.get('open_source') else '🔒 Proprietary'}</span>
    </div>
  </div>
  <a href="{t['homepage']}" class="cta">Try {t['name']} →</a>
</div>

<div class="pros-cons">
  <div class="pros">
    <h4>✓ Why it works as a {target['name']} alternative</h4>
    <ul>
{pros_li or '      <li>Covers the core workflow</li>'}
    </ul>
  </div>
  <div class="cons">
    <h4>✗ Where it falls short</h4>
    <ul>
{cons_li or '      <li>You may outgrow it for advanced features</li>'}
    </ul>
  </div>
</div>""")

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
        f"If that's not in the budget yet — or you specifically want open source — here are "
        f"the genuinely-free alternatives that work in 2026.\n\n"
        + quickpick + "\n\n"
        "## At a glance\n\n" + "\n".join(rows) + "\n\n"
        "## The contenders\n\n"
        + "\n\n---\n\n".join(cards) + "\n\n"
        f"## When you should just pay for {target['name']}\n\n"
        f"If you're already making money from your work and {target['name']} would save "
        "you 2+ hours/week, the math says pay for it. Free alternatives are right when "
        "you're validating an idea, learning the craft, or specifically value open-source "
        "insurance.\n\n"
        "## Honest disclosure\n\n"
        "Links may be affiliate. The free alternatives above are free for personal use. "
        "We only compare tools we'd use ourselves.\n"
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
