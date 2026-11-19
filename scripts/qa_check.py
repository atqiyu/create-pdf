#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""QA gate for a create-pdf document.

Checks
  1. TOC completeness  - no “—” placeholders left in the table of contents.
  2. Split headings    - a heading must not be the last line of a page
                         (break-after: avoid cannot see the next block's height).
  3. Page geometry     - every page is A4.
  4. Fonts             - flags Type3 output (CFF/OTF CJK vectorised by Chrome).
  5. Renders           - page PNGs for visual review.

Usage:
    python qa_check.py --pdf out/doc.pdf [--dpi 150] [--out qa]
"""
import os
import sys
import argparse

import pymupdf

A4 = (595.28, 841.89)
HEADING_PT = {21.0: "h1", 15.5: "h2", 11.5: "h3"}
BODY_PT = 10.5


def check_toc(pdf, toc_pages=3):
    doc = pymupdf.open(pdf)
    bad = []
    for p in range(min(toc_pages, doc.page_count)):
        txt = doc[p].get_text()
        if "目录" in txt and "··" in txt:
            bad.append(p + 1)
    return "OK (all entries numbered)" if not bad else f"placeholder dashes on pages {bad}"


def check_split_headings(pdf):
    doc = pymupdf.open(pdf)
    bad = []
    for p in range(doc.page_count):
        lines = []
        for b in doc[p].get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                t = "".join(s["text"] for s in l["spans"]).strip()
                if t:
                    size = max(s["size"] for s in l["spans"])
                    lines.append((l["bbox"][3], t, size, l["bbox"][0]))
        # ignore stamped footer/header (outside the text block)
        body = [x for x in lines if 40 < x[0] < doc[p].rect.height - 45]
        if not body:
            continue
        last = max(body, key=lambda x: x[0])
        for pt, name in HEADING_PT.items():
            if abs(last[2] - pt) < 0.7:
                bad.append(f"p{p+1}: {name} “{last[1][:18]}”")
    return "OK" if not bad else "split headings -> " + "; ".join(bad[:4])


def check_scale(pdf):
    """Body text should measure 10.5 pt. A uniform ratio != 1 means Chrome
    shrank the document because some element is wider than the text block."""
    doc = pymupdf.open(pdf)
    from collections import Counter
    c = Counter()
    for p in range(2, doc.page_count):
        for b in doc[p].get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for s in l["spans"]:
                    if s["text"].strip():
                        c[round(s["size"], 1)] += len(s["text"])
    if not c:
        return "SKIP (no text)"
    mode = c.most_common(1)[0][0]
    ratio = mode / BODY_PT
    if abs(ratio - 1) > 0.03:
        return (f"SCALED {ratio:.2f}x — body text measures {mode}pt instead of "
                f"{BODY_PT}pt; an element is wider than the text block")
    return f"OK (body {mode}pt)"


def check_empty_pages(pdf, min_chars=90):
    doc = pymupdf.open(pdf)
    bad = []
    for p in range(2, doc.page_count):          # skip cover + TOC
        txt = "".join(doc[p].get_text().split())
        if len(txt) < min_chars:
            bad.append(f"p{p+1} ({len(txt)} chars)")
    return "OK (no near-empty body pages)" if not bad else "near-empty: " + ", ".join(bad)


def check_geometry(pdf):
    doc = pymupdf.open(pdf)
    bad = [f"p{i+1}:{p.rect.width:.0f}x{p.rect.height:.0f}pt"
           for i, p in enumerate(doc) if abs(p.rect.width - A4[0]) > 2 or abs(p.rect.height - A4[1]) > 2]
    return (f"{doc.page_count} pages, all A4" if not bad else "; ".join(bad))


def check_fonts(pdf):
    doc = pymupdf.open(pdf)
    t3, names = set(), set()
    for page in doc:
        for f in page.get_fonts():
            n = f[3] or ""
            if "Type3" in n:
                t3.add(page.number + 1)
            elif n:
                names.add(n.split("+")[-1])
    if t3:
        return False, f"Type3 glyphs on pages {sorted(t3)} -> use a TrueType CJK font"
    cjk = [n for n in names if any(k in n for k in ("YaHei", "SimSun", "SimHei", "Noto", "Song", "Hei", "Droid"))]
    return True, "OK (" + ", ".join(sorted(cjk)[:4]) + ")"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--out", default="qa")
    a = ap.parse_args()

    print("[1/7] scale ...");      print("      ", check_scale(a.pdf))
    print("[2/7] toc ...");        print("      ", check_toc(a.pdf))
    print("[3/7] headings ...");   print("      ", check_split_headings(a.pdf))
    print("[4/7] empty pages ...");print("      ", check_empty_pages(a.pdf))
    print("[5/7] geometry ...");   print("      ", check_geometry(a.pdf))
    ok, msg = check_fonts(a.pdf)
    print("[6/7] fonts ...");      print("      ", ("PASS " if ok else "WARN ") + msg)
    print("[7/7] renders ...")
    os.makedirs(a.out, exist_ok=True)
    doc = pymupdf.open(a.pdf)
    for i, page in enumerate(doc, 1):
        page.get_pixmap(dpi=a.dpi).save(os.path.join(a.out, f"page{i:02d}.png"))
    print(f"       {doc.page_count} PNGs -> {a.out}")


if __name__ == "__main__":
    main()