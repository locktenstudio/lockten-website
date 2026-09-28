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

This script reads that folder, crops each figure the page uses, writes WebP
files at two widths (1x and 2x of the displayed size) into
assets/screens/materialmonitor/, and works out every pin as a percentage of
the cropped picture from the anchors, so a pin holds its place at any width.

    python scripts/mm_site_images.py <shots-folder>            convert and print
    python scripts/mm_site_images.py <shots-folder> --apply    also rewrite the MM-FIG blocks in materialmonitor.html
    python scripts/mm_site_images.py <shots-folder> --dry-run  print only, write nothing

Swapping in a new set of pictures is one run with --apply. Without --apply,
paste each printed block over the matching MM-FIG block in the page.

Crops. A console figure is a rectangle cut from the full-page picture, in the
page's CSS pixels: x0 to x1 across, y0 to y1 down (y1 can instead follow from
an aspect ratio, so every tour picture has the same shape). Each edge is a
number or (anchor, edge, offset), for example ("jobs_heading", "top", -20), so
a re-shoot that moves things down the page still crops the same content.
`nav: True` puts the console's navigation bar (which stays at the top of the
screen when the page scrolls) above the crop, cut to the same width. A figure
can have a "wide" crop and a "narrow" one; the narrow one is served under 700px
through <picture>, with its own pin positions.

A narrow crop can also be a "stack": two or more crops of the same page set one
above the other with a small gap, for a phone, when the things the pins point at
sit in columns too far apart to share one legible crop. "snap_x1": anchor moves a
crop's right edge left to the nearest clear column inside that anchor's rows, so
a cut line of text ends between words, and "fade": True softens that right edge
on the page.

`display` is how wide the crop shows at the 1440 layout (or at 390 for a
narrow crop). The script checks that the console's 17px body text comes out at
13px or more on a wide crop, and uses the scale to keep every pin, which is 28
screen pixels whatever the scale, inside its picture; a pin that does not fit
is hidden on the page and its number turns grey in the list.

Pins. Each pin names an anchor and a spot on its rectangle (`left` means just
outside its left edge, `top-right` its top right corner, and so on; see
SPOTS). The script writes the anchor point as percentages (--xN, --yN; --nxN,
--nyN for the narrow crop) and the push away from the rectangle in screen
pixels (--dxN, --dyN), because the pin keeps its size while the picture scales.

Needs Pillow with WebP. The morning email's first line has no anchor in the
shots, so the script measures it from email/morning.html with Playwright and
the local Chrome (see CHROME_GLOB); that step is skipped with a warning if
Playwright is missing.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "assets" / "screens" / "materialmonitor"
OUT_URL = "assets/screens/materialmonitor"
PAGE = REPO / "materialmonitor.html"

QUALITY = 82           # WebP quality to start from
MIN_QUALITY = 66       # the lowest it will go to meet a size budget
BUDGET_HERO = 250_000  # bytes, the hero at 2x
BUDGET_OTHER = 200_000  # bytes, every other file

NARROW_MEDIA = "(max-width: 699px)"
CONSOLE_BODY_PX = 17   # the console's body text
MIN_TEXT_PX = 13       # what that text must come out at on a wide crop

# How far a pin sits from the edge of what it points at, and its radius, in
# screen pixels: the pin is 28px with a 2px ring.
PUSH = 18
PIN_R = 14

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

# The tour pictures crossfade in one frame, so their wide crops share a shape.
TOUR_ASPECT = 1.6
# Where the pictures show at the 1440 layout (see the page's CSS): the tour
# screen and the hero picture run to 24px from the right edge.
TOUR_DISPLAY = 976
TOUR_SIZES = ("(min-width: 1320px) calc(50vw + 256px), (min-width: 1100px) calc(100vw - 404px), "
              "(min-width: 700px) min(960px, calc(100vw - 48px)), 100vw")
HERO_SIZES = ("(min-width: 1320px) calc(50vw + 302px), (min-width: 1100px) calc(100vw - 358px), "
              "(min-width: 700px) calc(100vw - 48px), 100vw")

