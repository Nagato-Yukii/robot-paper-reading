#!/usr/bin/env python3
"""Import a PDF library with layout crops, offline translation, and equation links.

Requires requirements-import.txt; model is the official Argos English->Chinese 1.9
package (OPUS-MT, CC BY 4.0). Model files stay outside the repository.
"""
import argparse
import hashlib
import html
import json
import re
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAPERS = {
    'hiking_in_the_wild': ('hiking', 'Hiking in the Wild', '野外徒步：可扩展的人形机器人感知跑酷框架', '感知 · 人形运动'),
    'ase': ('ase', 'ASE', 'ASE：物理仿真角色的大规模可复用对抗技能嵌入', '技能学习 · 角色控制'),
    'lswm': ('lswm', 'LSWM', 'LSWM：用于双足强化学习运动控制的长短历史世界模型', '世界模型 · 双足运动'),
    'robotics-transformer1': ('rt1', 'RT-1', 'RT-1：面向规模化真实机器人控制的 Robotics Transformer', '机器人学习 · 操作'),
    'towards bridging the gap': ('bridging-gap', 'Bridging the Gap', '弥合差距：面向多种足式机器人的系统化仿真到现实迁移', '仿真到现实 · 足式机器人'),
    'vision-language-action models transfer': ('vla-transfer', 'VLA Transfer', '视觉语言动作模型的迁移', 'VLA · 迁移学习'),
    'wham': ('wham', 'WHAM', 'WHAM：世界坐标下的人体运动重建', '人体运动 · 视觉'),
    'zhihu_机器人强化学习与关节pd控制': ('rl-pd-control', 'RL & PD Control', '机器人强化学习与关节 PD 控制', '中文资料 · 关节控制'),
    'h-infinity control': ('h-infinity', 'H-infinity Control', 'H∞ 控制', '控制理论 · 鲁棒控制'),
    'any2track': ('any2track', 'Any2Track', 'Any2Track：在任意扰动下跟踪任意运动', '运动跟踪 · 鲁棒控制'),
    'gvhmr': ('gvhmr', 'GVHMR', 'GVHMR：通过重力视角坐标恢复世界坐标系下的人体运动', '人体运动 · 三维重建'),
    'asap': ('asap', 'ASAP', 'ASAP：对齐仿真与现实物理以实现敏捷人形技能', '人形运动 · 仿真到现实'),
    'dreamwaq': ('dreamwaq', 'DreamWaQ', 'DreamWaQ：通过隐式地形想象学习鲁棒足式运动', '足式运动 · 状态估计'),
    'robust_humanoid_walking': ('robust-walking', 'Robust Humanoid Walking', '鲁棒人形机器人行走', '人形运动 · 鲁棒行走'),
    'almi': ('almi', 'ALMI', 'ALMI：用于人形策略学习的对抗运动控制与动作模仿', '对抗学习 · 动作模仿'),
    'him': ('him', 'HIM', 'HIM：人形运动控制', '人形运动 · 控制'),
    'kungfubot2': ('kungfubot2', 'KungfuBot2', 'KungfuBot2：学习多样化的人形全身运动技能', '人形机器人 · 全身控制'),
    'pbhc': ('kungfubot', 'KungfuBot / PBHC', 'KungfuBot：面向高动态技能学习的物理人形全身控制', '人形机器人 · 动态技能'),
    'exbody': ('exbody', 'ExBody', 'ExBody：富有表现力的人形全身控制', '人形机器人 · 全身控制'),
    'a reduction of imitation learning and structured prediction to no-regret online learning': ('dagger', 'DAgger', '将模仿学习与结构化预测归约到无遗憾在线学习', '模仿学习 · 在线学习'),
    'beyondmimic': ('beyondmimic', 'BeyondMimic', 'BeyondMimic：通过引导扩散实现从运动跟踪到通用人形控制', '动作模仿 · 扩散策略'),
    'visualmimic': ('visualmimic', 'VisualMimic', 'VisualMimic：视觉动作模仿', '视觉 · 动作模仿'),
    'learning_from_failures': ('learning-failures', 'Learning from Failures', '从失败中学习：结合情景记忆的高效强化学习控制', '强化学习 · 情景记忆'),
    'zest': ('zest', 'ZEST', 'ZEST：面向运动型机器人控制的零样本具身技能迁移', '技能迁移 · 机器人控制'),
}

