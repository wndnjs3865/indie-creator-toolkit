#!/usr/bin/env python3
"""
Indie Creator Toolkit — static site builder.

Reads:
  content/*.md      (frontmatter + markdown body)
  data/seed-tools.json
  data/affiliates.json
  templates/*.html.j2

Writes:
  site/index.html
  site/{slug}/index.html
  site/sitemap.xml
  site/robots.txt
"""
import json
import os
import re
import sys
import datetime as dt
from pathlib import Path

import yaml
import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
DATA = ROOT / "data"
OUT = ROOT / "site"

GH_USER = os.environ.get("GH_USER", "USER")
SITE_BASE = os.environ.get("SITE_BASE", f"https://{GH_USER}.github.io/indie-creator-toolkit")


def load_data():
    with open(DATA / "seed-tools.json") as f:
        tools = json.load(f)["tools"]
    with open(DATA / "affiliates.json") as f:
        affiliates = json.load(f)
    return tools, affiliates


def parse_frontmatter(text: str):
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm = yaml.safe_load(parts[1]) or {}
    return fm, parts[2].strip()


def render_affiliates(body: str, affiliates: dict) -> str:
    """Replace {AMAZON_AFF_US} etc. tokens in body with affiliate IDs.
    Tokens missing → leave blank (bare URL is still a working link)."""
    def replace_token(match):
        token = match.group(0).strip("{}")
        flat = []
        def flatten(d, prefix=""):
            for k, v in d.items():
                if isinstance(v, dict):
                    flatten(v, prefix + k + ".")
                else:
                    flat.append((k, v))
        flatten(affiliates)
        for k, v in flat:
            if v and token == k.upper():
                return v
        return ""
    return re.sub(r"\{[A-Z_]+\}", replace_token, body)


def pick_related(current_meta, all_meta, max_n=4):
    """Find pages with same persona OR same category, excluding self."""
    out = []
    for m in all_meta:
        if m["slug"] == current_meta["slug"]:
            continue
        score = 0
        if m.get("persona") == current_meta.get("persona"):
            score += 2
        if m.get("category") == current_meta.get("category"):
            score += 1
        if score > 0:
            out.append((score, m))
    out.sort(key=lambda x: -x[0])
    return [m for _, m in out[:max_n]]


def build():
    OUT.mkdir(exist_ok=True)
    tools, affiliates = load_data()
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]))

    # Pass 1: parse all pages, collect metadata
    all_pages = []
    for md_file in sorted(CONTENT.glob("*.md")):
        with open(md_file) as f:
            raw = f.read()
        fm, body_md = parse_frontmatter(raw)
        slug = fm.get("slug") or md_file.stem
        body_md = render_affiliates(body_md, affiliates)
        all_pages.append({
            "slug": slug,
            "title": fm.get("title", slug.replace("-", " ").title()),
            "description": fm.get("description", ""),
            "persona": fm.get("persona", ""),
            "persona_label": fm.get("persona_label", fm.get("persona", "")),
            "category": fm.get("category", ""),
            "pattern": fm.get("pattern", "best"),
            "updated": fm.get("updated", dt.date.today().isoformat()),
            "body_md": body_md,
            "url": f"{slug}/",
        })

    # Pass 2: render each
    for p in all_pages:
        related = pick_related(p, all_pages)
        body_html = markdown.markdown(p["body_md"], extensions=["tables", "fenced_code", "toc"])
        canonical = f"{SITE_BASE}/{p['slug']}/"
        word_count = len(re.findall(r"\w+", p["body_md"]))

        tpl = env.get_template("base.html.j2")
        html = tpl.render(
            title=p["title"], description=p["description"], canonical=canonical,
            updated=p["updated"], persona_label=p["persona_label"], persona=p["persona"],
            word_count=word_count, body=body_html, gh_user=GH_USER,
            site_base=SITE_BASE, related=related,
        )
        out_dir = OUT / p["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(html, encoding="utf-8")

    # Index — group by persona
    personas_map = {}
    for p in all_pages:
        key = p["persona"] or "general"
        personas_map.setdefault(key, {
            "id": key,
            "label": p["persona_label"] or "General",
            "pages": [],
        })["pages"].append(p)
    # Sort personas by name; comparisons & free-alts last
    def persona_sort(item):
        k = item[0]
        if k in ("comparison", "free-alternatives"): return (1, k)
        return (0, k)
    personas_list = [v for _, v in sorted(personas_map.items(), key=persona_sort)]
    for v in personas_list:
        v["pages"].sort(key=lambda x: x["title"])

    idx_tpl = env.get_template("index.html.j2")
    (OUT / "index.html").write_text(idx_tpl.render(
        personas=personas_list, canonical=SITE_BASE + "/",
        total_pages=len(all_pages),
        updated=dt.date.today().isoformat(),
    ), encoding="utf-8")

    # sitemap.xml
    urls = [SITE_BASE + "/"] + [f"{SITE_BASE}/{p['slug']}/" for p in all_pages]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append(f"<url><loc>{u}</loc><lastmod>{dt.date.today().isoformat()}</lastmod></url>")
    sm.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")

    # robots.txt
    (OUT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_BASE}/sitemap.xml\n",
        encoding="utf-8")

    print(f"[build] {len(all_pages)} pages → {OUT}")


if __name__ == "__main__":
    build()