# ---------------------------------------------------------------------------
# The figures on the page. Each id matches an MM-FIG block in the page.
#   source: "console:<page>" (cropped from console/full/<page>.png with
#           console/<page>.anchors.json), "email", or "app:<screen>".
#   crops:  "wide" and optionally "narrow"; see the notes at the top.
#           A wide crop can carry "vars": {name: (anchor, edge, offset)}, written to the
#           page as --name, a fraction of the crop's height; every figure with pins
#           also gets --ratio (height over width of the wide crop).
#   pins:   (anchor, spot) in number order; narrow_pins, if given, the same
#           pins with other spots for the narrow crop.
# ---------------------------------------------------------------------------
FIGURES = [
    {
        "id": "hero",
        "source": "console:dashboard",
        "out": "mm-hero-dashboard",
        "budget": BUDGET_HERO,
        "eager": True,
        "lcp": True,          # fetchpriority high, and a preload block for the head
        "alt": ("The Material Monitor dashboard with sample data: four job cards, the materials that "
                "need ordering with their order-by dates, this week's deliveries and the start of the "
                "follow-up list. A sample company, not a real job."),
        "pins": [("first_job_card", "left"), ("first_order_by_date", "left"),
                 ("deliveries_heading", "left"), ("follow_up_heading", "left")],
        "crops": {
            # The whole dashboard width, from the jobs row down through the first follow-up row, so
            # the phone over the lower right corner covers only the empty right side of that row.
            "wide": {"x0": 84, "x1": 1332, "y0": ("jobs_heading", "top", -20),
                     "y1": ("first_follow_up_row", "bottom", 16),
                     "vars": {"pt": ("first_follow_up_category", "top", -8)},
                     "display": 1022, "widths": [1040, 2080], "sizes": HERO_SIZES},
            # Phones: the left two job cards and the left of every section down to the line under the
            # follow-up heading, so all four pins show; the right edge falls between the second and third card.
            "narrow": {"x0": 60, "x1": 724, "y0": ("jobs_heading", "top", -16),
                       "y1": ("first_follow_up_category", "top", -8), "fade": True,
                       "display": 390, "widths": [560, 1120]},
        },
    },
    {
        "id": "hero-phone",
        "source": "app:home",
        "out": "mm-app-home",
        "eager": True,
        "alt": ("The field app's home screen with sample data: receive materials, look up a material, "
                "report a problem and the expected deliveries by day."),
        "crops": {"wide": {"widths": [240, 480], "sizes": "(min-width: 700px) 21vw, 52vw"}},
    },
    {
        "id": "tour-1",
        "source": "console:dashboard",
        "out": "mm-tour-dashboard",
        "alt": ("The dashboard's follow-up list with sample data: orders that have gone quiet, each "
                "with the reason and the rep, and the button that drafts the emails. A sample company."),
        "pins": [("search_box", "bottom"), ("first_follow_up_reason", "left"),
                 ("draft_an_email_button", "right")],
        "narrow_pins": [("search_box", "bottom"), ("first_follow_up_reason", "left"),
                        ("draft_an_email_button", "left")],
        "crops": {
            # Keeps the console's own bar, because the search box is a callout.
            "wide": {"nav": True, "x0": 100, "x1": 1372, "y0": ("follow_up_heading", "top", -24),
                     "aspect": TOUR_ASPECT, "display": TOUR_DISPLAY, "widths": [980, 1960], "sizes": TOUR_SIZES},
            # Phones: the right of the bar and the heading row (search box, Draft an email button)
            # above the left of the first follow-up row (its reason).
            "narrow": {"stack": [
                {"nav": True, "x0": 700, "x1": 1330, "y0": ("follow_up_heading", "top", -14),
                 "y1": ("draft_an_email_button", "bottom", 14)},
                {"x0": 90, "x1": 720, "y0": ("first_follow_up_category", "top", -10),
                 "y1": ("first_follow_up_row", "bottom", 8), "snap_x1": "first_follow_up_contact"}],
                "fade": True, "display": 390, "widths": [560, 1120]},
        },
    },
    {
        "id": "tour-2",
        "source": "console:job-board",
        "out": "mm-tour-job",
        "alt": ("One job's list with sample data: the box for bringing in a selections export, then the "
                "tile and appliance groups with each material's vendor, status and dates. A sample company."),
        "pins": [("first_section_heading", "left"), ("status_chip_ordered", "top"),
                 ("update_the_list_upload", "left")],
        "crops": {
            "wide": {"x0": 84, "x1": 1332, "y0": ("job_title", "top", -24), "aspect": TOUR_ASPECT,
                     "display": TOUR_DISPLAY, "widths": [980, 1960], "sizes": TOUR_SIZES},
            "narrow": {"x0": 60, "x1": 740, "y0": ("update_the_list_upload", "top", -24),
                       "y1": ("first_board_row", "bottom", 1), "fade": True,
                       "display": 390, "widths": [560, 1120]},
        },
    },
    {
        "id": "tour-3",
        "source": "console:material",
        "out": "mm-tour-material",
        # The form on the left with its order-by line, "Who sells it" and History in the right column.
        "alt": ("A material's page with sample data: its status and dates with the order-by date, the vendor "
                "and the rep with an email address and a phone number, and the history of what changed. "
                "A sample company."),
        "pins": [("vendor_and_rep", "left"), ("order_by_date", "left"), ("first_history_entry", "left")],
        "crops": {
            "wide": {"x0": 84, "x1": 1332, "y0": ("status_field", "top", -24), "aspect": TOUR_ASPECT,
                     "display": TOUR_DISPLAY, "widths": [980, 1960], "sizes": TOUR_SIZES},
            # Phones: the lead time and order-by rows of the form above Who sells it and the first
            # History entry from the right column.
            "narrow": {"stack": [
                {"x0": 90, "x1": 524, "y0": ("lead_time", "top", -12), "y1": ("order_by_date", "bottom", 12)},
                {"x0": 896, "x1": 1330, "y0": ("who_sells_it", "top", -16),
                 "y1": ("first_history_entry", "bottom", 8)}],
                "display": 390, "widths": [560, 868]},
        },
        "narrow_pins": [("vendor_and_rep", "left"), ("order_by_date", "left"), ("first_history_entry", "top-left")],
    },
    {
        "id": "tour-4",
        "source": "console:updates-proposals",
        "out": "mm-tour-updates",
        "alt": ("The Updates page with sample data: vendor updates waiting for an OK, each with the "
                "proposed change, the vendor's own sentence and Confirm, Edit and Dismiss. A sample company."),
        "pins": [("proposed_change", "left"), ("quoted_vendor_sentence", "left"),
                 ("confirm_button", "left")],
        "crops": {
            "wide": {"x0": 84, "x1": 1332, "y0": ("proposals_heading", "top", -24), "aspect": TOUR_ASPECT,
                     "display": TOUR_DISPLAY, "widths": [980, 1960], "sizes": TOUR_SIZES},
            "narrow": {"x0": 84, "x1": 640, "y0": ("proposal_card", "top", -16),
                       "y1": ("proposal_card", "bottom", 16), "snap_x1": "quoted_vendor_sentence",
                       "fade": True, "display": 390, "widths": [560, 1120]},
        },
    },
    {
        "id": "tour-5",
        "source": "console:follow-up",
        "out": "mm-tour-follow-up",
        "alt": ("Follow-up emails written for the reps with sample data, one per rep: each open order with its "
                "model number, how many arrived and the order date, and the button that opens it in Outlook. "
                "A sample company."),
        "pins": [("first_draft_vendor_and_rep", "left"), ("first_draft_body", "left"),
                 ("open_in_outlook", "left")],
        "crops": {
            "wide": {"x0": 84, "x1": 1332, "y0": ("first_draft", "top", -56), "aspect": TOUR_ASPECT,
                     "display": TOUR_DISPLAY, "widths": [980, 1960], "sizes": TOUR_SIZES},
            "narrow": {"x0": 84, "x1": 700, "y0": ("first_draft", "top", -16),
                       "y1": ("first_draft", "bottom", 12), "snap_x1": "first_draft_body",
                       "fade": True, "display": 390, "widths": [560, 1120]},
        },
    },
    {
        "id": "email",
        "source": "email",
        "measure": {"first_line": "td p"},
        "out": "mm-morning-email",
        "alt": ("The morning email with sample data: the updates waiting for an OK, the materials that "
                "need ordering, the problems flagged from the field and what arrived. A sample company."),
        "pins": [("first_line", "right"), ("section_1", "left"), ("section_2", "left"),
                 ("section_3", "left")],
        "crops": {
            # The email down to the end of Items received. It stops before "Orders and tracking",
            # whose carrier lines describe carrier tracking, which is not switched on yet.
            "wide": {"x0": 36, "x1": 684, "y0": 0, "y1": ("section_4", "top", -14),
                     "display": 600, "widths": [600, 1080],
                     "sizes": "(min-width: 1100px) 600px, (min-width: 700px) min(600px, calc(100vw - 48px)), 100vw"},
            # Phones: the masthead, the first line and Needs ordering, cut on the right so the
            # material names and dates read; the whole email is on wider screens.
            "narrow": {"x0": 40, "x1": 490, "y0": 0, "y1": ("section_4", "top", -14), "fade": True,
                       "display": 390, "widths": [560, 900]},
        },
        "narrow_pins": [("first_line", "left"), ("section_1", "left"), ("section_2", "left"),
                        ("section_3", "left")],
    },
    {
        "id": "field-receive",
        "source": "app:receive-list",
        "out": "mm-app-receive",
        "alt": ("The field app's receiving screen with sample data: what came in at one job, with a "
                "shower valve ticked and marked in good condition."),
        "crops": {"wide": {"widths": [280, 560], "sizes": "(min-width: 900px) 280px, 70vw"}},
    },
    {
        "id": "field-material",
        "source": "app:material",
        "out": "mm-app-material",
        "alt": ("A material in the field app with sample data: shipped and due Wednesday, with its tracking "
                "number, maker, model, vendor and rep. Buttons below email the rep or receive it."),
        "crops": {"wide": {"widths": [280, 560], "sizes": "(min-width: 900px) 280px, 70vw"}},
    },
    {
        "id": "field-problem",
        "source": "app:tell-the-office",
        "out": "mm-app-problem",
        "alt": ("The field app's report a problem screen with sample data: a powder room sink marked "
                "damaged, with a sentence for the office."),
        "crops": {"wide": {"widths": [280, 560], "sizes": "(min-width: 900px) 280px, 70vw"}},
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


def resolve(v, anchors: dict, what: str) -> float:
    """A crop edge: a number, or (anchor, edge, offset)."""
    if isinstance(v, (int, float)):
        return float(v)
    name, edge, off = v
    if name not in anchors:
        raise SystemExit(f"{what}: anchor {name!r} is not in the shots")
    x, y, w, h = anchors[name]
    base = {"top": y, "bottom": y + h, "left": x, "right": x + w}[edge]
    return base + float(off)


class Frame:
    """One cropped picture plus every anchor inside it, in the crop's CSS pixels."""

    def __init__(self, image: Image.Image, scale: float, css_w: float, css_h: float, desc: str):
        self.image = image          # full-resolution crop
        self.scale = scale          # image pixels per CSS pixel
        self.css_w = css_w
        self.css_h = css_h
        self.desc = desc
        self.anchor = {}            # name -> (x, y, w, h)
        self.var = {}               # name -> fraction of the crop's height


_full_cache: dict = {}


def console_source(shots: Path, page: str):
    key = (str(shots), page)
    if key not in _full_cache:
        data = load_json(shots / "console" / f"{page}.anchors.json")
        full_rel = data.get("full_page_picture") or f"console/full/{page}.png"
        full = Image.open(shots / full_rel).convert("RGB")
        anchors = {k: rect(v["full_page"]) for k, v in data["anchors"].items()
                   if isinstance(v, dict) and v.get("full_page")}
        nav = anchors.get("nav_updates")
        nav_h = (nav[1] + nav[3]) if nav else 62.0
        _full_cache[key] = (data, full_rel, full, anchors, nav_h)
    return _full_cache[key]


def crop_console(shots: Path, fig: dict, spec: dict) -> Frame:
    page = fig["source"].split(":", 1)[1]
    data, full_rel, full, anchors, nav_h = console_source(shots, page)
    scale = float(data.get("device_scale_factor", 2))
    page_h = float(data["full_page"]["height"])
    what = f"{fig['id']}"
    x0 = resolve(spec["x0"], anchors, what)
    x1 = resolve(spec["x1"], anchors, what)
    y0 = resolve(spec["y0"], anchors, what)
    if spec.get("snap_x1"):
        x1 = snap_clear_x(full, scale, x1, anchors[spec["snap_x1"]], what)
    top = nav_h if spec.get("nav") else 0.0
    w = x1 - x0
    if "aspect" in spec:
        y1 = y0 + w / spec["aspect"] - top
    else:
        y1 = resolve(spec["y1"], anchors, what)
    if y0 < top:                      # never repeat the bar's own rows
        y1 += top - y0
        y0 = top
    if y1 > page_h:
        y0, y1 = y0 - (y1 - page_h), page_h
    x0, x1, y0, y1 = (round(v) for v in (x0, x1, y0, y1))
    w, h = x1 - x0, (y1 - y0) + round(top)
    px = lambda v: int(round(v * scale))
    img = Image.new("RGB", (px(w), px(h)))
    if top:
        img.paste(full.crop((px(x0), 0, px(x1), px(top))), (0, 0))
    img.paste(full.crop((px(x0), px(y0), px(x1), px(y1))), (0, px(top)))
    bar = ", the console's bar kept" if top else ""
    fr = Frame(img, scale, w, h, f"{full_rel}, x {x0} to {x1}, y {y0} to {y1}{bar} ({w} x {h})")
    for name, (ax, ay, aw, ah) in anchors.items():
        if ay + ah <= nav_h:
            if top:
                fr.anchor[name] = (ax - x0, ay, aw, ah)
        else:
            fr.anchor[name] = (ax - x0, ay - y0 + top, aw, ah)
    # Named fractions of the crop's height for the page's CSS (for example where the hero phone starts).
    for vname, edge in spec.get("vars", {}).items():
        fr.var[vname] = (resolve(edge, anchors, what) - y0 + top) / h
    return fr


def snap_clear_x(full: Image.Image, scale: float, x1: float, band: tuple, what: str) -> float:
    """The nearest x at or left of x1 where the band's rows have 4 clear CSS pixels (a gap between words)."""
    import numpy as np
    bx, by, bw, bh = band
    rows = np.asarray(full.crop((0, int(by * scale), full.width, int((by + bh) * scale))).convert("L"))
    clear = (rows > 205).all(axis=0)              # a column with no ink in the band
    need = int(4 * scale)
    x = int(x1 * scale)
    for _ in range(int(160 * scale)):
        if clear[x - need:x].all():
            return (x - need / 2) / scale
        x -= 1
    warn(f"{what}: no gap between words near x {x1:.0f}; the edge stays")
    return x1


def crop_stack(shots: Path, fig: dict, spec: dict) -> Frame:
    """Several crops of one page, one above the other, for a phone."""
    gap = spec.get("gap", 14)
    parts = [crop_console(shots, fig, sub) for sub in spec["stack"]]
    scale = parts[0].scale
    w = max(p.css_w for p in parts)
    h = sum(p.css_h for p in parts) + gap * (len(parts) - 1)
    ground = parts[0].image.getpixel((2, parts[0].image.height - 2))
    img = Image.new("RGB", (int(round(w * scale)), int(round(h * scale))), ground)
    fr = Frame(img, scale, w, h, " then ".join(p.desc for p in parts))
    y = 0.0
    for p in parts:
        img.paste(p.image, (0, int(round(y * scale))))
        for name, (ax, ay, aw, ah) in p.anchor.items():
            # an anchor belongs to the part its top left corner falls in
            if name not in fr.anchor and 0 <= ax <= p.css_w and 0 <= ay <= p.css_h:
                fr.anchor[name] = (ax, ay + y, aw, ah)
        y += p.css_h + gap
    return fr


_email_cache: dict = {}


def crop_email(shots: Path, fig: dict, spec: dict) -> Frame:
    key = str(shots)
    if key not in _email_cache:
        data = load_json(shots / "email" / "morning.anchors.json")
        pic = Image.open(shots / data.get("picture", "email/morning.png")).convert("RGB")
        scale = float(data.get("device_scale_factor", 2))
        width = float(data.get("width", pic.width / scale))
        anchors = {k: rect(v) for k, v in data["anchors"].items()}
        html = shots / "email" / "morning.html"
        if fig.get("measure") and html.exists():
            anchors.update(measure_html(html, int(width), fig["measure"]))
        _email_cache[key] = (data, pic, scale, anchors)
    data, pic, scale, anchors = _email_cache[key]
    x0, x1 = resolve(spec["x0"], anchors, "email"), resolve(spec["x1"], anchors, "email")
    y0, y1 = resolve(spec["y0"], anchors, "email"), resolve(spec["y1"], anchors, "email")
    x0, x1, y0, y1 = (round(v) for v in (x0, x1, y0, y1))
    px = lambda v: int(round(v * scale))
    img = pic.crop((px(x0), px(y0), px(x1), px(y1)))
    fr = Frame(img, scale, x1 - x0, y1 - y0, f"{data.get('picture', 'email/morning.png')}, x {x0} to {x1}, y {y0} to {y1}")
    fr.anchor = {k: (x - x0, y - y0, w, h) for k, (x, y, w, h) in anchors.items()}
    return fr


def crop_app(shots: Path, fig: dict, spec: dict) -> Frame:
    screen = fig["source"].split(":", 1)[1]
    pic = Image.open(shots / "app" / f"{screen}.png").convert("RGB")
    scale = 3.0
    apath = shots / "app" / f"{screen}.anchors.json"
    if apath.exists():
        scale = float(load_json(apath).get("device_scale_factor", 3))
    return Frame(pic, scale, pic.width / scale, pic.height / scale, f"app/{screen}.png")


def save_webp(img: Image.Image, path: Path, width: int, budget: int, dry: bool) -> tuple[int, int, int, int]:
    width = min(width, img.width)          # never enlarge the source
    h = round(img.height * width / img.width)
    small = img.resize((width, h), Image.LANCZOS) if width != img.width else img
    q = QUALITY
    while True:
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
    return width, h, size, q


def place_pins(fig: dict, fr: Frame, display: float | None, variant: str) -> list[dict]:
    """Every pin as a percentage of the crop, or hidden when it does not fit inside."""
    k = (display / fr.css_w) if display else 1.0      # screen pixels per CSS pixel
    out = []
    pins = fig.get("narrow_pins", fig["pins"]) if variant == "narrow" else fig.get("pins", [])
    for n, (name, spot) in enumerate(pins, start=1):
        fx, fy, pxs, pys = SPOTS[spot]
        a = fr.anchor.get(name)
        p = {"n": n, "name": name, "spot": spot, "hidden": True}
        if a is not None:
            x, y, w, h = a
            ax, ay = x + fx * w, y + fy * h
            cx, cy = ax + pxs * PUSH / k, ay + pys * PUSH / k      # the pin's centre, CSS px
            r = (PIN_R + 1) / k
            if r <= cx <= fr.css_w - r and r <= cy <= fr.css_h - r:
                p.update(hidden=False, rect=a, x=100 * ax / fr.css_w, y=100 * ay / fr.css_h,
                         dx=pxs * PUSH, dy=pys * PUSH)
        if p["hidden"]:
            warn(f"{fig['id']} {variant}: pin {n} ({name}) does not fit in the crop; hidden there")
        out.append(p)
    return out


def img_tag(fig: dict, files: list[tuple[int, int]], spec: dict, stem: str, cls: str | None) -> str:
    w1, h1 = files[0]
    srcset = ", ".join(f"{OUT_URL}/{stem}-{w}.webp {w}w" for w, _ in files)
    loading = 'fetchpriority="high"' if fig.get("lcp") else ("" if fig.get("eager") else 'loading="lazy"')
    c = f'class="{cls}" ' if cls else ""
    return (f'<img {c}src="{OUT_URL}/{stem}-{w1}.webp" srcset="{srcset}" sizes="{spec["sizes"]}" '
            f'width="{w1}" height="{h1}" {loading + " " if loading else ""}decoding="async" alt="{fig["alt"]}">')


def block_for(fig: dict, shots_name: str, frames: dict, pins: dict, files: dict) -> str:
    fid = fig["id"]
    lines = [f"<!-- MM-FIG {fid} START. Generated by scripts/mm_site_images.py from {shots_name}."]
    for variant, fr in frames.items():
        lines.append(f"     {variant}: {fr.desc}")
        for p in pins.get(variant, []):
            if p["hidden"]:
                lines.append(f"       pin {p['n']}  {p['name']} ({p['spot']}): outside this crop, hidden")
            else:
                x, y, w, h = p["rect"]
                lines.append(f"       pin {p['n']}  {p['name']} ({p['spot']}) box {x:.0f},{y:.0f} {w:.0f}x{h:.0f}"
                             f" -> left {p['x']:.3f}% top {p['y']:.3f}%, pushed {p['dx']}px {p['dy']}px")
    if fig.get("pins"):
        lines.append("     To move a pin or a crop, change it in the script and run it again; do not edit the numbers here.")
    lines[-1] += " -->"
    wide = img_tag(fig, files["wide"], fig["crops"]["wide"], fig["out"], "shot-img" if fig.get("pins") else None)
    if "narrow" in files:
        nf = files["narrow"]
        nsrc = ", ".join(f"{OUT_URL}/{fig['out']}-n-{w}.webp {w}w" for w, _ in nf)
        pic = (f'<picture><source media="{NARROW_MEDIA}" srcset="{nsrc}" sizes="100vw" '
               f'width="{nf[0][0]}" height="{nf[0][1]}">{wide}</picture>')
    else:
        pic = wide
    if fig.get("pins"):
        parts, classes = [], ["shot"]
        for p in pins["wide"]:
            if p["hidden"]:
                classes.append(f"miss-{p['n']}")
            else:
                parts.append(f"--x{p['n']}:{p['x']:.3f}%;--y{p['n']}:{p['y']:.3f}%;"
                             f"--dx{p['n']}:{p['dx']}px;--dy{p['n']}:{p['dy']}px")
        wfr = frames["wide"]
        parts.append(f"--ratio:{wfr.css_h / wfr.css_w:.4f}")
        for vname, v in fig["crops"]["wide"].get("vars", {}).items():
            parts.append(f"--{vname}:{wfr.var[vname]:.4f}")
        if fig["crops"].get("narrow", {}).get("fade"):
            classes.append("nfade")
        if "narrow" in pins:
            classes.append("two")
            for p in pins["narrow"]:
                if p["hidden"]:
                    classes.append(f"nmiss-{p['n']}")
                else:
                    parts.append(f"--nx{p['n']}:{p['x']:.3f}%;--ny{p['n']}:{p['y']:.3f}%;"
                                 f"--ndx{p['n']}:{p['dx']}px;--ndy{p['n']}:{p['dy']}px")
        lines.append(f'<div class="{" ".join(classes)}" style="{";".join(parts)}">')
        lines.append(f'<div class="pic">{pic}')
    else:
        lines.append(pic)
    lines.append(f"<!-- MM-FIG {fid} END -->")
    return "\n".join(lines)


def preload_block(fig: dict, files: dict, shots_name: str) -> str:
    """Preload the largest picture of the first screen, the wide or the narrow crop by width."""
    fid = fig["id"] + "-preload"
    out = [f"<!-- MM-FIG {fid} START. Generated by scripts/mm_site_images.py from {shots_name}. -->"]
    wide = files["wide"]
    srcset = ", ".join(f"{OUT_URL}/{fig['out']}-{w}.webp {w}w" for w, _ in wide)
    media = ' media="(min-width: 700px)"' if "narrow" in files else ""
    out.append(f'<link rel="preload" as="image" href="{OUT_URL}/{fig["out"]}-{wide[0][0]}.webp" '
               f'imagesrcset="{srcset}" imagesizes="{fig["crops"]["wide"]["sizes"]}"{media} fetchpriority="high">')
    if "narrow" in files:
        nf = files["narrow"]
        nsrc = ", ".join(f"{OUT_URL}/{fig['out']}-n-{w}.webp {w}w" for w, _ in nf)
        out.append(f'<link rel="preload" as="image" href="{OUT_URL}/{fig["out"]}-n-{nf[0][0]}.webp" '
                   f'imagesrcset="{nsrc}" imagesizes="100vw" media="{NARROW_MEDIA}" fetchpriority="high">')
    out.append(f"<!-- MM-FIG {fid} END -->")
    return "\n".join(out)


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

    blocks, total = {}, {}
    for fig in FIGURES:
        if args.only and fig["id"] not in args.only:
            continue
        kind = fig["source"].split(":", 1)[0]
        base_cropper = {"console": crop_console, "email": crop_email, "app": crop_app}[kind]
        cropper = lambda sh, f, sp: (crop_stack if "stack" in sp else base_cropper)(sh, f, sp)
        frames, pins, files, written = {}, {}, {}, set()
        print(f"\n== {fig['id']}")
        for variant, spec in fig["crops"].items():
            fr = cropper(shots, fig, spec)
            frames[variant] = fr
            stem = fig["out"] + ("-n" if variant == "narrow" else "")
            display = spec.get("display")
            note = ""
            if display:
                k = display / fr.css_w
                note = f", shown {display}px wide (x{k:.3f})"
                if kind == "console" and variant == "wide":
                    text = CONSOLE_BODY_PX * k
                    note += f", console text {text:.1f}px"
                    if text < MIN_TEXT_PX:
                        warn(f"{fig['id']}: the console's {CONSOLE_BODY_PX}px text shows at {text:.1f}px, under {MIN_TEXT_PX}px")
                if k > 1.08 and variant == "wide":
                    warn(f"{fig['id']}: the crop is enlarged {k:.2f} times at the 1440 layout; it may look soft")
            print(f"   {variant}: {fr.desc}{note}")
            files[variant] = []
            for w in spec["widths"]:
                aw = min(w, fr.image.width)
                if any(fw == aw for fw, _ in files[variant]):
                    continue
                path = OUT_DIR / f"{stem}-{aw}.webp"
                aw, ah, size, q = save_webp(fr.image, path, aw, fig.get("budget", BUDGET_OTHER), args.dry_run)
                files[variant].append((aw, ah))
                written.add(path.name)
                total[path.name] = size
                print(f"     {path.name:36s} {aw} x {ah}  {size / 1000:6.1f} KB  q{q}")
            if fig.get("pins"):
                pins[variant] = place_pins(fig, fr, display, variant)
                for p in pins[variant]:
                    if not p["hidden"]:
                        print(f"     pin {p['n']}  {p['name']:28s} {p['spot']:12s} left {p['x']:7.3f}%  "
                              f"top {p['y']:7.3f}%  push {p['dx']:+d}px {p['dy']:+d}px")
        if not args.dry_run:        # remove this figure's files from earlier crops
            for old in glob.glob(str(OUT_DIR / f"{fig['out']}-*.webp")):
                if Path(old).name not in written and re.fullmatch(re.escape(fig["out"]) + r"-(n-)?\d+\.webp", Path(old).name):
                    os.remove(old)
        blocks[fig["id"]] = block_for(fig, shots.name, frames, pins, files)
        print(blocks[fig["id"]])
        if fig.get("lcp"):
            blocks[fig["id"] + "-preload"] = preload_block(fig, files, shots.name)

    print(f"\nTotal of the WebP files written: {sum(total.values()) / 1000:.0f} KB over {len(total)} files.")
    if args.apply and not args.dry_run:
        apply_blocks(blocks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
