"""Render docs-src/**/*.md into the PDF deliverables inside the 8 phase folders.

Edit docs-src/project.json (team id, dates, links) or any .md file, then run:
    pip install markdown playwright && playwright install chromium
    python tools/build_docs.py
Set CHROMIUM_PATH to use an existing Chromium binary.
"""
import json
import os
import re
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs-src"
CSS = """
body{font-family:Georgia,'Times New Roman',serif;font-size:11pt;line-height:1.45;color:#111;max-width:100%}
h1{font-size:20pt;text-align:center;margin:0 0 10pt}h2{font-size:14pt;margin:16pt 0 6pt;border-bottom:1px solid #999}h3{font-size:12pt;margin:12pt 0 4pt}
table{border-collapse:collapse;width:100%;margin:6pt 0 10pt;font-size:9.5pt;page-break-inside:auto}tr{page-break-inside:avoid}
th,td{border:1px solid #555;padding:4pt 6pt;vertical-align:top;text-align:left}th{background:#e8e8e8}
pre{background:#f4f4f4;border:1px solid #bbb;padding:8pt;font-size:8.2pt;line-height:1.25;white-space:pre;overflow:hidden}
code{font-family:Consolas,monospace;font-size:9pt}img{max-width:100%;border:1px solid #bbb;margin:4pt 0}
.hdr td:first-child{width:28%;font-weight:bold;background:#f0f0f0}
"""


def header(marks: str) -> str:
    return ("<table class='hdr'><tr><td>Date</td><td>{{date}}</td></tr><tr><td>Team ID</td><td>{{team_id}}</td></tr>"
            f"<tr><td>Project Name</td><td>{{{{project_name}}}}</td></tr><tr><td>Maximum Marks</td><td>{marks}</td></tr></table>\n")


def render(md_text: str, values: dict) -> str:
    md_text = re.sub(r"\{\{HEADER:(.+?)\}\}", lambda m: header(m.group(1)), md_text)
    for key, value in values.items():
        md_text = md_text.replace("{{" + key + "}}", value)
    return markdown.markdown(md_text, extensions=["tables", "fenced_code", "md_in_html"])


def main() -> None:
    values = json.loads((SRC / "project.json").read_text())
    files = sorted(p for p in SRC.rglob("*.md"))
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=os.getenv("CHROMIUM_PATH") or None)
        page = browser.new_page()
        for md in files:
            rel = md.relative_to(SRC)
            html = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{render(md.read_text(), values)}</body></html>"
            tmp = SRC / "_tmp.html"          # inside docs-src so relative image paths (assets/...) resolve
            tmp.write_text(html)
            page.goto(tmp.as_uri())
            out = ROOT / rel.with_suffix(".pdf")
            out.parent.mkdir(parents=True, exist_ok=True)
            page.pdf(path=str(out), format="A4", margin={"top": "15mm", "bottom": "15mm", "left": "15mm", "right": "15mm"})
            print("built", out.relative_to(ROOT))
        browser.close()
    (SRC / "_tmp.html").unlink(missing_ok=True)


if __name__ == "__main__":
    main()
