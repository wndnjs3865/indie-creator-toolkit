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
    Tokens missing → leave bare URL."""
    def replace_token(match):
        token = match.group(0)
        # Walk affiliate dict to find a matching value
        flat = []
        def flatten(d, prefix=""):
            for k, v in d.items():
                if isinstance(v, dict):
                    flatten(v, prefix + k + ".")
                else:
                    flat.append((k, v))
        flatten(affiliates)
        for k, v in flat:
            if v and token.strip("{}") == k.upper():
                return v
        return ""  # blank → no tracking, just bare URL
    return re.sub(r"\{[A-Z_]+\}", replace_token, body)


def build():
    OUT.mkdir(exist_ok=True)
    tools, affiliates = load_data()
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]))

    pages_index = []
    for md_file in sorted(CONTENT.glob("*.md")):
        with open(md_file) as f:
            raw = f.read()
        fm, body_md = parse_frontmatter(raw)
        slug = fm.get("slug") or md_file.stem
        title = fm.get("title", slug.replace("-", " ").title())
        description = fm.get("description", "")
        persona = fm.get("persona", "")
        persona_label = fm.get("persona_label", persona)
        updated = fm.get("updated", dt.date.today().isoformat())
        body_md = render_affiliates(body_md, affiliates)
        body_html = markdown.markdown(body_md, extensions=["tables", "fenced_code", "toc"])

        canonical = f"{SITE_BASE}/{slug}/"
        word_count = len(re.findall(r"\w+", body_md))

        tpl = env.get_template("base.html.j2")
        html = tpl.render(
            title=title, description=description, canonical=canonical,
            updated=updated, persona_label=persona_label,
            word_count=word_count, body=body_html, gh_user=GH_USER,
        )

        out_dir = OUT / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(html, encoding="utf-8")

        pages_index.append({
            "slug": slug, "title": title, "url": f"/{slug}/",
            "persona": persona, "persona_label": persona_label,
            "updated": updated,
        })

    # Group pages by persona for index
    personas_map = {}
    for p in pages_index:
        personas_map.setdefault(p["persona"] or "general", {
            "label": p["persona_label"] or "General",
            "pages": [],
        })["pages"].append(p)
    personas_list = [{"label": v["label"], "pages": v["pages"]}
                     for k, v in sorted(personas_map.items())]

    idx_tpl = env.get_template("index.html.j2")
    (OUT / "index.html").write_text(idx_tpl.render(
        personas=personas_list, canonical=SITE_BASE + "/",
        updated=dt.date.today().isoformat(),
    ), encoding="utf-8")

    # sitemap.xml
    urls = [SITE_BASE + "/"] + [f"{SITE_BASE}/{p['slug']}/" for p in pages_index]
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

    print(f"[build] {len(pages_index)} pages → {OUT}")


if __name__ == "__main__":
    build()
