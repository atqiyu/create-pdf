# Pitfalls

Every entry below came from the first build of this skill. Symptom → cause → fix.

## 1. The whole document prints at 80 % (or some odd scale)

**Symptom.** Every font measures smaller than declared: CSS `21pt` arrives as
`16.8pt`, body `10.5pt` arrives as `8.4pt`. The page box is still A4.

**Cause.** One element is wider than the printable text block. Chrome does not
clip it — it **shrinks the entire document** so the widest content fits. In the
first build the cover was `width: 210mm` while the text block was
`210 − 21 − 21 = 168mm`; `168 / 210 = 0.8` exactly.

It can also be triggered by `@page :first { margin: 0 }` when the first-page
rule is not applied, leaving that 210mm block inside normal margins.

**Fix.** Keep every element inside the text block. No full-bleed covers; if you
need a bleed, print a separate cover PDF and merge it. Also check stray
`width: 210mm`, wide tables and unwrapped `<pre>` lines.

**Detect.** `qa_check.py` compares heading font sizes against the CSS table and
prints `expected vs actual` when the whole document is scaled.

## 2. A cover title jumps to the next page

**Symptom.** Page 1 shows only the eyebrow and a rule; the title starts on
page 2.

**Cause.** The global rule `h1 { break-before: page }` (chapters start a new
page) also matches the cover's `<h1>`.

**Fix.** `.cover h1 { break-before: avoid; page-break-before: avoid; }` — and
generally override every global heading rule for the cover.

## 3. PyMuPDF stamps nothing (no header, no footer)

**Symptom.** The hairline appears, the text does not.

**Cause.** `page.insert_textbox()` returns a negative value when the text does
not fit the rectangle, and writes nothing. A 11 pt-tall box is too tight for an
8 pt line (ascender + descender ≈ 9.5 pt plus margins).

**Fix.** Give the box ≥ 16 pt of height (the baseline stays at the rect's top
edge plus font size, so shift the rect, not the text). Check the return value:

```python
rc = page.insert_textbox(rect, text, fontname="china-s", fontsize=8, align=2)
if rc < 0:
    print("text did not fit", rect)
```

`insert_text` does not support horizontal alignment — use `insert_textbox` with
`align=2`, or measure with `pymupdf.get_text_length()`.

## 4. TOC page numbers stay as placeholders

**Symptom.** `··` in the contents; build log says `located 0/11 headings`.

**Cause A.** Font-size mismatch (see §1): the locator looks for headings at the
CSS size and finds nothing when everything is scaled.
**Cause B.** The needle includes a section number that is rendered as a separate
span with no separating space; the joined line text is `1.2项目背景` while the
needle is `1.2 项目背景`.

**Fix.** Normalise (strip all whitespace) before comparing, search only spans at
the heading's size (±1 pt), and walk headings **in document order**, advancing a
page cursor — otherwise an early heading can match a later repeated title.

## 5. `@page` margin boxes do not work

`@page { @top-center { content: "…" } }` and `position: running(head)` are CSS
Generated Content for Paged Media. Chrome does not implement them.
→ Print first, then stamp header/footer and page numbers with PyMuPDF (§3).
Same reason the TOC needs two passes: `target-counter()` is unimplemented too.

## 6. Chinese becomes unsearchable Type3

Chrome vectorises OTF/CFF CJK fonts (e.g. Noto Sans SC `.otf`) into Type3 glyph
procedures: sharp, but the text layer is lost and the file balloons.
→ Put a TrueType family first: `"Microsoft YaHei"`. `qa_check.py` warns when
`Type3` appears in the font list.

## 7. 中文 inside `\text{}` looks like a different typeface

KaTeX's text font has no CJK glyphs, so Chrome falls back to SimSun (a Song
face) inside a Hei document.
→ `.katex .text, .katex .mord.text { font-family: "Microsoft YaHei", sans-serif; }`
The `.mord.text` part matters: KaTeX wraps `\text` in `.mord.text`, which has
higher specificity than a bare `.text` rule.

## 8. Math is raw `$…$` in the PDF

`--print-to-pdf` can capture the page before browser-side KaTeX finishes.
→ Pre-render server-side (`scripts/math.js`). In the inline regex use `[^$]`
(not `[^\n$]`), otherwise formulas you wrapped across source lines are skipped.

## 9. A page is 90 % empty

**Symptom.** A chapter overflows by 2–3 lines; the next chapter forces a page
break; the leftover lines sit alone on a page.

**Cause.** Content length vs. fixed chapter boundaries — not a CSS bug.
**Fix.** Trim the chapter, move a figure to the next chapter, or drop the
chapter break if the document is short. `qa_check.py` flags near-empty pages so
you notice before printing.

## 10. A table loses its header on the second page

`<thead>` repeats only when it is a real table-header group.
→ Always wrap the header row in `<thead>` and the body in `<tbody>`; don't put
the header inside `<tbody>`.

## 11. Numbering disagrees between headings and the TOC

CSS counters on `h2::before` cannot be reused by the TOC (different container),
so the two can drift.
→ Number headings in Python at build time (`number_headings()`), inject
`<span class="secno">`, and let the TOC reuse the same string. One source of
truth.

## 12. A heading sits alone at the foot of a page

`break-after: avoid` looks only at the immediately following block. If that
block is a 12-line paragraph, the engine can honour the rule and still leave the
heading visually stranded above a page break.
→ Wrap heading + first paragraph in `.keep` (`break-inside: avoid`), or keep that
paragraph short. `qa_check.py` reports headings that are the last line on a page.

## 13. Cover feels empty

A cover with a title and an abstract on A4 has a lot of air. That is correct —
covers are typographic. Fill the bottom with the meta block (unit, version,
date, classification), not with decoration.