#!/usr/bin/env python3
"""Render the guide's share image (assets/og/og-guide.png, 1200 x 630).

The card is the guide's own cover: the navy blueprint ground, the guide's title,
"Free guide, as of October 2026" and the plan-sheet cover drawing, which is read
straight out of guide.html so the two never drift. Run it again after the cover changes:

    python scripts/guide_og_image.py

It needs Playwright and a Chrome; it uses the puppeteer Chrome in ~/.cache when there
is one (Playwright's own Chromium does not start on some Windows machines).
"""

import glob
import html
import os
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAGE = REPO / "guide.html"
OUT = REPO / "assets" / "og" / "og-guide.png"

CARD = """<!DOCTYPE html><html><head><meta charset="utf-8">
<base href="{base}">
<link rel="stylesheet" href="styles.css">
<style>
html, body {{ margin: 0; width: 1200px; height: 630px; overflow: hidden; background: #0C1B38; }}
.card {{ position: relative; width: 1200px; height: 630px; overflow: hidden; background-color: #0C1B38;
        background-image: linear-gradient(rgba(255,255,255,.06) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.06) 1px, transparent 1px);
        background-size: 32px 32px; }}
.eyebrow {{ position: absolute; left: 72px; top: 82px; margin: 0; font-family: 'Geist Mono', monospace; font-size: 20px;
           letter-spacing: 0.14em; text-transform: uppercase; color: #A8CCEE; }}
h1 {{ position: absolute; left: 72px; top: 140px; width: 600px; margin: 0; font-family: 'Instrument Serif', Georgia, serif;
      font-weight: 400; font-size: 78px; line-height: 1.02; letter-spacing: -0.01em; color: #FFFFFF; }}
.rule {{ position: absolute; left: 72px; bottom: 112px; width: 560px; height: 1px; background: rgba(255,255,255,.22); }}
.foot {{ position: absolute; left: 72px; bottom: 66px; font-family: 'Geist Mono', monospace; font-size: 18px;
        letter-spacing: 0.12em; text-transform: uppercase; color: #C3D2E6; }}
.art {{ position: absolute; right: 60px; top: 120px; width: 470px; }}
.art svg {{ display: block; width: 100%; height: auto; }}
</style></head><body><div class="card">
<p class="eyebrow">Free guide, as of October 2026</p>
<h1>{title}</h1>
<div class="rule"></div>
<div class="foot">Lock Ten Studio &middot; lockten.ai/guide</div>
<div class="art">{art}</div>
</div></body></html>"""


def main() -> int:
    page = PAGE.read_text(encoding="utf-8")
    art = re.search(r'<div class="cover-art">(<svg.*?</svg>)</div>', page, re.S).group(1)
    title = re.search(r'<header class="cover">.*?<h1>(.*?)</h1>', page, re.S).group(1)
    card = CARD.format(base=REPO.as_uri() + "/", art=art, title=title)
    from playwright.sync_api import sync_playwright
    exes = sorted(glob.glob(os.path.expanduser("~/.cache/puppeteer/chrome/*/chrome-win64/chrome.exe")))
    kwargs = {"headless": True, **({"executable_path": exes[-1]} if exes else {})}
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "og.html"
        src.write_text(card, encoding="utf-8")
        with sync_playwright() as pw:
            browser = pw.chromium.launch(**kwargs)
            pg = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
            pg.goto(src.as_uri(), wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(OUT), clip={"x": 0, "y": 0, "width": 1200, "height": 630})
            browser.close()
    print(f"Wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size / 1000:.0f} KB).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
