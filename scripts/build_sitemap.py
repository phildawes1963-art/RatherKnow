"""Generates frontend/public/sitemap.xml from docs/route_table.json (indexable routes only)."""
import json
import os
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(ROOT, "docs", "route_table.json")
OUT = os.path.join(ROOT, "frontend", "public", "sitemap.xml")

with open(TABLE, encoding="utf-8") as fh:
    table = json.load(fh)

base = table["site"]["base_url"]
today = date.today().isoformat()
paths = []
for route in table["routes"]:
    if not route.get("indexable"):
        continue
    if route.get("dynamic"):
        for slug in route.get("slugs", []):
            paths.append(route["path"].replace("{slug}", slug))
    else:
        paths.append(route["path"])

body = "\n".join(
    f"  <url><loc>{base}{p}</loc><lastmod>{today}</lastmod></url>" for p in paths
)
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>\n"
    )
print(f"wrote {len(paths)} urls to {OUT}")
