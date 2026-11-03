#!/usr/bin/env python3
"""Detect imported image boundaries that slice a PDF text line."""
import json
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parents[1]

def audit():
    pymupdf.TOOLS.set_small_glyph_heights(True)
    errors = []
    images = 0
    for config in sorted((ROOT / 'pipeline/configs').glob('*.json')):
        cfg = json.loads(config.read_text())
        if not cfg.get('imported'):
            continue
        data = json.loads((ROOT / 'content' / cfg['id'] / 'document.json').read_text())
        with pymupdf.open(ROOT / cfg['pdf']) as pdf:
            for entry in data['pages']:
                page = pdf[entry['number'] - 1]
                lines = [line for block in page.get_text('dict')['blocks']
                         for line in block.get('lines', [])]
                for block in entry['blocks']:
                    if 'image' not in block:
                        continue
                    images += 1
                    rect = pymupdf.Rect(block['bbox'])
                    for line in lines:
                        bounds = pymupdf.Rect(line['bbox'])
                        overlap = rect & bounds
                        if (not overlap.is_empty and bounds.get_area() > 0
                                and overlap.get_area() / bounds.get_area() > .02
                                and not (rect + (-.05, -.05, .05, .05)).contains(bounds)):
                            errors.append({'paper': cfg['id'], 'id': block['id'],
                                           'page': entry['number'],
                                           'line': ''.join(s['text'] for s in line['spans'])})
    for ident, filename, pdfname in [
            ('rax', 'figs.json', 'rax.pdf'),
            ('bcg', 'crops.json', 'Bundled Contact Gradients.pdf')]:
        rows = json.loads((ROOT / 'site' / ident / 'figs' / filename).read_text())
        with pymupdf.open(ROOT / 'sources' / pdfname) as pdf:
            for item in rows:
                images += 1
                rect = pymupdf.Rect(item['bbox'] if ident == 'bcg' else
                                    [0, item['top'], 595, item['bot']])
                for block in pdf[item['page'] - 1].get_text('dict')['blocks']:
                    for line in block.get('lines', []):
                        bounds = pymupdf.Rect(line['bbox'])
                        overlap = rect & bounds
                        if (not overlap.is_empty and bounds.get_area() > 0
                                and overlap.get_area() / bounds.get_area() > .02
                                and not (rect + (-.05, -.05, .05, .05)).contains(bounds)):
                            errors.append({'paper': ident, 'image': item['file'],
                                           'page': item['page'],
                                           'line': ''.join(s['text'] for s in line['spans'])})
    return {'images': images, 'errors': errors}

if __name__ == '__main__':
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(result['errors']))
