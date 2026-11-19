#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Create a minimal, empty document skeleton.

    python scaffold.py my-doc --title "项目名称"

Produces only placeholders — no sample prose, no demo figures — so the author
starts from a blank page:

    my-doc/parts/p00-cover.html      cover with the given fields filled
    my-doc/parts/p01-chapter1.html   one chapter stub
    my-doc/parts/p02-chapter2.html   second chapter stub
    my-doc/theme.css                 empty override file
"""
import os
import sys
import argparse

COVER = """<section class="cover">
  <div class="eyebrow">{kind} · {date}</div>
  <div class="rule"></div>
  <h1>{title}</h1>
  <div class="sub">{subtitle}</div>

  <p class="abstract">{abstract}</p>

  <div class="spacer"></div>

  <div class="meta">
    <div class="row"><span>编制单位　<b>{org}</b></span><span>版本　<b>v1.0</b></span></div>
    <div class="row"><span>日期　<b>{date}</b></span><span>密级　<b>内部</b></span></div>
    <div class="org">ORGANIZATION · DOCUMENT</div>
  </div>
</section>
"""

# Chapter stubs stay deliberately empty: headings plus a placeholder paragraph.
# Everything else (figures, tables, callouts, math) is documented in
# references/components.md so the author adds only what the document needs.
CHAPTER = """<!-- 一章一个文件。h1 自动编号并另起一页；h2 / h3 自动编号 1.1 / 1.1.1。
     可用组件见组件清单。 -->
<h1>第一章标题</h1>
<p class="lead">这一章要回答的问题，一到两句。</p>

<h2>第一节标题</h2>
<p>正文。</p>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--title", default="文档标题")
    ap.add_argument("--subtitle", default="副标题：一句话说明这份文档解决什么")
    ap.add_argument("--kind", default="文档")
    ap.add_argument("--org", default="编制单位")
    ap.add_argument("--date", default="2026 年 11 月")
    ap.add_argument("--abstract", default="摘要：两三行说明这份文档回答什么问题、给谁看、结论是什么。")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    dst = os.path.join(a.target, "parts")
    if os.path.exists(dst) and os.listdir(dst) and not a.force:
        sys.exit(f"{dst} already has files; pass --force to overwrite")
    os.makedirs(dst, exist_ok=True)

    cover = COVER.format(kind=a.kind, date=a.date, title=a.title,
                         subtitle=a.subtitle, abstract=a.abstract, org=a.org)
    open(os.path.join(dst, "p00-cover.html"), "w", encoding="utf-8").write(cover)
    for i in (1, 2):
        p = os.path.join(dst, f"p{i:02d}-chapter{i}.html")
        open(p, "w", encoding="utf-8").write(CHAPTER)

    theme = os.path.join(a.target, "theme.css")
    if not os.path.exists(theme):
        open(theme, "w", encoding="utf-8").write(
            "/* per-document overrides: colours, margins, one-offs */\n")

    skill = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"scaffolded {a.target} (cover + 2 empty chapters). Next:\n"
          f"  python {os.path.join(skill, 'scripts', 'build.py')} "
          f"--dir {a.target} --out {a.target}/out/doc.pdf --title \"{a.title}\"")


if __name__ == "__main__":
    main()