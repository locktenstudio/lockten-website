#!/usr/bin/env python3
"""Rebuild the FAQPage JSON-LD in materialmonitor.html from the page's own FAQ.

The FAQ on the page is a list of <details><summary>Question</summary><p>Answer</p></details>.
Search engines read the FAQPage JSON-LD in the head instead, so the two must say the same
thing. Run this after any change to a question or an answer:

    python scripts/mm_faq_jsonld.py

It rewrites the FAQPage block in place (HTML comments and tags stripped from the answers, the
non-breaking spaces that keep last lines from running short turned back into spaces)
and then checks that every JSON-LD block on the page parses.
"""

import html
import json
import re
import sys
from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent / "materialmonitor.html"


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else PAGE
    src = path.read_text(encoding="utf-8")
    faq = re.search(r'<div class="faq[^"]*">(.*?)</div>\s*</div>\s*</section>', src, re.S)
    if not faq:
        print("No FAQ block found.", file=sys.stderr)
        return 1
    items = []
    for m in re.finditer(r"<details><summary>(.*?)</summary><p>(.*?)</p></details>", faq.group(1), re.S):
        answer = re.sub(r"<!--.*?-->", "", m.group(2), flags=re.S)
        answer = re.sub(r"<[^>]+>", "", answer)
        answer = html.unescape(re.sub(r"\s+", " ", answer)).replace(" ", " ").strip()
        items.append({"@type": "Question", "name": html.unescape(m.group(1).strip()).replace(" ", " "),
                      "acceptedAnswer": {"@type": "Answer", "text": answer}})
    block = json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": items},
                       indent=2, ensure_ascii=False)
    new, n = re.subn(
        r'<script type="application/ld\+json">\s*\{\s*"@context": "https://schema.org",\s*"@type": "FAQPage".*?</script>',
        lambda _: '<script type="application/ld+json">\n' + block + "\n</script>", src, count=1, flags=re.S)
    if n != 1:
        print("No FAQPage JSON-LD block found.", file=sys.stderr)
        return 1
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', new, re.S):
        json.loads(b)
    path.write_text(new, encoding="utf-8", newline="\n")
    print(f"{len(items)} questions written; every JSON-LD block parses.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
