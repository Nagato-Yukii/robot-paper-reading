#!/usr/bin/env python3
"""Crop arbitrary regions of a PDF into JPEGs, driven by a JSON spec.

Spec format (list of dicts):
  {"name": "fig1", "page": 1, "x0": 40, "y0": 120, "x1": 300, "y1": 400}
Coordinates are PDF points (1/72 inch), origin at the top-left of the page.
Optional per-item "dpi" (default 200), "pad" (points, default 0).

Usage:
  python3 pipeline/crop.py --pdf sources/paper.pdf --spec _build/paper/floats.json \
      --out site/paper/figs [--dpi 200] [--quality 88]
"""
import argparse, json, os, subprocess

def crop(pdf, item, out_dir, dpi, quality):
    page = int(item["page"])
    pad = float(item.get("pad", 0))
    x0 = max(0.0, float(item["x0"]) - pad)
    y0 = max(0.0, float(item["y0"]) - pad)
    x1 = float(item["x1"]) + pad
    y1 = float(item["y1"]) + pad
    scale = dpi / 72.0
    w = int(round((x1 - x0) * scale))
    h = int(round((y1 - y0) * scale))
    if w < 4 or h < 4:
        raise SystemExit(f"bad box for {item['name']}: {w}x{h}")
    out = os.path.join(out_dir, item["name"])
    subprocess.run([
        "pdftoppm", "-jpeg", "-jpegopt", f"quality={quality}", "-r", str(dpi),
        "-f", str(page), "-l", str(page),
        "-x", str(int(round(x0 * scale))), "-y", str(int(round(y0 * scale))),
        "-W", str(w), "-H", str(h), "-singlefile", pdf, out], check=True)
    return out + ".jpg"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--spec", required=True, help="JSON list of boxes")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--quality", type=int, default=88)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    items = json.load(open(a.spec, encoding="utf-8"))
    for it in items:
        path = crop(a.pdf, it, a.out, int(it.get("dpi", a.dpi)), a.quality)
        print(f"{it['name']:14s} p{it['page']:<3d} -> {path}")

if __name__ == "__main__":
    main()
