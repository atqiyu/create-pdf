---
name: create-pdf
description: Author a high-quality, print-ready PDF document by writing HTML + CSS (with KaTeX math and SVG figures), then rendering it with headless Chrome. Use whenever the user asks to 写/生成/输出 一份 PDF 文档 — 报告、方案、论文、白皮书、说明书、简历、政策文件、会议材料 — or says "把这个内容做成排版精美的 PDF", "出一份可打印的报告", "make a PDF report/document", even if they only hand over rough notes, an outline or a Markdown draft.
---

# create-pdf

Write the document as **HTML parts + one stylesheet**, then print it with Chrome.
The result is a flowing A4 document with automatic numbering, a real table of
contents with page numbers, running heads, page numbers and PDF bookmarks.

This skill is for **flowing documents** (text that paginates itself). For
slide-like fixed layouts — one designed page per screen — use `pptx-to-handout`
instead.

## Quick start

```bash
SKILL=~/.agents/skills/create-pdf

# scaffold a new document (cover + 2 empty chapters + theme.css)
python $SKILL/scripts/scaffold.py my-doc --title "项目名称"

# build: headings numbered, TOC filled, heads/footers stamped, bookmarks written
python $SKILL/scripts/build.py --dir my-doc --out my-doc/out/doc.pdf \
    --title "项目名称" --author "作者/单位"

# gate the result
python $SKILL/scripts/qa_check.py --pdf my-doc/out/doc.pdf --dpi 150
```

Requires Python 3.9+, Node 16+, Chrome or Edge. `pip install pymupdf`.

## How it works

```
parts/p00-cover.html          optional, detected by class="cover"
parts/p01-….html …            body: h1 = chapter, h2/h3 = sections
        │
        ├─ number_headings()  injects <span class="secno">1.2</span> + ids
        ├─ pass 1 → draft.pdf → locate every heading by (text, font size)
        ├─ pass 2 → real TOC page numbers → final PDF
        └─ PyMuPDF stamp(): running head + footer + bookmarks + metadata
```

Chrome cannot do `@page` margin boxes or `target-counter()`, which is why page
numbers and headers are added after printing rather than in CSS. Everything
else — pagination, widow control, table header repetition, figure/table
numbering — is plain CSS (`break-inside`, `thead { display: table-header-group }`,
CSS counters).

## Authoring

Write one file per chapter in `parts/`, plain semantic HTML:

```html
<h1>项目背景与目标</h1>            <!-- chapter: starts a new page, auto "1" -->
<p class="lead">这一章要回答什么。</p>

<h2>现状与问题</h2>                 <!-- auto "1.1" -->
<p>正文……</p>

<figure class="figure">             <!-- auto "图 1" -->
  <svg …></svg>
  <figcaption>图注写“要看什么”</figcaption>
</figure>

<figure class="table-wrap">         <!-- auto "表 1" -->
  <figcaption>表题</figcaption>
  <table><thead>…</thead><tbody>…</tbody></table>
</figure>

<div class="callout warn">          <!-- callout / warn / note -->
  <div class="ct">关键约束</div><p>……</p>
</div>
```

Rules that keep the output clean:

- **Never type numbers** — chapters, sections, figures and tables are numbered
  by the build/ CSS. The TOC reuses the same numbers.
- One `h1` per chapter, and let the chapter start on a fresh page. If a chapter
  spills 2–3 lines onto a new page, you get a nearly blank page — trim text or
  move a figure, don't fight the layout.
- Figures: inline SVG preferred (crisp); avoid screenshots. Keep `<svg>` with
  `width`/`height` attributes matching the viewBox.
- Tables: use `<thead>`; long tables then repeat their header across pages.
- Math: `$…$` inline, `$$…$$` display. Pre-rendered by KaTeX at build time.
- Colour and type: don't inline styles; change tokens in `theme.css`.

Full component reference: `references/components.md`.

## Quality bar (checked by qa_check.py)

| Check | Pass condition |
|---|---|
| Scale | body text measures exactly 10.5 pt (a ratio ≠ 1 means something is wider than the text block) |
| TOC | no `··` placeholders left — every entry has a page number |
| Split headings | no heading is the last line of a page |
| Empty pages | no body page under ~90 characters |
| Geometry | every page is 595.28 × 841.89 pt (A4) |
| Fonts | no Type3 glyphs; Chinese embedded as TrueType |
| Renders | one PNG per page for visual review |

Then read the PNGs yourself: look for a page that is 90 % empty, a figure that
floats far from its caption, a table split across pages without a repeated
header, and any paragraph whose last line is a single character.

## Debugging

- `--debug` paints headings that land at the page edge and leaves the draft HTML
  (`draft.html`) in the document folder.
- `--keep` keeps the two-pass intermediates.
- If every page looks 0.8× too small, some element is wider than the text block:
  Chrome shrinks the whole document to fit. See `references/pitfalls.md` §1.

## Limitations (by design)

- A4 portrait, CJK-first. Letter or landscape needs edits in `assets/base.css`
  and the constants at the top of `scripts/build.py`.
- No footnote-at-page-bottom (Chrome lacks `float: footnote`) — use endnotes
  (`.refs`) or bracketed citations.
- No cross-references like "见第 12 页" (needs `target-counter`); write the
  section name instead.
- Fancy covers are typographic, not full-bleed: a 210 mm-wide cover forces
  Chrome's shrink-to-fit. Keep the cover inside the text block.