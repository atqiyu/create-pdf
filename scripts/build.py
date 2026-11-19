#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build a flowing A4 PDF document from HTML parts.

Two passes:
  1. print a draft PDF to learn where every heading landed;
  2. rebuild the table of contents with real page numbers, print the final PDF,
     then stamp running heads / page numbers and write PDF bookmarks.

Parts live in <dir>/parts/p*.html and are concatenated in order. Headings are
auto-numbered (1 / 1.1 / 1.1.1) by this script, so authors never type numbers.

Usage:
    python build.py --dir doc --out out/doc.pdf --title "…" [--author "…"]
                    [--toc-depth 2] [--theme modern] [--no-stamp] [--debug]
"""
import os
import re
import sys
import glob
import json
import shutil
import argparse
import subprocess

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
BASE_CSS = os.path.join(SKILL, "assets", "base.css")
KATEX_SRC = os.path.join(SKILL, "assets", "katex")

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]

# must match base.css
HEADING_PT = {1: 21.0, 2: 15.5, 3: 11.5}
MARGIN_L, MARGIN_R, MARGIN_T = 21.0, 21.0, 24.0     # mm
STAMP_PT = 8.0

SHELL = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>{title}</title>
<meta name="author" content="{author}">
<link rel="stylesheet" href="vendor/katex/katex.min.css">
<style>
{base}
{theme}
</style></head>
<body>
{cover}
{toc}
{body}
{debug}
</body></html>"""

DEBUG_JS = """<script>
window.addEventListener('load', () => {
  document.querySelectorAll('h1,h2,h3').forEach(h => {
    const r = h.getBoundingClientRect();
    // a heading within 2px of the page bottom will be split by the printer
    if (r.bottom > window.innerHeight - 2 && r.top < window.innerHeight) {
      h.style.background = '#fee'; h.dataset.split = '1';
    }
  });
});
</script>"""


def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    for name in ("google-chrome", "chromium", "chrome", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    sys.exit("Chrome/Edge not found")


def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", "", s)


def plain_text(html):
    """Heading text as the PDF will roughly show it: no tags, no math."""
    s = re.sub(r"\$\$[\s\S]+?\$\$", "", html)
    s = re.sub(r"\$[^$]+?\$", "", s)
    return strip_tags(s)


def number_headings(parts, toc_depth):
    """Inject <span class="secno"> and ids; collect TOC entries."""
    counters = [0, 0, 0]
    entries = []
    out = []
    idx = 0
    for part in parts:
        def repl(m):
            nonlocal idx
            lvl = int(m.group(1))
            attrs = m.group(2) or ""
            inner = m.group(3)
            if "data-toc-skip" in attrs:
                return m.group(0)
            counters[lvl - 1] += 1
            for j in range(lvl, 3):
                counters[j] = 0
            secno = ".".join(str(counters[k]) for k in range(lvl))
            idx += 1
            hid = re.search(r'id="([^"]+)"', attrs)
            hid = hid.group(1) if hid else f"h-{idx}"
            attrs = re.sub(r'\s*id="[^"]*"', "", attrs)
            entries.append({
                "id": hid, "level": lvl, "secno": secno,
                "html": inner.strip(),
                "plain": plain_text(inner),
                "needle": (secno + plain_text(inner))[:24],
                "size": HEADING_PT[lvl],
            })
            # h4 and deeper are never in the TOC; level filter happens later
            if lvl <= toc_depth:
                pass
            return f'<h{lvl}{attrs} id="{hid}"><span class="secno">{secno}</span>{inner}</h{lvl}>'

        out.append(re.sub(r"<h([123])(\s[^>]*)?>([\s\S]*?)</h\1>", repl, part))
    visible = [e for e in entries if e["level"] <= toc_depth]
    return out, visible


def build_toc(entries, page_map):
    if not entries:
        return ""
    rows = []
    for e in entries:
        num = page_map.get(e["id"], "\u2014")
        rows.append(
            f'<li class="lvl{e["level"]}"><span class="t">'
            f'<span class="secno">{e["secno"]}</span>\u2002{e["html"]}</span>'
            f'<span class="d"></span><span class="p" data-id="{e["id"]}">{num}</span></li>'
        )
    return ('<nav class="toc"><h2 class="toc-title">目录</h2><ul>' +
            "".join(rows) + "</ul></nav>")


def assemble(title, author, base_css, theme_css, cover, toc, body, debug=False):
    return SHELL.format(title=title, author=author, base=base_css, theme=theme_css,
                        cover=cover, toc=toc, body=body, debug=DEBUG_JS if debug else "")


def print_pdf(chrome, html_path, out_path):
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    url = "file:///" + os.path.abspath(html_path).replace("\\", "/")
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--allow-file-access-from-files", "--virtual-time-budget=10000",
                    f"--print-to-pdf={os.path.abspath(out_path)}", url],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def locate_headings(pdf_path, entries):
    """Sequential search: a heading is on the page where a same-size span
    starts the next unmatched heading. Headings are in document order, so
    scanning forward avoids matching a later duplicate first."""
    doc = pymupdf.open(pdf_path)
    pages = []
    for pno in range(doc.page_count):
        lines = []
        for b in doc[pno].get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                txt = ""
                size = 0
                for s in l["spans"]:
                    txt += s["text"]
                    size = max(size, s["size"])
                if txt.strip():
                    lines.append((txt, size))
        pages.append(lines)

    result = {}
    cursor = 0
    for e in entries:
        needle = strip_tags(e["needle"])
        if len(needle) < 3:
            continue
        found = None
        for pno in range(cursor, len(pages)):
            for txt, size in pages[pno]:
                if abs(size - e["size"]) <= 1.0 and needle in strip_tags(txt):
                    found = pno + 1
                    break
            if found:
                break
        if found:
            result[e["id"]] = found
            cursor = found - 1
    doc.close()
    return result


