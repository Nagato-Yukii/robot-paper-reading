#!/usr/bin/env python3
"""Snap imported figure/equation crops to complete PDF glyph boundaries.

Nearby prose outside the detected object is excluded at a blank-space boundary.
The original detector rectangle is retained so repeated repair is idempotent.
"""
import argparse
import json
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parents[1]

def complete_crop_rect(page, bbox):
    pymupdf.TOOLS.set_small_glyph_heights(True)
    pg = page
    lines = [(pymupdf.Rect(line['bbox']), ''.join(span['text'] for span in line['spans']))
             for block in page.get_text('dict')['blocks'] for line in block.get('lines', [])]
    original = pymupdf.Rect(bbox)
    rect = original + (-2, -2, 2, 2)
    excluded = []
    for bounds, text in lines:
        intersection = bounds & rect
        if intersection.is_empty:
            continue
        middle = (bounds.y0 + bounds.y1) / 2
        if (len(text.strip()) > 45 and not original.y0 <= middle <= original.y1
                and intersection.height / bounds.height < .55):
            excluded.append(bounds)
        else:
            rect |= bounds
    for bounds in excluded:
        if bounds.y0 >= original.y1 - 1:
            rect.y1 = min(rect.y1, bounds.y0 - .6)
        elif bounds.y1 <= original.y0 + 1:
            rect.y0 = max(rect.y0, bounds.y1 + .6)
    # Tall symbols and adjacent prose can share a vertical band. In that case
    # preserve a complete line, rather than truncating either one to save space.
    for _ in range(30):
        before = tuple(rect)
        for bounds, text in lines:
            intersection = bounds & rect
            if not intersection.is_empty and intersection.get_area() / bounds.get_area() > .005:
                rect |= bounds
        if tuple(rect) == before:
            break
    return rect & page.rect

def repair(ident):
    cfg = json.loads((ROOT / 'pipeline/configs' / (ident + '.json')).read_text())
    path = ROOT / 'content' / ident / 'document.json'
    data = json.loads(path.read_text())
    pdf = pymupdf.open(ROOT / cfg['pdf'])
    for entry in data['pages']:
        page = pdf[entry['number'] - 1]
        for block in entry['blocks']:
            if 'image' not in block:
                continue
            original = block.get('original_bbox', block['bbox'])
            rect = complete_crop_rect(page, original)
            image = page.get_pixmap(matrix=pymupdf.Matrix(3, 3), clip=rect, alpha=False)
            image.save(str(ROOT / 'site' / ident / block['image']))
            block.update(original_bbox=original, bbox=list(rect),
                         image_width=image.width, image_height=image.height,
                         crop_repair='complete-glyph-boundaries-v1')
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ids', nargs='+')
    args = parser.parse_args()
    for ident in args.ids:
        repair(ident)
