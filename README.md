# Indie Creator Toolkit

> Software & tools comparisons for solo creators — writers, podcasters, indie game devs, illustrators, newsletter operators, screenwriters, musicians.

We compare free, freemium, and paid tools so creators don't waste money on bloated SaaS they don't need yet.

## Build locally
```bash
pip install --user markdown jinja2 pyyaml feedparser requests
python3 scripts/build.py
# Output in site/
```

## Workflows
- `.github/workflows/build.yml` — build & deploy on push
- `.github/workflows/daily-page.yml` — generate 1 new page daily
- `.github/workflows/weekly-refresh.yml` — refresh tool metadata weekly

## License
MIT (code) / All affiliate disclosures present in each post.
