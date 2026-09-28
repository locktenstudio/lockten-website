#!/usr/bin/env python3
"""Material Monitor page pictures: a shots folder in, WebP files and pin positions out.

The Material Monitor product page (materialmonitor.html) shows real console and
field app pictures taken from a sample company, with numbered pins placed on
them. The pictures come from the product repo's `scripts/marketing_shots.py`,
which writes a shots folder like this:

    console/<page>.png                 1440 x 900 viewport pictures at 2x
    console/<page>.anchors.json        CSS-pixel rectangles of things a pin can point at
    console/full/<page>.png            the whole page at 2x
    email/morning.png + .html + .anchors.json
    app/<screen>.png (+ .anchors.json) 390 x 844 phone pictures at 3x

This script reads that folder, frames each figure the page uses, writes WebP
files at two widths (1x and 2x of the displayed size) into
assets/screens/materialmonitor/, and works out every pin as a percentage of
the picture from the anchors, so a pin holds its place at any width.

    python scripts/mm_site_images.py <shots-folder>            convert and print
    python scripts/mm_site_images.py <shots-folder> --apply    also rewrite the MM-FIG blocks in materialmonitor.html
    python scripts/mm_site_images.py <shots-folder> --dry-run  print only, write nothing

Swapping in a new set of pictures is one run with --apply. Without --apply,
paste each printed block over the matching MM-FIG block in the page.

How a pin is placed: each pin names an anchor and a spot on its rectangle
(`left` means just outside its left edge, `top-right` its top right corner,
and so on; see SPOTS). The script writes the anchor point as percentages
(--xN, --yN) and the push away from the rectangle in screen pixels (--dxN,
--dyN), because a 28px pin is 28 screen pixels at every width while the
picture scales. The page's CSS places pins, leader lines and labels from
those four numbers.

How a console figure is framed: the viewport pictures scroll with the page but
the console's navigation bar stays at the top, so any view can be rebuilt from
the full-page picture: the bar, then the page from the chosen scroll offset.
A frame names the anchor to put near the top and the height of the view; if a
pin's anchor does not fit, the script tops the frame on the pins instead and
says which pins still fall outside (the page then hides those pins).

Needs Pillow with WebP. The morning email's first line has no anchor in the
shots, so the script measures it from email/morning.html with Playwright and
the local Chrome (see CHROME below); that step is skipped with a warning if
Playwright is missing.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "assets" / "screens" / "materialmonitor"
OUT_URL = "assets/screens/materialmonitor"
PAGE = REPO / "materialmonitor.html"

QUALITY = 82          # WebP quality to start from
MIN_QUALITY = 66      # the lowest it will go to meet a size budget
BUDGET_HERO = 250_000  # bytes, the hero at 2x
BUDGET_OTHER = 200_000  # bytes, every other file

# How far a pin sits from the edge of what it points at, in screen pixels:
# the pin is 28px with a 2px ring, so 18px leaves a hair of space.
PUSH = 18

# Where on an anchor rectangle a pin goes: (fx, fy, push_x, push_y).
# fx and fy are fractions of the rectangle; push is in units of PUSH.
SPOTS = {
    "center": (0.5, 0.5, 0, 0),
    "left": (0.0, 0.5, -1, 0),
    "right": (1.0, 0.5, 1, 0),
    "top": (0.5, 0.0, 0, -1),
    "bottom": (0.5, 1.0, 0, 1),
    "top-left": (0.0, 0.0, 0, 0),
    "top-right": (1.0, 0.0, 0, 0),
    "inside-left": (0.0, 0.5, 1, 0),
    "inside-right": (1.0, 0.5, -1, 0),
}

CHROME_GLOB = os.path.expanduser("~/.cache/puppeteer/chrome/*/chrome-win64/chrome.exe")

# ---------------------------------------------------------------------------
# The figures on the page. Each id matches an MM-FIG block in the page.
#   source: "console:<page>" (framed from console/full/<page>.png with
#           console/<page>.anchors.json), "email", or "app:<screen>".
#   frame:  console only. top/prefer_top name an anchor (or "page" for the
#           top of the page), pad_top is the space above it; height is the
#           view height, or bottom lists anchors to end below (+ pad_bottom).
#   crop:   email only, where the picture ends.
#   pins:   (anchor, spot) in number order.
# ---------------------------------------------------------------------------
FIGURES = [
    {
        "id": "hero",
        "source": "console:dashboard",
        "frame": {"top": "jobs_heading", "pad_top": 12,
                  "bottom": ["follow_up_heading", "draft_an_email_button"], "pad_bottom": 18},
        "out": "mm-hero-dashboard",
        "widths": [960, 1920],
        "budget": BUDGET_HERO,
        "eager": True,
        "sizes": "(min-width: 1320px) 954px, (min-width: 1100px) calc(100vw - 366px), calc(100vw - 48px)",
        "alt": ("The Material Monitor dashboard with sample data: four job cards, the materials that "
                "need ordering with their order-by dates, this week's deliveries and the start of the "
                "follow-up list. A sample company, not a real job."),
        "pins": [("first_job_card", "left"), ("first_order_by_date", "left"),
                 ("deliveries_heading", "left"), ("follow_up_heading", "left")],
    },
    {
        "id": "hero-phone",
        "source": "app:home",
        "out": "mm-app-home",
        "widths": [240, 480],
        "eager": True,
        "sizes": "(min-width: 1100px) 210px, 26vw",
        "alt": ("The field app's home screen with sample data: receive materials, look up a material, "
                "report a problem and the expected deliveries by day."),
    },
    {
        "id": "tour-1",
        "source": "console:dashboard",
        "frame": {"prefer_top": "follow_up_heading", "pad_top": 24, "height": 900},
        "out": "mm-tour-dashboard",
        "widths": [880, 1760],
        "sizes": "(min-width: 1100px) 832px, (min-width: 928px) 880px, calc(100vw - 48px)",
        "alt": ("The dashboard's follow-up list with sample data: orders that have gone quiet, each "
                "with the reason and the rep, and the button that drafts the emails. A sample company."),
        "pins": [("search_box", "bottom"), ("first_follow_up_reason", "left"),
                 ("draft_an_email_button", "right")],
    },
    {
        "id": "tour-2",
        "source": "console:job-board",
        "frame": {"prefer_top": "page", "height": 900},
        "out": "mm-tour-job",
        "widths": [880, 1760],
        "sizes": "(min-width: 1100px) 832px, (min-width: 928px) 880px, calc(100vw - 48px)",
        "alt": ("One job's list with sample data: the box for bringing in a selections export, then the "
                "tile and appliance groups with each material's vendor, status and dates. A sample company."),
        "pins": [("first_section_heading", "left"), ("status_chip_ordered", "top"),
                 ("update_the_list_upload", "left")],
    },
    {
        "id": "tour-3",
        "source": "console:material",
        "frame": {"prefer_top": "page", "pad_top": 0, "height": 900, "fallback_pad": 110},
        "out": "mm-tour-material",
        "widths": [880, 1760],
        "sizes": "(min-width: 1100px) 832px, (min-width: 928px) 880px, calc(100vw - 48px)",
        "alt": ("A material's page with sample data: its lead time and order-by date, the vendor and "
                "the rep with an email address and a phone number. A sample company."),
        "pins": [("vendor_and_rep", "left"), ("order_by_date", "left"), ("history_list", "left")],
    },
    {
        "id": "tour-4",
        "source": "console:updates-proposals",
        "frame": {"prefer_top": "proposals_heading", "pad_top": 24, "height": 900},
        "out": "mm-tour-updates",
        "widths": [880, 1760],
        "sizes": "(min-width: 1100px) 832px, (min-width: 928px) 880px, calc(100vw - 48px)",
        "alt": ("The Updates page with sample data: vendor updates waiting for an OK, each with the "
                "proposed change, the vendor's own sentence and Confirm, Edit and Dismiss. A sample company."),
        "pins": [("proposed_change", "left"), ("quoted_vendor_sentence", "left"),
                 ("confirm_button", "right")],
    },
    {
        "id": "tour-5",
        "source": "console:follow-up",
        "frame": {"prefer_top": "title", "pad_top": 22, "height": 900},
        "out": "mm-tour-follow-up",
        "widths": [880, 1760],
        "sizes": "(min-width: 1100px) 832px, (min-width: 928px) 880px, calc(100vw - 48px)",
        "alt": ("A follow-up email written for one rep with sample data: the open items with model "
                "numbers, quantities and order dates, and the button that opens it in Outlook. A sample company."),
        "pins": [("first_draft_vendor_and_rep", "left"), ("first_draft_body", "left"),
                 ("open_in_outlook", "left")],
    },
    {
        "id": "email",
        "source": "email",
        "crop": {"bottom": "section_4", "pad_bottom": -14},
        "measure": {"first_line": "td p"},
        "out": "mm-morning-email",
        "widths": [520, 1040],
        "sizes": "(min-width: 900px) 520px, calc(100vw - 48px)",
        "alt": ("The morning email with sample data: the updates waiting for an OK, the materials that "
                "need ordering, the problems flagged from the field and what arrived. A sample company."),
        "pins": [("first_line", "right"), ("section_1", "left"), ("section_2", "left"),
                 ("section_3", "left")],
    },
    {
        "id": "field-receive",
        "source": "app:receive-list",
        "out": "mm-app-receive",
        "widths": [280, 560],
        "sizes": "(min-width: 900px) 280px, 70vw",
        "alt": ("The field app's receiving screen with sample data: what came in at one job, with a "
                "shower valve ticked and marked in good condition."),
    },
    {
        "id": "field-material",
        "source": "app:material",
        "out": "mm-app-material",
        "widths": [280, 560],
        "sizes": "(min-width: 900px) 280px, 70vw",
        "alt": ("A material in the field app with sample data: shipped and due Wednesday, with its tracking "
                "number, maker, model, vendor and rep. Buttons below email the rep or receive it."),
    },
    {
        "id": "field-problem",
        "source": "app:tell-the-office",
        "out": "mm-app-problem",
        "widths": [280, 560],
        "sizes": "(min-width: 900px) 280px, 70vw",
        "alt": ("The field app's report a problem screen with sample data: a powder room sink marked "
                "damaged, with a sentence for the office."),
    },
]


def warn(msg: str) -> None:
    print(f"  ! {msg}", file=sys.stderr)


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def rect(r: dict) -> tuple[float, float, float, float]:
    return float(r["x"]), float(r["y"]), float(r["w"]), float(r["h"])


def measure_html(html: Path, width: int, selectors: dict[str, str]) -> dict[str, tuple]:
    """Measure elements in an HTML picture source with headless Chrome."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        warn("Playwright is not installed, so the email's measured anchors are skipped.")
        return {}
    exes = sorted(glob.glob(CHROME_GLOB))
    kwargs = {"headless": True}
    if exes:
        kwargs["executable_path"] = exes[-1]
    found = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**kwargs)
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.goto(html.resolve().as_uri())
        for name, sel in selectors.items():
            box = page.evaluate(
                "(s) => { const e = document.querySelector(s); if (!e) return null;"
                " const b = e.getBoundingClientRect(); return [b.x, b.y, b.width, b.height]; }",
                sel,
            )
            if box:
                found[name] = tuple(round(v, 1) for v in box)
            else:
                warn(f"{html.name}: nothing matches {sel!r} for {name}")
        browser.close()
    return found


