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
        buttons = ''.join(
            f'<button type="button" class="star" data-value="{value}" '
            f'aria-label="{label}：{value} 星" aria-pressed="false" title="{value} 星">☆</button>'
            for value in range(1, 6))
        ratings.append(f'<div><dt>{label}</dt><dd class="stars" role="group" '
                       f'aria-label="{label}" data-paper="{html.escape(ident)}" '
                       f'data-metric="{key}">{buttons}</dd></div>')
    year = review.get('publication_year')
    if year is not None and (type(year) is not int or not 1900 <= year <= 2100):
        raise ValueError(f'Invalid publication year: {ident}')
    month = review.get('publication_month')
    if month is not None and (year is None or type(month) is not int or not 1 <= month <= 12):
        raise ValueError(f'Invalid publication month: {ident}')
    year_label = str(year) if year is not None else '年份待核实'
    if month is not None:
        year_label += f'.{month}'
    venue = review.get('publication_venue')
    venue_source = review.get('publication_venue_source')
    if not venue or not isinstance(venue_source, str) or not venue_source.startswith(('https://', 'http://')):
        raise ValueError(f'Missing publication venue/source: {ident}')
    # Conference editions and proceedings publication years can differ.
    # Keep both years when the venue already identifies a different edition.
    if year is not None and re.search(rf'\b{year}\b', venue):
        publication_label = re.sub(rf'\b{year}\b', year_label, venue, count=1)
    else:
        venue_name, separator, status = venue.partition(' · ')
        publication_label = f'{venue_name} {year_label}'
        if separator:
            publication_label += f' · {status}'
    venue_note = review.get('publication_venue_note') or f'查看论文出处：{venue}'
    venue_html = (f'<a class="paper-publication" href="{html.escape(venue_source, quote=True)}" '
                  f'target="_blank" rel="noopener noreferrer" '
                  f'aria-label="出处：{html.escape(venue, quote=True)}" '
                  f'title="{html.escape(venue_note, quote=True)}">({html.escape(publication_label)})</a>')
    english_html = html.escape(review['en_title'])
    cover = review['cover']
    cover_path = (ROOT / 'site' / cover['src']).resolve()
    if not cover_path.is_relative_to(ROOT / 'site') or not cover_path.is_file():
        raise ValueError(f'Missing paper cover: {ident}')
    return f'''    <article class="card">
      <h3><a href="{html.escape(ident)}/index.html">{html.escape(title)}</a><span class="paper-en" lang="en"><a href="{html.escape(ident)}/index.html">{english_html}</a> {venue_html}</span></h3>
      <a class="paper-cover" href="{html.escape(ident)}/index.html" aria-label="打开{html.escape(title)}">
        <img src="{html.escape(cover['src'])}" alt="{html.escape(cover['alt'])}" loading="lazy" decoding="async">
      </a>
      <p class="review">{html.escape(review['comment'])}</p>
      <dl class="ratings">{''.join(ratings)}</dl>
      <div class="personal-review">
        <label for="comment-{html.escape(ident)}">我的评语</label>
        <textarea class="user-comment" id="comment-{html.escape(ident)}" data-paper="{html.escape(ident)}" rows="3" maxlength="5000" placeholder="写下你的阅读感受、疑问或结论…" aria-describedby="comment-status-{html.escape(ident)}"></textarea>
        <div class="comment-feedback"><span id="comment-status-{html.escape(ident)}" role="status" aria-live="polite">正在读取…</span><button type="button" class="comment-retry" hidden>重试保存</button></div>
      </div>
    </article>'''


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
    note = '<p class="rating-note">由你评分：每项 5 颗星，点几颗亮几颗；再次点击当前分数可清空。评分自动保存到本机数据库。</p><p id="rating-status" role="status" aria-live="polite"></p>'
    page = re.sub(r'\s*<p class="rating-note">.*?</p>(?:<p id="rating-status"[^>]*>.*?</p>)?', '', page, flags=re.S)
    page = re.sub(r'<h2 class="sec">已收录.*?</h2>', f'<h2 class="sec">已收录 · Papers <span>{len(cards)} 份阅读材料</span></h2>\n  {note}', page, count=1)
    path.write_text(page)
    print(f'Updated index: {len(cards)} compact review cards')


if __name__ == '__main__':
    main()