def stamp(pdf_in, pdf_out, title, entries, page_map, has_cover=True):
    """Running head (current chapter) + footer page numbers + PDF outline."""
    doc = pymupdf.open(pdf_in)
    w, h = doc[0].rect.width, doc[0].rect.height          # points
    ml, mr = MARGIN_L / 25.4 * 72, MARGIN_R / 25.4 * 72
    head_y = 12.5 / 25.4 * 72
    foot_y = (297 - 12) / 25.4 * 72
    n = doc.page_count

    # chapter (h1) per page
    chaps = sorted([(page_map.get(e["id"]), e["plain"] or e["html"])
                    for e in entries if e["level"] == 1 and page_map.get(e["id"])])
    def chapter_of(p):
        cur = title
        for pg, name in chaps:
            if pg <= p:
                cur = name
        return cur

    for i, page in enumerate(doc):
        pno = i + 1
        if has_cover and pno == 1:
            continue
        # header: chapter name, right aligned, hairline under
        sec = chapter_of(pno)
        if len(sec) > 34:
            sec = sec[:33] + "\u2026"
        page.insert_textbox(pymupdf.Rect(ml, head_y - 12, w - mr, head_y + 4), sec,
                            fontname="china-s", fontsize=STAMP_PT,
                            color=(0.42, 0.45, 0.51), align=2)
        page.draw_line((ml, head_y + 4.2), (w - mr, head_y + 4.2),
                       color=(0.85, 0.88, 0.92), width=0.5)
        # footer: title left, page right
        page.insert_textbox(pymupdf.Rect(ml, foot_y - 12, ml + 380, foot_y + 4), title,
                            fontname="china-s", fontsize=STAMP_PT,
                            color=(0.55, 0.58, 0.63), align=0)
        page.insert_textbox(pymupdf.Rect(w - mr - 140, foot_y - 12, w - mr, foot_y + 4),
                            f"{pno} / {n}", fontname="china-s", fontsize=STAMP_PT,
                            color=(0.30, 0.34, 0.40), align=2)

    toc = []
    for e in entries:
        pg = page_map.get(e["id"])
        if pg:
            name = (e["plain"] or e["html"]).strip() or e["id"]
            toc.append([e["level"], name, pg])
    if toc:
        doc.set_toc(toc)
    doc.set_metadata({"title": title, "creator": "create-pdf", "producer": "Chrome + PyMuPDF"})
    doc.save(pdf_out, garbage=3, deflate=True)
    doc.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="doc")
    ap.add_argument("--out", default="out/doc.pdf")
    ap.add_argument("--title", default="文档")
    ap.add_argument("--author", default="")
    ap.add_argument("--toc-depth", type=int, default=2, choices=[1, 2, 3])
    ap.add_argument("--theme", default="")
    ap.add_argument("--no-toc", action="store_true")
    ap.add_argument("--no-stamp", action="store_true")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--keep", action="store_true", help="keep intermediate html/pdf")
    a = ap.parse_args()

    root = os.path.abspath(a.dir)
    parts_paths = sorted(glob.glob(os.path.join(root, "parts", "p*.html")))
    if not parts_paths:
        sys.exit(f"no parts in {root}/parts")
    parts = [open(p, encoding="utf-8").read() for p in parts_paths]

    cover = ""
    if 'class="cover"' in parts[0] or "class='cover'" in parts[0]:
        cover, parts = parts[0], parts[1:]

    base_css = open(BASE_CSS, encoding="utf-8").read()
    theme_css = ""
    if a.theme:
        tp = os.path.join(SKILL, "assets", "themes", a.theme + ".css")
        if os.path.exists(tp):
            theme_css = open(tp, encoding="utf-8").read()
        else:
            print(f"[warn] theme not found: {a.theme}")

    numbered, entries = number_headings(parts, a.toc_depth)
    body = "\n".join(numbered)

    vk = os.path.join(root, "vendor", "katex")
    if not os.path.exists(vk):
        shutil.copytree(KATEX_SRC, vk)

    def render(toc_html, html_name):
        html = assemble(a.title, a.author, base_css, theme_css, cover, toc_html,
                        body, debug=a.debug)
        p = os.path.join(root, html_name)
        open(p, "w", encoding="utf-8").write(html)
        # math pre-render (server side; print can't wait for browser JS)
        subprocess.run(["node", os.path.join(HERE, "math.js"),
                        os.path.join(vk, "katex.min.js"), p,
                        os.path.join(root, html_name.replace(".src", ""))],
                       check=True, cwd=root)
        return os.path.join(root, html_name.replace(".src", ""))

    final_pdf = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(final_pdf), exist_ok=True)

    if a.no_toc or not entries:
        html = render("", "handout.src.html")
        print_pdf(find_chrome(), html, final_pdf)
        if not a.no_stamp:
            tmp = final_pdf + ".tmp"
            shutil.move(final_pdf, tmp)
            stamp(tmp, final_pdf, a.title, entries, {}, bool(cover))
            os.remove(tmp)
        print("PDF:", final_pdf)
        return

    # pass 1 — draft, no page numbers yet
    draft_html = render(build_toc(entries, {}), "draft.src.html")
    draft_pdf = os.path.join(root, "draft.pdf")
    print_pdf(find_chrome(), draft_html, draft_pdf)

    page_map = locate_headings(draft_pdf, entries)
    missing = [e["secno"] for e in entries if e["id"] not in page_map]
    print(f"[toc] located {len(page_map)}/{len(entries)} headings"
          + (f", missing: {missing[:6]}" if missing else ""))

    # pass 2 — final, with real page numbers
    final_html = render(build_toc(entries, page_map), "doc.src.html")
    print_pdf(find_chrome(), final_html, final_pdf)

    if not a.no_stamp:
        tmp = final_pdf + ".tmp"
        shutil.move(final_pdf, tmp)
        stamp(tmp, final_pdf, a.title, entries, page_map, bool(cover))
        os.remove(tmp)

    if not a.keep:
        for f in (draft_pdf, os.path.join(root, "draft.html"),
                  os.path.join(root, "doc.html")):
            if os.path.exists(f):
                os.remove(f)
    print("PDF:", final_pdf)


if __name__ == "__main__":
    main()