class Frame:
    """A picture to write plus a way to find each anchor inside it (CSS px)."""

    def __init__(self, image: Image.Image, scale: float, css_w: float, css_h: float, desc: str):
        self.image = image          # full-resolution picture for this figure
        self.scale = scale          # image pixels per CSS pixel
        self.css_w = css_w
        self.css_h = css_h
        self.desc = desc
        self.anchor = {}            # name -> (x, y, w, h) in this frame's CSS px


def frame_console(shots: Path, fig: dict) -> Frame:
    page = fig["source"].split(":", 1)[1]
    anchors_path = shots / "console" / f"{page}.anchors.json"
    data = load_json(anchors_path)
    full_rel = data.get("full_page_picture") or f"console/full/{page}.png"
    full = Image.open(shots / full_rel).convert("RGB")
    scale = float(data.get("device_scale_factor", 2))
    vw = float(data["viewport"]["width"])
    page_h = float(data["full_page"]["height"])
    anchors = {k: rect(v["full_page"]) for k, v in data["anchors"].items()
               if isinstance(v, dict) and v.get("full_page")}
    nav = anchors.get("nav_updates")
    nav_h = (nav[1] + nav[3]) if nav else 62.0

    spec = fig["frame"]
    pins = [p[0] for p in fig.get("pins", [])]
    missing = [p for p in pins if p not in anchors]
    for m in missing:
        warn(f"{fig['id']}: anchor {m!r} is not in {anchors_path.name}")

    def top_for(name: str, pad: float) -> float:
        if name == "page":
            return 0.0
        return anchors[name][1] - nav_h - pad

    def fits(s: float, h: float, name: str) -> bool:
        x, y, w, hh = anchors[name]
        if y + hh <= nav_h:            # in the navigation bar, always in view
            return True
        return y - s >= nav_h - 1 and y - s + hh <= h + 1

    if "top" in spec:
        s = top_for(spec["top"], spec.get("pad_top", 0))
    else:
        s = top_for(spec.get("prefer_top", "page"), spec.get("pad_top", 0))
    s = max(0.0, s)
    if "height" in spec:
        h = float(spec["height"])
    else:
        bottom = max(anchors[b][1] + anchors[b][3] for b in spec["bottom"])
        h = bottom + spec.get("pad_bottom", 0) - s
    present = [p for p in pins if p in anchors]
    if "prefer_top" in spec and not all(fits(s, h, p) for p in present):
        body = [anchors[p] for p in present if anchors[p][1] + anchors[p][3] > nav_h]
        pad = spec.get("fallback_pad", 24)
        s = max(0.0, min(r[1] for r in body) - nav_h - pad)
        warn(f"{fig['id']}: the pins do not all fit below {spec['prefer_top']!r}; "
             f"framed on the pins instead (scroll {s:.0f})")
    s = min(s, max(0.0, page_h - h))
    s = round(s)
    h = round(h)

    px = lambda v: int(round(v * scale))
    img = Image.new("RGB", (px(vw), px(h)))
    img.paste(full.crop((0, 0, px(vw), px(nav_h))), (0, 0))
    img.paste(full.crop((0, px(s + nav_h), px(vw), px(s + h))), (0, px(nav_h)))
    fr = Frame(img, scale, vw, h, f"{full_rel}, a {vw:.0f} x {h} view at scroll {s}, navigation bar kept")
    for name, (x, y, w, hh) in anchors.items():
        if y + hh <= nav_h:
            fr.anchor[name] = (x, y, w, hh)
        elif y - s >= nav_h - 1 and y - s + hh <= h + 1:
            fr.anchor[name] = (x, y - s, w, hh)
    return fr


