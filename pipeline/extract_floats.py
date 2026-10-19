#!/usr/bin/env python3
"""Extract figure/table regions from rax.pdf: bbox caption detection + color-band figure box."""
import re, subprocess, os, json
from PIL import Image, ImageChops

BASE = "/home/shuai/Desktop/papers"
PDF = os.path.join(BASE, "rax.pdf")
OUT = os.path.join(BASE, "rax_zh", "figs")
os.makedirs(OUT, exist_ok=True)
DPI = 200
RENDER_DPI = 120

txt = open(os.path.join(BASE, "rax_bbox.html"), encoding="utf-8").read()
pages = re.findall(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', txt, re.S)


def lines2(body):
    words = re.findall(
        r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>', body)
    d = {}
    for xm, ym, xM, yM, t in words:
        d.setdefault(round(float(ym), 1), []).append((float(xm), float(xM), float(yM), t))
    out = []
    for y in sorted(d):
        ws = sorted(d[y], key=lambda w: w[0])
        out.append(dict(y=y, y1=max(w[2] for w in ws), x0=min(w[0] for w in ws),
                        x1=max(w[1] for w in ws), text=" ".join(w[3] for w in ws)))
    return out


def color_bands(png, thr=28, minfrac=3):
    im = Image.open(png).convert("RGB")
    W, H = im.size
    r, g, b = im.split()
    mx = ImageChops.lighter(ImageChops.lighter(r, g), b)
    mn = ImageChops.darker(ImageChops.darker(r, g), b)
    d = ImageChops.subtract(mx, mn).point(lambda v: 255 if v > thr else 0)
    rows = d.resize((1, H), Image.BOX).load()
    bands, inb, s = [], False, 0
    for y in range(H):
        if rows[0, y] > minfrac:
            if not inb:
                s, inb = y, True
            e = y
        elif inb:
            bands.append((s, e)); inb = False
    if inb:
        bands.append((s, e))
    sc = 72.0 / RENDER_DPI
    return [(a * sc, b * sc) for a, b in bands]


results = []
TOP_MARGIN, BOT_MARGIN = 55.0, 790.0


def ink_profile(png, thr=205):
    im = Image.open(png).convert("L")
    W, H = im.size
    d = im.point(lambda v: 255 if v < thr else 0)
    rp = d.resize((1, H), Image.BOX).load()
    return dict(rows=[rp[0, y] for y in range(H)], sc=72.0 / RENDER_DPI)

for i, (w, h, body) in enumerate(pages, 1):
    L = lines2(body)
    if not L:
        continue
    words = re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>', body)
    bars = [(float(a), float(b)) for a, b, c, d, t in words if "|" in t]
    png = os.path.join(BASE, "tmp", f"lp-{i:02d}.png")
    for j, ln in enumerate(L):
        m = re.match(r'^(Figure|Table|Algorithm)\s*(\d+)\b', ln["text"])
        if not m or ln["x0"] > 200:
            continue
        if not any(abs(by - ln["y"]) < 12 and -3 < (bx - ln["x0"]) < 90 for bx, by in bars):
            continue
        kind, num = m.group(1), m.group(2)
        k = j
        while k + 1 < len(L) and (L[k+1]["y"] - L[k]["y"]) < 19 and (L[k+1]["y"] - ln["y"]) < 100:
            k += 1
        cap_top, cap_bot = ln["y"], L[k]["y1"]
        top = bot = None
        if kind == "Figure":
            if os.path.exists(png):
                bands = color_bands(png)
                cand = [b for b in bands if b[1] < cap_top + 2 and b[1] > cap_top - 460]
                if cand:
                    merged = [cand[-1]]
                    for bb in reversed(cand[:-1]):
                        if merged[0][0] - bb[1] < 48:
                            merged.insert(0, bb)
                    ct = max(TOP_MARGIN, merged[0][0] - 9)
                    # trim a sliver of body text above the figure: skip past the next blank row
                    ir = ink_profile(png)
                    rows, sc = ir["rows"], ir["sc"]
                    k2 = int(ct / sc)
                    if k2 < len(rows) and rows[k2] > 2:
                        lim = int((ct + 22) / sc)
                        while k2 < len(rows) and k2 < lim and rows[k2] > 2:
                            k2 += 1
                        ct = max(ct, min(k2 * sc - 1, cap_top - 90))
                    if cap_top - ct > 90:
                        top, bot = ct, cap_top - 6
            if top is None:
                s = j - 1
                while s >= 0 and L[s]["text"].strip() in ("|", ""):
                    s -= 1
                if s < 0:
                    continue
                top = TOP_MARGIN
                while s - 1 >= 0:
                    if (L[s]["y"] - L[s-1]["y"]) >= 18 and (cap_top - L[s]["y"]) >= 110:
                        top = L[s]["y"] - 8
                        break
                    s -= 1
                bot = cap_top - 6
            if bot - top > 640:
                top = bot - 640
        else:
            s = k + 1
            if s >= len(L):
                continue
            top = cap_bot + 4
            bot = None
            while s + 1 < len(L):
                if (L[s+1]["y"] - L[s]["y"]) >= 18 and (L[s]["y1"] - cap_bot) >= 55:
                    bot = L[s]["y1"] + 8
                    break
                s += 1
            if bot is None:
                bot = min(BOT_MARGIN, L[-1]["y1"] + 8)
        if bot - top < 40:
            continue
        results.append(dict(page=i, kind=kind, num=int(num), top=round(top, 1),
                            bot=round(bot, 1), caption=ln["text"], cap_top=cap_top,
                            cap_bot=round(cap_bot, 1)))

best = {}
for r in results:
    key = (r["kind"], r["num"])
    if key not in best or (r["bot"] - r["top"]) > (best[key]["bot"] - best[key]["top"]):
        best[key] = r
results = sorted(best.values(), key=lambda r: (r["kind"] != "Figure", r["num"]))

for r in results:
    p, top, bot = r["page"], r["top"], r["bot"]
    name = f"{r['kind'].lower()}{r['num']:02d}_p{p:02d}"
    r["file"] = name + ".jpg"
    y = int(top * DPI / 72.0)
    H = int((bot - top) * DPI / 72.0)
    subprocess.run(["pdftoppm", "-jpeg", "-jpegopt", "quality=86", "-r", str(DPI),
                    "-f", str(p), "-l", str(p), "-x", "0", "-y", str(y),
                    "-W", str(int(595 * DPI / 72)), "-H", str(H), "-singlefile",
                    PDF, os.path.join(OUT, name)], check=True)

json.dump(results, open(os.path.join(OUT, "figs.json"), "w"), indent=1, ensure_ascii=False)
print(f"{len(results)} floats")
for r in results:
    print(f"{r['kind']} {r['num']:2d} p{r['page']:2d} y={r['top']:6.1f}-{r['bot']:6.1f} "
          f"h={r['bot']-r['top']:5.1f} {r['caption'][:46]}")
