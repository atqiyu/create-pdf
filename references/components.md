# Component reference

Everything below is already styled by `assets/base.css`. Copy the snippets into
`parts/*.html`; override tokens in the document's `theme.css`.

## Page & text

| Element | What it does |
|---|---|
| `.cover` | typographic cover, one per document, detected as the first part |
| `h1` | chapter: `break-before: page`, auto number `1`, rule under |
| `h2` / `h3` | sections, auto `1.1` / `1.1.1` |
| `h4` | unnumbered sub-sub head, for a single paragraph's label |
| `p.lead` | opening paragraph of a chapter, slightly larger |
| `p.small` | 9 pt note |
| `.muted` | secondary grey text |
| `hr` | section separator |
| `ul.tight` / `ol.tight` | list without paragraph spacing |

## Cover

```html
<section class="cover">
  <div class="eyebrow">技术方案 · 2026</div>
  <div class="rule"></div>
  <h1>文档标题</h1>
  <div class="sub">副标题：一句话说明它解决什么</div>
  <p class="abstract">两三行的摘要，供评审快速判断是否相关。</p>
  <div class="spacer"></div>
  <div class="meta">
    <div class="row"><span>编制单位　<b>某某中心</b></span><span>版本　<b>v1.0</b></span></div>
    <div class="row"><span>日期　<b>2026 年 11 月</b></span><span>密级　<b>内部</b></span></div>
    <div class="org">LATIN ORG LINE</div>
  </div>
</section>
```

The cover must stay inside the text block (168 mm). A 210 mm-wide cover makes
Chrome scale the entire document down — see pitfalls §1.

## Figures

```html
<figure class="figure">
  <svg viewBox="0 0 640 180" width="640" height="180" xmlns="…">…</svg>
  <figcaption>图注写清楚“看图应该看到什么”</figcaption>
</figure>
```

- Auto numbering: `图 1`, `图 2` … via CSS counter.
- `break-inside: avoid` keeps figure + caption together.
- Raster images: `<img src="assets/x.png">`, `max-width:100%`.
- Give `<svg>` explicit `width`/`height`; CSS then scales to the block width.
- Tips: stroke 1.4–1.7 units, label ≥ 12 units in a 640-unit viewBox (≈ 7 pt at
  168 mm), text `font-family="'Microsoft YaHei',sans-serif"`.

## Tables

```html
<figure class="table-wrap">
  <figcaption>表题</figcaption>
  <table>
    <thead><tr><th style="width:18%">列</th><th>说明</th></tr></thead>
    <tbody>
      <tr><td><b>粗体行首</b></td><td>内容</td></tr>
    </tbody>
  </table>
</figure>
```

- Auto numbering: `表 1` …; the caption sits **above** the table (academic style).
- `thead` repeats automatically when a table spans pages.
- Rules follow the booktabs convention: 1 pt top, 0.5 pt under the header,
  1 pt bottom; no vertical lines.
- Cell helpers: `.c` centre, `.r` right.

## Callouts

```html
<div class="callout">        <!-- default: blue, “说明/口径” -->
  <div class="ct">口径说明</div><p>…</p>
</div>
<div class="callout warn">   <!-- amber, constraints and risks -->
<div class="callout note">   <!-- green, conclusions and confirmations -->
```

Keep a callout to one idea and ≤ 3 short paragraphs; it never splits across pages.

## Math

```html
<p>覆盖率为 $R=N_{\text{served}}/N_{\text{total}}$。</p>
<div class="math-block">$$C \le \frac{Q\cdot p\cdot T}{\lambda}$$</div>
```

- Inline fractions blow up line height; in tight tables write `(a+b)/c`.
- `\text{中文}` is forced to the UI font by CSS (KaTeX has no CJK glyphs).

## KPI row

```html
<div class="kpis">
  <div class="kpi"><div class="k">数据时效</div><div class="v">≤ 5 分钟</div></div>
  …
</div>
```

Three is the comfortable maximum; it works best right after a chapter's goals.

## Quote, code, references

```html
<blockquote><p>一句需要被单独强调的话。</p></blockquote>

<pre><code>命令行或示例代码</code></pre>

<div class="refs"><ol><li>文献条目。</li></ol></div>
```

## Two columns (sparingly)

```html
<div class="cols c2"><div>左</div><div>右</div></div>
```

Flex columns are fine for short paired blocks (a table and a note, a formula and
its explanation). Avoid them for long prose — across a page break, columns get
out of sync.

## Layout diagnosis

- A figure drifting far from its caption → the SVG's viewBox has more blank
  space than content; crop the viewBox and the height attribute together.
- A nearly blank page → a chapter overflowed by a few lines; trim, or move a
  figure/table to the next chapter.
- A heading alone at the bottom → `break-after: avoid` only looks one block
  ahead; wrap heading + first paragraph in `.keep` if it persists.
- Loose justified lines → the line contains a long unbreakable token (URL,
  code, wide math); set `.nowrap` on short tokens or shorten them.