def frame_email(shots: Path, fig: dict) -> Frame:
    data = load_json(shots / "email" / "morning.anchors.json")
    pic = Image.open(shots / data.get("picture", "email/morning.png")).convert("RGB")
    scale = float(data.get("device_scale_factor", 2))
    w = float(data.get("width", pic.width / scale))
    anchors = {k: rect(v) for k, v in data["anchors"].items()}
    html = shots / "email" / "morning.html"
    if fig.get("measure") and html.exists():
        anchors.update(measure_html(html, int(w), fig["measure"]))
    crop = fig.get("crop", {})
    h = float(data.get("height", pic.height / scale))
    if crop.get("bottom") in anchors:
        h = anchors[crop["bottom"]][1] + crop.get("pad_bottom", 0)
    elif crop.get("bottom"):
        warn(f"email: crop anchor {crop['bottom']!r} missing; the whole email is used")
    h = round(h)
    img = pic.crop((0, 0, pic.width, int(round(h * scale))))
    fr = Frame(img, scale, w, h, f"{data.get('picture', 'email/morning.png')}, cropped to {w:.0f} x {h}")
    fr.anchor = {k: v for k, v in anchors.items() if v[1] + v[3] <= h}
    return fr


def frame_app(shots: Path, fig: dict) -> Frame:
    screen = fig["source"].split(":", 1)[1]
    pic = Image.open(shots / "app" / f"{screen}.png").convert("RGB")
    apath = shots / "app" / f"{screen}.anchors.json"
    scale = 3.0
    anchors = {}
    if apath.exists():
        data = load_json(apath)
        scale = float(data.get("device_scale_factor", 3))
        anchors = {k: rect(v) for k, v in data["anchors"].items()}
    fr = Frame(pic, scale, pic.width / scale, pic.height / scale, f"app/{screen}.png")
    fr.anchor = anchors
    return fr


