#!/usr/bin/env python3
"""Build compact library cards with a reading comment and three review scores."""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORE_LABELS = (('influence', '影响力'), ('experiments', '实验完整性'), ('reference', '方法可参考性'))


def render_card(ident, title, review):
    ratings = []
    for key, label in SCORE_LABELS:
        score = review['scores'][key]
        if score is not None and (type(score) is not int or not 1 <= score <= 5):
            raise ValueError(f'Invalid {key} score for {ident}')
        value = '不适用' if score is None else f'{score}<small> / 5</small>'
        ratings.append(f'<div><dt>{label}</dt><dd>{value}</dd></div>')
    return f'''    <a class="card" href="{html.escape(ident)}/index.html">
      <h3>{html.escape(title)}</h3>
      <p class="review">{html.escape(review['comment'])}</p>
      <dl class="ratings">{''.join(ratings)}</dl>
    </a>'''


def main():
    path = ROOT / 'site/index.html'
    page = path.read_text()
    reviews = json.loads((ROOT / 'content/reading-reviews.json').read_text())
    configs = {p.stem: json.loads(p.read_text()) for p in (ROOT / 'pipeline/configs').glob('*.json')}
    if set(reviews['papers']) != set(configs):
        raise ValueError('Each paper must have exactly one reading review')
    cards = []
    for ident, review in reviews['papers'].items():
        cfg = configs[ident]
        title = cfg.get('zh_title') or cfg['title'].removesuffix(' · 中英对照')
        cards.append(render_card(ident, title, review))
    grid = '  <div class="grid">\n' + '\n'.join(cards) + '\n  </div>\n\n'
    page, count = re.subn(r'  <div class="grid">.*?(?=  <footer>)', lambda _: grid, page, count=1, flags=re.S)
    if count != 1:
        raise ValueError('Cannot locate library card grid')
    note = '<p class="rating-note">阅读初评 · 5 分制；影响力按方向价值与带动潜力评估，非引用量排名；实验看验证覆盖，方法看借鉴价值。</p>'
    page = re.sub(r'\s*<p class="rating-note">.*?</p>', '', page, flags=re.S)
    page = re.sub(r'<h2 class="sec">已收录.*?</h2>', f'<h2 class="sec">已收录 · Papers <span>{len(cards)} 份阅读材料</span></h2>\n  {note}', page, count=1)
    path.write_text(page)
    print(f'Updated index: {len(cards)} compact review cards')


if __name__ == '__main__':
    main()