def plain(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'!\[[^]]*\]\([^)]*\)', '', text)
    text = re.sub(r'\[([^]]+)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'<br\s*/?>', ' ', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'(?m)^\s*[#>]+\s*', '', text)
    text = text.replace('**', '').replace('_', '')
    text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)
    return re.sub(r'\s+', ' ', text).strip()

class OfflineTranslator:
    def __init__(self, model):
        import ctranslate2
        import sentencepiece
        self.sp = sentencepiece.SentencePieceProcessor(model_file=str(model/'sentencepiece.model'))
        self.engine = ctranslate2.Translator(str(model/'model'), device='cpu', compute_type='int8',
                                            inter_threads=2, intra_threads=4)
        self.cache_file = ROOT/'_work/translation-cache.json'
        self.cache_file.parent.mkdir(exist_ok=True)
        self.cache = json.loads(self.cache_file.read_text()) if self.cache_file.exists() else {}

    def translate(self, texts):
        pending = list(dict.fromkeys(t for t in texts if t and t not in self.cache))
        jobs, owners = [], []
        for text in pending:
            # Short chunks avoid encoder/output truncation on long PDF paragraphs.
            sentences = re.split(r'(?<=[.!?;])\s+(?=[A-Z0-9(])', text)
            chunks, current = [], ''
            for sentence in sentences:
                words = sentence.split()
                for start in range(0, len(words), 55):
                    piece = ' '.join(words[start:start+55])
                    if current and len(self.sp.encode(current+' '+piece)) > 140:
                        chunks.append(current); current = ''
                    current = (current+' '+piece).strip()
            if current: chunks.append(current)
            for chunk in chunks:
                jobs.append(self.sp.encode(chunk, out_type=str)); owners.append(text)
        results = {}
        for start in range(0, len(jobs), 48):
            batch = self.engine.translate_batch(jobs[start:start+48], beam_size=4,
                max_decoding_length=384, repetition_penalty=1.1, max_batch_size=48)
            for owner, result in zip(owners[start:start+48], batch):
                translated = self.sp.decode(result.hypotheses[0]).replace('▁', '').strip()
                results.setdefault(owner, []).append(translated)
        for text in pending:
            translated = ''.join(results.get(text, []))
            for before, after in [('政策','策略'),('可分辨的模拟','可微分仿真'),('可差别模拟','可微分仿真'),
                                  ('强化教学','强化学习'),('处罚','惩罚'),('机器人动力学的分析梯度','机器人动力学的解析梯度')]:
                translated = translated.replace(before,after)
            if not translated: raise RuntimeError('Empty translation: '+text[:100])
            self.cache[text] = translated
        self.cache_file.write_text(json.dumps(self.cache, ensure_ascii=False))
        return [self.cache.get(t, '') for t in texts]


def labels_in_formula(page, box):
    import pymupdf
    rect = pymupdf.Rect(box)
    # Formula numbers are separate PDF lines, usually right aligned.
    found = []
    for block in page.get_text('dict', clip=rect+(-2,-2,2,2))['blocks']:
        for line in block.get('lines', []):
            text = ''.join(s['text'] for s in line['spans']).strip()
            m = re.fullmatch(r'\(\s*([A-Z]?\.?\d+(?:\.\d+)*[a-z]?)\s*\)', text)
            if m and line['bbox'][0] > rect.x0 + rect.width*.55:
                found.append(m.group(1))
    if not found:
        raw = page.get_textbox(rect).strip()
        m = re.search(r'\(\s*([A-Z]?\.?\d+(?:\.\d+)*[a-z]?)\s*\)\s*[,.;]?\s*$', raw)
        if m: found.append(m.group(1))
    return list(dict.fromkeys(found))


def save_crop(page, rect, path, dpi=200):
    import pymupdf
    rect = (pymupdf.Rect(rect)+(-2,-2,2,2)) & page.rect
    if rect.is_empty: return
    pix = page.get_pixmap(matrix=pymupdf.Matrix(dpi/72,dpi/72), clip=rect, alpha=False)
    pix.save(str(path))


def extract(pdf, ident, output):
    import pymupdf
    import pymupdf4llm
    doc = pymupdf.open(pdf)
    print(f'EXTRACT {ident}: {len(doc)} pages',flush=True)
    # Layout model orders columns and identifies tables, figures, and display math.
    chunks = pymupdf4llm.to_markdown(doc, page_chunks=True, use_ocr=False, write_images=False)
    pages, title, in_refs = [], doc.metadata.get('title','').strip(), False
    for index, chunk in enumerate(chunks):
        page = doc[index]
        blocks = []
        for n, box in enumerate(chunk['page_boxes']):
            kind = box['class']
            raw = chunk['text'][slice(*box['pos'])]
            text = plain(raw)
            if kind in ('page-header','page-footer'): continue
            if kind == 'title' and not title: title = text
            if kind == 'section-header':
                if re.search(r'\b(references|bibliography)\b', text, re.I): in_refs = True
                elif re.search(r'\b(appendix|supplement|acknowledg)\b',text,re.I): in_refs = False
            b = {'id':f'p{index+1}-b{n}', 'kind':kind, 'bbox':list(box['bbox']),
                 'en':text, 'reference':in_refs}
            if kind in ('formula','picture','table','code'):
                asset=f'p{index+1:03d}-{n:03d}.png'
                save_crop(page,box['bbox'],output/'figs'/asset)
                b['image']='figs/'+asset
                b['labels']=labels_in_formula(page,box['bbox']) if kind=='formula' else []
            elif text:
                # Exact source crop is available for inline math and extraction ambiguities.
                asset=f'p{index+1:03d}-{n:03d}-source.png'
                save_crop(page,box['bbox'],output/'figs'/asset,150)
                b['source_image']='figs/'+asset
            else: continue
            blocks.append(b)
        # Detect numbered math missed by the layout model without assigning new numbers.
        known = {x for b in blocks for x in b.get('labels',[])}
        for rawblock in page.get_text('dict')['blocks']:
            for line in rawblock.get('lines',[]):
                text=''.join(s['text'] for s in line['spans']).strip()
                m=re.fullmatch(r'\(\s*([A-Z]?\.?\d+(?:\.\d+)*[a-z]?)\s*\)',text)
                if not m or m.group(1) in known: continue
                x0,y0,x1,y1=line['bbox']
                if x0 < page.rect.width*.35: continue
                candidates=[b for b in blocks if b['bbox'][1]-8 <= (y0+y1)/2 <= b['bbox'][3]+8
                            and b['bbox'][0] < x0 and b['bbox'][2] >= x0-25]
                if not candidates: continue
                target=min(candidates,key=lambda b:abs((b['bbox'][1]+b['bbox'][3])/2-(y0+y1)/2))
                # Require non-prose context to avoid treating numbered lists as equations.
                if target['kind']!='formula' and re.search(r'[A-Za-z]{5,}',target['en']): continue
                if 'image' not in target:
                    target['image']=target.pop('source_image');target['kind']='formula'
                target.setdefault('labels',[]).append(m.group(1));known.add(m.group(1))
        pix=page.get_pixmap(matrix=pymupdf.Matrix(1.3,1.3),alpha=False)
        pix.save(str(output/'figs'/f'page-{index+1:03d}.jpg'),jpg_quality=85)
        pages.append({'number':index+1,'blocks':blocks})
    return {'title':title,'pages':pages,'page_count':len(doc)}


def eq_id(label): return 'eq-'+label.replace('.','-')


def repair_numbered_equations(data, pdf, output):
    """Recover display equations merged into prose by the layout detector."""
    import pymupdf
    additions = 0
    for page_data in data['pages']:
        page = pdf[page_data['number']-1]
        known = {label for b in page_data['blocks'] for label in b.get('labels', [])}
        for rawblock in page.get_text('dict')['blocks']:
            for line in rawblock.get('lines', []):
                text = ''.join(span['text'] for span in line['spans']).strip()
                match = re.search(r'\(\s*([A-Z]?\.?[1-9]\d?(?:\.\d+)*[a-z]?)\s*\)\s*[,.;]?\s*$', text)
                if not match or match.group(1) in known: continue
                label = match.group(1)
                # Prose, numbered lists, citations and table cells are not equations.
                left = text[:match.start()]
                if left and (re.search(r'[A-Za-z]{5,}', left) or not re.search(r'[=+−∥∈𝑎-𝑧α-ω()|]|[A-Za-z]\d', left)):
                    continue
                x0,y0,x1,y1 = line['bbox']
                right_edge = x1/page.rect.width
                if not (right_edge > .75 or .43 < right_edge < .53): continue
                candidates = [b for b in page_data['blocks']
                    if b['bbox'][1]-9 <= (y0+y1)/2 <= b['bbox'][3]+5
                    and b['bbox'][0] < x1-8 and b['bbox'][2] >= x1-28]
                if not candidates: continue
                target = min(candidates,key=lambda b:abs((b['bbox'][1]+b['bbox'][3])/2-(y0+y1)/2))
                if target['kind'] in ('table','caption'): continue
                if target['kind']=='picture' and (left.strip() or y0-target['bbox'][1]>30): continue
                if target['kind'] == 'formula':
                    target.setdefault('labels',[]).append(label)
                    rect = pymupdf.Rect(target['bbox']) | pymupdf.Rect(line['bbox'])
                    target['bbox'] = list(rect)
                    save_crop(page,rect,output/target['image'])
                else:
                    # Keep the complete prose block too; the source crop is authoritative.
                    math_lines=[l for raw in page.get_text('dict')['blocks'] for l in raw.get('lines',[])
                        if y0-16 <= l['bbox'][1] <= y1+8
                        and l['bbox'][0] >= target['bbox'][0]-4
                        and l['bbox'][2] <= target['bbox'][2]+4
                        and not re.search(r'[A-Za-z]{5,}', ''.join(s['text'] for s in l['spans']))]
                    rect=[min(l['bbox'][0] for l in math_lines),min(l['bbox'][1] for l in math_lines),
                          max(l['bbox'][2] for l in math_lines),max(l['bbox'][3] for l in math_lines)] if math_lines else [target['bbox'][0],y0-12,target['bbox'][2],y1+8]
                    if target['kind']=='picture' and rect[3]<target['bbox'][3]-40:
                        target['bbox'][1]=rect[3]+7
                        save_crop(page,target['bbox'],output/target['image'])
                    ident = target['id']+'-eq-'+label.replace('.','-')
                    image = 'figs/'+ident+'.png'
                    save_crop(page,rect,output/image)
                    block = {'id':ident,'kind':'formula','bbox':rect,'en':text,
                             'image':image,'labels':[label],'recovered':True}
                    page_data['blocks'].insert(page_data['blocks'].index(target),block)
                known.add(label);additions += 1
    return additions


def render(data, cfg):
    override_path=ROOT/'content'/cfg['id']/'translation_overrides.json'
    if override_path.exists():
        overrides=json.loads(override_path.read_text())
        for page in data['pages']:
            for block in page['blocks']:
                if block['id'] in overrides:block['zh']=overrides[block['id']]
    equations = {}
    candidates = {}
    locations = {}
    anchors = {}
    for pos, block in enumerate(b for page in data['pages'] for b in page['blocks']):
        locations[block['id']] = pos
        for label in block.get('labels', []):
            anchor = eq_id(label)
            if label in candidates: anchor += '-'+block['id']
            key = (block['id'],label)
            anchors[key] = anchor
            candidates.setdefault(label,[]).append(key)
            equations[label if len(candidates[label])==1 else label+'@'+block['id']] = block['id']
    backlinks = {key:[] for key in anchors}
    def resolve(label, block_id):
        return min(candidates[label], key=lambda key:abs(locations[key[0]]-locations[block_id]))
    def linked(text, block_id, lang):
        # Only link explicit equation cues. Bare numeric tuples are ambiguous.
        # Extend the cue over lists/ranges, e.g. Eqs. (3), (4) and (5).
        pattern = r'(?:\b(?:[Ee]q(?:uation)?s?\.?|[Ee]xpressions?)\s*|(?:公式|方程|式)\s*)\(?[A-Z]?\.?\d+(?:\.\d+)*[a-z]?\)?(?:\s*(?:,|and|or|to|through|–|—|-|和|至|、)\s*\(?[A-Z]?\.?\d+(?:\.\d+)*[a-z]?\)?)*'
        def replace_cue(match):
            cue=match.group(0)
            def replace_number(number):
                label=number.group(0).strip('() ')
                resolved_label=label if label in candidates else label+'a'
                if resolved_label not in candidates: return html.escape(number.group(0))
                target = resolve(resolved_label,block_id)
                ref=f'ref-{block_id}-{lang}-{label}-{len(backlinks[target])+1}'
                backlinks[target].append(ref)
                return f'<a class="eq-ref" id="{ref}" href="#{anchors[target]}" title="跳转到公式 ({label})">{html.escape(number.group(0))}</a>'
            parts=[];last=0
            for number in re.finditer(r'\(?[A-Z]?\.?\d+(?:\.\d+)*[a-z]?\)?',cue):
                parts.append(html.escape(cue[last:number.start()]));parts.append(replace_number(number));last=number.end()
            return ''.join(parts)+html.escape(cue[last:])
        parts=[];last=0
        for match in re.finditer(pattern,text):
            parts.append(html.escape(text[last:match.start()]));parts.append(replace_cue(match));last=match.end()
        return ''.join(parts)+html.escape(text[last:])

    body=[]
    body.append(f'<div class="title-block"><div class="kicker">{html.escape(cfg["category"])}</div><h1>{html.escape(cfg["zh_title"])}</h1><p class="en-title">{html.escape(data["title"])}</p><div class="links"><a href="../index.html">← 返回论文库</a><a href="{{{{PDF}}}}" target="_blank" rel="noopener">原始 PDF ↗</a></div></div>')
    chinese=cfg.get('source_language')=='zh'
    if chinese:
        notice='本资料原文为中文，保留原文及公式图表。'
    elif cfg.get('translation_engine')=='antigravity':
        notice='中文经 Gemini 3.8 Flash（Medium）对照英文逐段重译与润色，尚未经过逐段人工校对。缺损的行内公式已标明，请核对原版；图表及编号公式保留原貌。'
    else:
        notice='中文为 OPUS-MT 本机机器初译，尚未人工逐段校对。数学符号以同页原文及公式裁图为准；文中图表内文字和参考文献保留原貌。'
    body.append('<aside class="translation-notice">'+notice+' 可展开每段“核对原版排版”或每页原图进行核对。点击正文公式编号可跳转，公式下方可返回引用处。</aside>')
    if equations:
        index_links=' '.join(f'<a class="eq-ref" href="#{anchor}">({html.escape(key[1])}) · {key[0].split("-")[0]}</a>' for key,anchor in anchors.items())
        body.append(f'<details class="equation-index" id="equation-index"><summary>公式索引（{len(equations)} 个原始编号）</summary><div>{index_links}</div></details>')
    for page in data['pages']:
        number=page['number']
        body.append(f'<h2 data-num="{number}">第 {number} 页<span class="en-h">Page {number}</span><a class="pg" href="{{{{PDF}}}}#page={number}" target="_blank">PDF p.{number}</a></h2>')
        for b in page['blocks']:
            ident=b['id'];kind=b['kind'];en=b['en'];zh=b.get('zh','')
            if 'image' in b:
                block_anchors=''.join(f'<span class="eq-anchor" id="{anchors[(ident,label)]}"></span>' for label in b.get('labels',[]))
                label_text=' / '.join('('+x+')' for x in b.get('labels',[]))
                desc={'formula':'公式','table':'表格','picture':'插图','code':'代码'}.get(kind,'原文图像')
                body.append(f'<figure class="float imported-{kind}" id="{ident}">{block_anchors}<img loading="lazy" decoding="async" src="{b["image"]}" alt="{desc} {label_text} · 第 {number} 页"><figcaption>{desc} {html.escape(label_text)} · PDF p.{number}</figcaption>__BACKLINKS_{ident}__</figure>')
            else:
                en_html=linked(en,ident,'en');zh_html=linked(zh,ident,'zh')
                supplemental=[]
                for target_anchor,label in dict.fromkeys(re.findall(r'href="#([^"]+)" title="跳转到公式 \(([^)]*)\)"',en_html)):
                    if '#'+target_anchor in zh_html: continue
                    target_key=next(key for key,value in anchors.items() if value==target_anchor)
                    ref=f'ref-{ident}-zh-source-{label}'
                    backlinks[target_key].append(ref)
                    supplemental.append(f'<a class="eq-ref" id="{ref}" href="#{target_anchor}">({label})</a>')
                if supplemental:zh_html+='<span class="source-equation-refs"> 原文公式引用：'+'、'.join(supplemental)+'</span>'
                cls='pair imported-heading' if kind in ('title','section-header') else 'pair'
                if b.get('reference'): cls+=' bibliography-pair'
                body.append(f'<div class="{cls}" id="{ident}"><div class="en" lang="en"><p>{en_html}</p><details class="source-check"><summary>核对原版排版</summary><img loading="lazy" src="{b["source_image"]}" alt="第 {number} 页对应原文段落"></details></div><div class="zh" lang="zh-CN"><p>{zh_html}</p></div></div>')
        body.append(f'<details class="source-page"><summary>展开第 {number} 页原版整页（含全部图表、公式与页眉页脚）</summary><a href="{{{{PDF}}}}#page={number}" target="_blank"><img loading="lazy" decoding="async" src="figs/page-{number:03d}.jpg" alt="原始 PDF 第 {number} 页"></a></details>')
    result='\n'.join(body)
    for page in data['pages']:
        for b in page['blocks']:
            if 'image' not in b:continue
            links=['<a href="#equation-index" class="eq-backref">↩ 返回公式索引</a>'] if b.get('labels') else []
            for label in b.get('labels',[]):
                for n,ref in enumerate(backlinks.get((b['id'],label),[]),1):
                    links.append(f'<a href="#{ref}" class="eq-backref">↩ 返回 ({label}) 引用 {n}</a>')
            result=result.replace('__BACKLINKS_'+b['id']+'__','<div class="eq-backlinks">'+' '.join(links)+'</div>' if links else '')
    return result,{'equations':equations,'equation_references':sum(map(len,backlinks.values())),
                  'paragraphs':sum('image' not in b for p in data['pages'] for b in p['blocks'])}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--library',type=Path)
    ap.add_argument('--model',type=Path)
    ap.add_argument('--only', nargs='+', help='Import only these paper IDs')
    ap.add_argument('--rebuild',action='store_true',help='Rebuild saved imports without extraction or model')
    args=ap.parse_args()
    if args.rebuild:
        for path in sorted((ROOT/'pipeline/configs').glob('*.json')):
            cfg=json.loads(path.read_text())
            if not cfg.get('imported'):continue
            content=ROOT/'content'/cfg['id'];data=json.loads((content/'document.json').read_text())
            result,stats=render(data,cfg);(content/'00_document.html').write_text(result)
            cfg['validation']=stats;path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
            from build import build
            build(str(path))
        return
    if not args.library or not args.model:ap.error('--library and --model are required for import')
    seen={};entries=[]
    for pdf in sorted(args.library.rglob('*.pdf')):
        digest=hashlib.sha256(pdf.read_bytes()).hexdigest()
        if digest in seen:seen[digest]['aliases'].append(str(pdf.relative_to(args.library)));continue
        meta=PAPERS.get(pdf.stem.lower())
        if not meta:raise ValueError('Unknown PDF: '+str(pdf))
        ident,brand,zh_title,category=meta
        entry={'id':ident,'pdf_path':pdf,'sha256':digest,'aliases':[str(pdf.relative_to(args.library))],
               'brand':brand,'zh_title':zh_title,'category':category}
        seen[digest]=entry;entries.append(entry)
    translator=OfflineTranslator(args.model)
    manifest=ROOT/'content/library-manifest.json'
    report=json.loads(manifest.read_text()) if manifest.exists() else []
    for entry in entries:
        if args.only and entry['id'] not in args.only: continue
        start=time.time();ident=entry['id']
        content=ROOT/'content'/ident;content.mkdir(exist_ok=True)
        output=ROOT/'site'/ident;(output/'figs').mkdir(parents=True,exist_ok=True)
        dest=ROOT/'sources'/(ident+'.pdf');shutil.copyfile(entry['pdf_path'],dest)
        data_file=content/'document.json'
        if data_file.exists():data=json.loads(data_file.read_text())
        else:data=extract(str(dest),ident,output)
        chinese=ident=='rl-pd-control'
        texts=[b['en'] for p in data['pages'] for b in p['blocks'] if 'image' not in b and not b.get('reference') and not b.get('zh')]
        print(f'TRANSLATE {ident}: {len(texts)} paragraphs, {sum(map(len,texts))} chars',flush=True)
        if texts:
            translated=iter(texts if chinese else translator.translate(texts))
            for p in data['pages']:
                for b in p['blocks']:
                    if 'image' in b:continue
                    if b.get('reference'):b['zh']=b['en']
                    elif not b.get('zh'):b['zh']=next(translated)
        data_file.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        cfg={k:v for k,v in entry.items() if k not in ('pdf_path','aliases')}
        cfg.update({'pdf':f'sources/{ident}.pdf','title':entry['zh_title']+' · 中英对照',
                    'brand_sub':data['title'],'out':f'site/{ident}','imported':True,
                    'source_language':'zh' if chinese else 'en','math':False,
                    'translation':'Original Chinese' if chinese else 'OPUS-MT en-zh 1.9, machine draft; unreviewed',
                    'source_aliases':entry['aliases']})
        body,stats=render(data,cfg);(content/'00_document.html').write_text(body)
        data_file.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        cfg['validation']=stats
        (ROOT/'pipeline/configs'/(ident+'.json')).write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
        from build import build
        build(str(ROOT/'pipeline/configs'/(ident+'.json')))
        report=[r for r in report if r['id']!=ident]
        report.append({'id':ident,'pages':data['page_count'],'sha256':entry['sha256'],**stats})
        (ROOT/'content/library-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(f'DONE {ident}: {stats}, {time.time()-start:.1f}s',flush=True)
    print('ALL DONE',len(report),'documents',sum(x['pages'] for x in report),'pages',flush=True)

if __name__=='__main__':main()