def save_webp(img: Image.Image, path: Path, width: int, budget: int, dry: bool) -> tuple[int, int, int]:
    h = round(img.height * width / img.width)
    small = img.resize((width, h), Image.LANCZOS) if width != img.width else img
    q = QUALITY
    while True:
        from io import BytesIO
        buf = BytesIO()
        small.save(buf, format="WEBP", quality=q, method=6)
        size = buf.tell()
        if size <= budget or q <= MIN_QUALITY:
            break
        q -= 4
    if size > budget:
        warn(f"{path.name} is {size / 1000:.0f} KB, over its {budget / 1000:.0f} KB budget even at quality {q}")
    if not dry:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(buf.getvalue())
    return size, q, h


def pin_numbers(fig: dict, fr: Frame) -> list[dict]:
    out = []
    for n, (name, spot) in enumerate(fig.get("pins", []), start=1):
        fx, fy, pxs, pys = SPOTS[spot]
        a = fr.anchor.get(name)
        if a is None:
            warn(f"{fig['id']}: pin {n} ({name}) is outside the picture; it is hidden on the page")
            out.append({"n": n, "name": name, "spot": spot, "hidden": True})
            continue
        x, y, w, h = a
        ax, ay = x + fx * w, y + fy * h
        out.append({
            "n": n, "name": name, "spot": spot, "hidden": False, "rect": a,
            "x": 100 * ax / fr.css_w, "y": 100 * ay / fr.css_h,
            "dx": pxs * PUSH, "dy": pys * PUSH,
        })
    return out


