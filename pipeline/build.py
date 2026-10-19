#!/usr/bin/env python3
"""Assemble content/<id>/*.html + pipeline/template.html into site/<id>/index.html.

Usage:  python3 pipeline/build.py pipeline/configs/rax.json
Config keys:
  id, content, out, pdf, brand, brand_sub, title, kicker, accent, accent_soft
"""
import os, re, glob, json, html, sys, shutil
from equation_links import link_numbered_math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build(cfg_path):
    cfg = json.load(open(cfg_path, encoding="utf-8"))
    cid = cfg["id"]
    content_dir = os.path.join(ROOT, cfg.get("content", f"content/{cid}"))
    out_dir = os.path.join(ROOT, cfg.get("out", f"site/{cid}"))
    os.makedirs(out_dir, exist_ok=True)

    pdf_rel = cfg.get("pdf", "")
    if pdf_rel:
        pdf_rel = os.path.relpath(os.path.join(ROOT, pdf_rel), out_dir)

    parts = sorted(glob.glob(os.path.join(content_dir, "*.html")))
    if not parts:
        sys.exit(f"no parts in {content_dir}")
    body = "\n".join(open(p, encoding="utf-8").read() for p in parts)
    body = body.replace("{{PDF}}", pdf_rel)
    body = link_numbered_math(body)

    toc = []

    def add_id(m):
        attrs, inner = m.group(1), m.group(2)
        num = re.search(r'data-num="([^"]+)"', attrs)
        idx = len(toc) + 1
        sid = "sec-%02d" % idx
        plain = re.sub(r'<a class="pg".*?</a>', "", inner, flags=re.S)
        plain = re.sub(r'<span class="en-h".*?</span>', "", plain, flags=re.S)
        plain = re.sub(r"<[^>]+>", "", plain)
        plain = html.unescape(plain).replace("\xa0", " ")
        plain = re.sub(r"\s+", " ", plain).strip()
        lab = (num.group(1) if num else str(idx)).strip()
        if not re.match(r"^(\d+(\.\d+)*|[A-H]|附录|摘要|参考文献)$", lab):
            lab = ""
        if lab and plain.startswith(lab):
            plain = plain[len(lab):].strip()
        zh = plain.split("｜")[0].strip()
        toc.append((sid, zh, lab))
        return '<h2 id="%s"%s>%s</h2>' % (sid, attrs, inner)

    body = re.sub(r"<h2([^>]*)>(.*?)</h2>", add_id, body, flags=re.S)

    nav = "\n".join(
        '<a href="#%s"><span class="n">%s</span>%s</a>' % (sid, num, html.escape(zh))
        for sid, zh, num in toc)

    math_css = math_js = ""
    if cfg.get("math"):
        src = os.path.join(ROOT, "pipeline", "vendor", "katex")
        dst = os.path.join(out_dir, "vendor", "katex")
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        math_css = '<link rel="stylesheet" href="vendor/katex/katex.min.css">'
        math_js = (
            '<script defer src="vendor/katex/katex.js"></script>\n'
            '<script defer src="vendor/katex/auto-render.js"></script>\n'
            '<script>document.addEventListener("DOMContentLoaded",function(){'
            'renderMathInElement(document.body,{delimiters:['
            '{left:"\\\\[",right:"\\\\]",display:true},'
            '{left:"\\\\(\",right:"\\\\)",display:false}],throwOnError:false});});</script>')

    tpl = open(os.path.join(ROOT, "pipeline", "template.html"), encoding="utf-8").read()
    subs = {
        "{{TITLE}}": cfg.get("title", cid),
        "{{BRAND}}": cfg.get("brand", cid),
        "{{BRAND_SUB}}": cfg.get("brand_sub", ""),
        "{{TRANSLATION_CREDIT}}": html.escape(cfg.get("translation_credit",
            "译文润色：Gemini3.8 medium"
            if cfg.get("translation_model") == "gemini-3.8-flash-medium" else "")),
        "{{KICKER}}": cfg.get("kicker", ""),
        "{{ACCENT}}": cfg.get("accent", "#3f51b5"),
        "{{ACCENT_SOFT}}": cfg.get("accent_soft", "#eceffb"),
        "{{MATH_CSS}}": math_css,
        "{{MATH_JS}}": math_js,
        "{{TOC}}": nav,
        "{{BODY}}": body,
    }
    out = tpl
    for k, v in subs.items():
        out = out.replace(k, v)

    out_path = os.path.join(out_dir, "index.html")
    open(out_path, "w", encoding="utf-8").write(out)
    print(f"built {out_path}  ({len(out)//1024} KB, {len(toc)} sections, {len(parts)} parts)")
    return out_path


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "pipeline", "configs", "rax.json")
    build(path)
