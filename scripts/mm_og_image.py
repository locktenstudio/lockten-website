#!/usr/bin/env python3
"""Render the Material Monitor share image (assets/og/og-materialmonitor.png, 1200 x 630).

The card is the page's own identity: slate ground, the product lockup, the page's
headline with its copper italic line, and a crop of the dashboard picture the page
uses (assets/screens/materialmonitor/mm-hero-dashboard-2080.webp, sample data) in
the same plain browser frame. Run it again after the headline or the pictures change:

    python scripts/mm_og_image.py

It needs Playwright and a Chrome; it uses the puppeteer Chrome in ~/.cache when there
is one (Playwright's own Chromium does not start on some Windows machines).
"""

import glob
import os
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAGE = REPO / "materialmonitor.html"
OUT = REPO / "assets" / "og" / "og-materialmonitor.png"
SHOT = "assets/screens/materialmonitor/mm-hero-dashboard-2080.webp"

CARD = """<!DOCTYPE html><html><head><meta charset="utf-8">
<base href="{base}">
<link rel="stylesheet" href="styles.css">
<style>
html, body {{ margin: 0; width: 1200px; height: 630px; overflow: hidden; background: #1D232B; }}
.card {{ position: relative; width: 1200px; height: 630px; background: #1D232B; overflow: hidden; }}
.lock {{ position: absolute; left: 64px; top: 56px; display: flex; align-items: center; gap: 14px; }}
.lock svg {{ width: 50px; height: 50px; }}
.lock span {{ font-family: 'Instrument Serif', Georgia, serif; font-size: 36px; color: #EEF1F4; letter-spacing: -0.01em; }}
h1 {{ position: absolute; left: 64px; top: 150px; width: 520px; margin: 0; font-family: 'Instrument Serif', Georgia, serif;
      font-weight: 400; font-size: 64px; line-height: 1.04; letter-spacing: -0.02em; color: #FFFFFF; }}
h1 em {{ display: block; font-style: italic; color: #DE9A66; }}
.foot {{ position: absolute; left: 64px; bottom: 60px; font-family: 'Geist Mono', monospace; font-size: 17px;
        letter-spacing: 0.12em; text-transform: uppercase; color: #B6BCC5; }}
.rule {{ position: absolute; left: 64px; bottom: 102px; width: 44px; height: 2px; background: #C8763C; }}
.frame {{ position: absolute; left: 640px; top: 70px; width: 820px; border-radius: 14px 0 0 0; overflow: hidden;
          box-shadow: 0 30px 70px -24px rgba(0,0,0,0.7); }}
.bar {{ display: flex; align-items: center; gap: 8px; height: 34px; padding: 0 16px; background: #2A313A; }}
.bar i {{ width: 11px; height: 11px; border-radius: 50%; background: #58616D; }}
.bar b {{ margin-left: 90px; font: 400 15px 'Geist Mono', monospace; color: #AEB5BF; background: #1D232B; border-radius: 6px; padding: 3px 16px; }}
.frame img {{ display: block; width: 1040px; height: auto; margin-left: -8px; }}
.cap {{ position: absolute; left: 64px; bottom: 22px; font: 400 14px 'Geist Mono', monospace; color: #888F9C; letter-spacing: 0.04em; }}
</style></head><body><div class="card">
<div class="lock">{mark}<span>Material Monitor</span></div>
<h1>{headline}</h1>
<div class="rule"></div>
<div class="foot">Office console &middot; Field app</div>
<div class="frame"><div class="bar"><i></i><i></i><i></i><b>app.materialmonitor.app</b></div><img src="{shot}" alt=""></div>
<div class="cap">Sample company, not a real job.</div>
</div></body></html>"""


def main() -> int:
    page = PAGE.read_text(encoding="utf-8")
    mark = re.search(r'<a href="#top" class="mm-lockup">\s*(<svg.*?</svg>)', page, re.S).group(1)
    headline = re.search(r'<h1 class="hero-headline[^"]*">(.*?)</h1>', page, re.S).group(1)
    html = CARD.format(base=REPO.as_uri() + "/", mark=mark, headline=headline, shot=SHOT)
    from playwright.sync_api import sync_playwright
    exes = sorted(glob.glob(os.path.expanduser("~/.cache/puppeteer/chrome/*/chrome-win64/chrome.exe")))
    kwargs = {"headless": True, **({"executable_path": exes[-1]} if exes else {})}
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "og.html"
        src.write_text(html, encoding="utf-8")
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
