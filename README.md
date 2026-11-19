# create-pdf

> Write a document as HTML/CSS, print it with headless Chrome: a flowing A4 PDF
> with automatic numbering, a real table of contents, running heads, page numbers
> and PDF bookmarks.

This is a ZCode/agent skill: the repo is the skill folder. It complements
`pptx-to-handout` — that one designs fixed A4 pages from a slide deck, this one
typesets text that paginates itself (reports, proposals, papers, manuals).

## Features

- **Auto numbering** — chapters `1`, sections `1.1`, subsections `1.1.1`;
  figures `图 1`, tables `表 1`. You never type a number, and the TOC reuses the
  same values, so numbering cannot drift.
- **Real TOC page numbers** — the build prints a draft, locates every heading by
  (text, font size), then reprints with the numbers filled in.
- **Running heads + footers + bookmarks** — stamped after printing with PyMuPDF,
  because Chrome does not implement `@page` margin boxes or `target-counter()`.
- **Print-grade CSS** — widow/orphan control, `break-inside: avoid` on figures
  and callouts, repeating table headers, booktabs rules, KaTeX math, inline SVG.
- **QA gate** — detects the document-wide shrink trap, leftover TOC
  placeholders, headings stranded at page feet, near-empty pages, Type3 fonts,
  and renders every page to PNG for review.

## Quick start

Requirements: Python 3.9+, Node 16+, Chrome or Edge, `pip install pymupdf`.

```bash
git clone https://github.com/atqiyu/create-pdf.git
cp -r create-pdf ~/.agents/skills/        # or .zcode/skills/

SKILL=~/.agents/skills/create-pdf
python $SKILL/scripts/scaffold.py my-doc --title "项目名称"   # empty skeleton
python $SKILL/scripts/build.py --dir my-doc --out my-doc/out/doc.pdf \
    --title "项目名称" --author "作者/单位"
python $SKILL/scripts/qa_check.py --pdf my-doc/out/doc.pdf --dpi 150
```

## Layout

```
create-pdf/
├── SKILL.md                  workflow, quality bar, limitations
├── references/
│   ├── components.md         every component with copy-paste snippets
│   └── pitfalls.md           13 traps: the 0.8× shrink, missing stamps, Type3…
├── scripts/
│   ├── build.py              two-pass build + stamp + bookmarks
│   ├── math.js               server-side KaTeX pre-render
│   ├── qa_check.py           7 checks + page renders
│   └── scaffold.py           new document skeleton
└── assets/
    ├── base.css              A4 document stylesheet (tokens + components)
    └── katex/                local KaTeX + woff2 (offline)
```

## Authoring in one paragraph

One file per chapter in `parts/`, plain semantic HTML: `<h1>` opens a chapter
(new page), `<h2>`/`<h3>` are sections, `<figure class="figure">` and
`<figure class="table-wrap">` hold figures and tables, `.callout` marks an
aside. Math goes in `$…$`. Restyle via `theme.css`; never hand-number anything.

For flowing documents Chrome's paged-media support is good but not complete —
see `references/pitfalls.md` before fighting the layout.

MIT licensed.