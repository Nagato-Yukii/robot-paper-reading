#!/usr/bin/env python3
"""Apply only a complete, validated Antigravity run; preserve recoverable originals."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime,timezone
from run_batches import ROOT as RUN,MODEL,validate

REPO=Path(__file__).resolve().parents[2]
STAGE=RUN/'staging'

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod);return mod


def main():
    manifest=json.loads((RUN/'manifest.json').read_text());papers={};usage={}
    for item in manifest:
        jid=item['job_id'];p=RUN/'results'/(jid+'.json')
        if not p.exists():raise SystemExit('Missing validated result: '+jid)
        result=json.loads(p.read_text());job=json.loads((RUN/'jobs'/(jid+'.json')).read_text())
        if result['requested_model']!=MODEL or result['effort']!='medium':raise SystemExit('Model mismatch: '+jid)
        receipt=next((p for p in (RUN/'receipts').glob(jid+'-attempt-*.json') if hashlib.sha256(p.read_bytes()).hexdigest()==result['receipt_sha256']),None)
        if receipt is None:raise SystemExit('Missing original CLI receipt: '+jid)
        envelope=json.loads(receipt.read_text());rows=validate(job,envelope)
        if rows!=result['translations'] or envelope.get('conversation_id')!=result['conversation_id'] or envelope.get('usage')!=result['usage']:raise SystemExit('CLI receipt/result mismatch: '+jid)
        source=Path(job['source_file'])
        if hashlib.sha256(source.read_bytes()).hexdigest()!=job['source_sha256']:raise SystemExit('Source changed: '+str(source))
        record=papers.setdefault(job['paper_id'],{'translations':{},'batches':[]})
        for row in rows:
            if row['id'] in record['translations']:raise SystemExit('Duplicate paragraph: '+jid+'/'+row['id'])
            record['translations'][row['id']]=row['zh']
        record['batches'].append({k:result[k] for k in ('job_id','conversation_id','receipt_sha256','usage','elapsed_seconds')})
        for k,v in result['usage'].items():
            if isinstance(v,(float,int)):usage[k]=usage.get(k,0)+v
    for name in ('pipeline','content'):
        shutil.copytree(REPO/name,STAGE/name,dirs_exist_ok=True)
    for name in ('README.md','NOTICE.md'):
        shutil.copyfile(REPO/name,STAGE/name)
    (STAGE/'site').mkdir(exist_ok=True);shutil.copyfile(REPO/'site/index.html',STAGE/'site/index.html')
    importer_path=STAGE/'pipeline/import_library.py'
    source=importer_path.read_text()
    old="notice='本资料原文为中文，保留原文及公式图表。' if chinese else '中文为 OPUS-MT 本机机器初译，尚未人工逐段校对。数学符号以同页原文及公式裁图为准；文中图表内文字和参考文献保留原貌。'"
    new="""if chinese:
        notice='本资料原文为中文，保留原文及公式图表。'
    elif cfg.get('translation_engine')=='antigravity':
        notice='中文经 Gemini 3.8 Flash（Medium）对照英文逐段重译与润色，尚未经过逐段人工校对。缺损的行内公式已标明，请核对原版；图表及编号公式保留原貌。'
    else:
        notice='中文为 OPUS-MT 本机机器初译，尚未人工逐段校对。数学符号以同页原文及公式裁图为准；文中图表内文字和参考文献保留原貌。'"""
    if old not in source and "cfg.get('translation_engine')=='antigravity'" not in source:raise SystemExit('Unexpected importer version; review notice patch')
    importer_path.write_text(source.replace(old,new))
    index_path=STAGE/'pipeline/build_index.py';source=index_path.read_text()
    source=source.replace("lang='中文原文' if cfg['source_language']=='zh' else '全文机器初译 · 待校对'", "lang='中文原文' if cfg['source_language']=='zh' else ('Gemini 3.8 Flash · Medium 润色 · 待人工校对' if cfg.get('translation_engine')=='antigravity' else '全文机器初译 · 待校对')")
    index_path.write_text(source)
    sys.path.insert(0,str(STAGE/'pipeline'))
    importer=load_module('gemini_importer',importer_path)
    builder=load_module('gemini_builder',STAGE/'pipeline/build.py')
    timestamp=datetime.now(timezone.utc).isoformat()
    for ident,record in papers.items():
        data_path=STAGE/'content'/ident/'document.json';data=json.loads(data_path.read_text())
        expected={b['id'] for pg in data['pages'] for b in pg['blocks'] if 'image' not in b and not b.get('reference')}
        if set(record['translations'])!=expected:raise SystemExit('Full paper coverage mismatch: '+ident)
        for pg in data['pages']:
            for block in pg['blocks']:
                if block['id'] in expected:block['zh']=record['translations'][block['id']]
        override_path=data_path.parent/'translation_overrides.json'
        if override_path.exists():
            ids=json.loads(override_path.read_text())
            override_path.write_text(json.dumps({key:record['translations'][key] for key in ids},ensure_ascii=False,indent=2)+'\n')
        cfg_path=STAGE/'pipeline/configs'/(ident+'.json');cfg=json.loads(cfg_path.read_text())
        cfg.update({'translation_engine':'antigravity','translation_model':MODEL,'translation_effort':'medium',
                    'translation':'Gemini 3.8 Flash (Medium), polished against English via local Antigravity CLI',
                    'translation_review':'gemini-polished-awaiting-human-review','polished_paragraphs':len(expected),'polished_at':timestamp})
        body,stats=importer.render(data,cfg);cfg['validation']=stats
        data_path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        (data_path.parent/'00_document.html').write_text(body)
        cfg_path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
        provenance={'model':MODEL,'effort':'medium','via':'local Antigravity CLI','completed_at':timestamp,
                    'paragraphs':len(expected),'status':'all-batches-successfully-validated','human_reviewed':False,'batches':record['batches']}
        (data_path.parent/'polish_provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
        builder.build(str(cfg_path))
    indexed=[]
    for cfgpath in sorted((STAGE/'pipeline/configs').glob('*.json')):
        cfg=json.loads(cfgpath.read_text())
        if not cfg.get('imported'):continue
        data=json.loads((STAGE/'content'/cfg['id']/'document.json').read_text())
        indexed.append({'id':cfg['id'],'title':data['title'],'pages':data['page_count'],'sha256':cfg['sha256'],
                        'source_aliases':cfg['source_aliases'],'translation_review':cfg.get('translation_review'),**cfg['validation']})
    (STAGE/'content/library-manifest.json').write_text(json.dumps(indexed,ensure_ascii=False,indent=2)+'\n')
    subprocess.run([sys.executable,str(STAGE/'pipeline/build_index.py')],check=True)
    summary={'model':MODEL,'effort':'medium','papers':len(papers),'paragraphs':sum(len(r['translations']) for r in papers.values()),'batches':len(manifest),'usage':usage,'prepared_at':timestamp}
    (RUN/'completion.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print('Validated and rendered staging output. Live repository has not been changed.')

if __name__=='__main__':main()