def block_for(fig: dict, fr: Frame, pins: list[dict], files: list[tuple[int, int]], shots_name: str) -> str:
    fid = fig["id"]
    lines = [f"<!-- MM-FIG {fid} START. Generated by scripts/mm_site_images.py from {shots_name}: {fr.desc}."]
    if pins:
        lines.append("     To move a pin, change its anchor or spot in the script and run it again; do not edit the numbers by hand.")
        for p in pins:
            if p["hidden"]:
                lines.append(f"     pin {p['n']}  {p['name']} ({p['spot']}): not in this picture, hidden")
            else:
                x, y, w, h = p["rect"]
                lines.append(
                    f"     pin {p['n']}  {p['name']} ({p['spot']}) box {x:.0f},{y:.0f} {w:.0f}x{h:.0f} of "
                    f"{fr.css_w:.0f}x{fr.css_h:.0f} -> left {p['x']:.3f}% top {p['y']:.3f}%, "
                    f"pushed {p['dx']}px {p['dy']}px")
    lines[-1] += " -->"
    w1, h1 = files[0]
    srcset = ", ".join(f"{OUT_URL}/{fig['out']}-{w}.webp {w}w" for w, _ in files)
    loading = 'fetchpriority="high"' if fig.get("eager") else 'loading="lazy"'
    img = (f'<img src="{OUT_URL}/{fig["out"]}-{w1}.webp" srcset="{srcset}" sizes="{fig["sizes"]}" '
           f'width="{w1}" height="{h1}" {loading} decoding="async" alt="{fig["alt"]}">')
    if pins:
        style = ";".join(
            f"--x{p['n']}:{p['x']:.3f}%;--y{p['n']}:{p['y']:.3f}%;--dx{p['n']}:{p['dx']}px;--dy{p['n']}:{p['dy']}px"
            for p in pins if not p["hidden"])
        hidden = " ".join(f"miss-{p['n']}" for p in pins if p["hidden"])
        cls = "shot" + (f" {hidden}" if hidden else "")
        lines.append(f'<div class="{cls}" style="{style}">')
        lines.append(f'<div class="pic">{img}')
    else:
        lines.append(img)
    lines.append(f"<!-- MM-FIG {fid} END -->")
    return "\n".join(lines)


def apply_blocks(blocks: dict[str, str]) -> None:
    html = PAGE.read_text(encoding="utf-8")
    for fid, block in blocks.items():
        pat = re.compile(r"<!-- MM-FIG " + re.escape(fid) + r" START.*?<!-- MM-FIG " + re.escape(fid) + r" END -->", re.S)
        if not pat.search(html):
            warn(f"{PAGE.name} has no MM-FIG {fid} block; paste it by hand")
            continue
        html = pat.sub(lambda m: block, html, count=1)
    PAGE.write_text(html, encoding="utf-8", newline="\n")
    print(f"Rewrote the MM-FIG blocks in {PAGE.name}.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("shots", type=Path, help="the shots folder (site-shots or site-shots-2)")
    ap.add_argument("--apply", action="store_true", help="rewrite the MM-FIG blocks in materialmonitor.html")
    ap.add_argument("--dry-run", action="store_true", help="print only, write no files")
    ap.add_argument("--only", nargs="*", help="figure ids to do (default: all)")
    args = ap.parse_args()
    shots = args.shots.resolve()
    if not (shots / "console").is_dir():
        print(f"{shots} does not look like a shots folder (no console/ inside).", file=sys.stderr)
        return 2

    blocks = {}
    total = {}
    for fig in FIGURES:
        if args.only and fig["id"] not in args.only:
            continue
        kind = fig["source"].split(":", 1)[0]
        fr = {"console": frame_console, "email": frame_email, "app": frame_app}[kind](shots, fig)
        pins = pin_numbers(fig, fr)
        files = []
        print(f"\n== {fig['id']}  ({fr.desc})")
        for w in fig["widths"]:
            path = OUT_DIR / f"{fig['out']}-{w}.webp"
            size, q, h = save_webp(fr.image, path, w, fig.get("budget", BUDGET_OTHER), args.dry_run)
            files.append((w, h))
            total[path.name] = size
            print(f"   {path.name:34s} {w} x {h}  {size / 1000:6.1f} KB  q{q}")
        for p in pins:
            if p["hidden"]:
                print(f"   pin {p['n']}  {p['name']:28s} OUTSIDE THE PICTURE (hidden)")
            else:
                print(f"   pin {p['n']}  {p['name']:28s} {p['spot']:12s} left {p['x']:7.3f}%  top {p['y']:7.3f}%"
                      f"  push {p['dx']:+d}px {p['dy']:+d}px")
        block = block_for(fig, fr, pins, files, shots.name)
        blocks[fig["id"]] = block
        print(block)

    print(f"\nTotal of the WebP files written: {sum(total.values()) / 1000:.0f} KB over {len(total)} files.")
    if args.apply and not args.dry_run:
        apply_blocks(blocks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
