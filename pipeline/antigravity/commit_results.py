#!/usr/bin/env python3
"""Commit a fully validated staged run, without retaining old translation backups."""
from pathlib import Path
import copy
import hashlib
import json
import shutil
import subprocess
import tempfile
import sys
from datetime import datetime,timezone

from run_batches import ROOT as RUN
REPO=Path(__file__).resolve().parents[2]

def source_projection(data):
    value=copy.deepcopy(data)
    for page in value['pages']:
        for block in page['blocks']:block.pop('zh',None)
    return value

def main():
    stage=RUN/'staging';completion=json.loads((RUN/'completion.json').read_text())
    jobs=json.loads((RUN/'manifest.json').read_text());papers=sorted({j['paper_id'] for j in jobs})
    if completion['papers']!=len(papers) or completion['batches']!=len(jobs):raise SystemExit('Incomplete run')
    paths=[Path('pipeline/import_library.py'),Path('pipeline/build_index.py'),Path('README.md'),Path('NOTICE.md')]
    changed=0;processed=0
    for ident in papers:
        original=REPO/'content'/ident/'document.json';updated=stage/'content'/ident/'document.json'
        expected=next(j['source_sha256'] for j in jobs if j['paper_id']==ident)
        if hashlib.sha256(original.read_bytes()).hexdigest()!=expected:raise SystemExit('Source changed: '+ident)
        before=json.loads(original.read_text());after=json.loads(updated.read_text())
        if source_projection(before)!=source_projection(after):raise SystemExit('Non-translation content changed: '+ident)
        old={b['id']:b.get('zh') for p in before['pages'] for b in p['blocks']}
        for page in after['pages']:
            for block in page['blocks']:
                if 'image' not in block and not block.get('reference'):
                    processed+=1;changed+=block.get('zh')!=old.get(block['id'])
        for name in ('document.json','00_document.html','polish_provenance.json','translation_overrides.json'):
            relative=Path('content')/ident/name
            if (stage/relative).exists():paths.append(relative)
        paths.extend([Path('pipeline/configs')/(ident+'.json'),Path('site')/ident/'index.html'])
    for p in (stage/'pipeline/antigravity').glob('*.py'):paths.append(p.relative_to(stage))
    completion.update({'processed_paragraphs':processed,'changed_paragraphs':changed,'source_content_preserved':True,
                       'formulas_images_and_numbers_preserved':True})
    (stage/'content/polish-manifest.json').write_text(json.dumps(completion,ensure_ascii=False,indent=2)+'\n')
    paths.extend([Path('content/library-manifest.json'),Path('content/polish-manifest.json'),Path('site/index.html')])
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=Path(tempfile.mkdtemp(prefix='rpr-rollback-'))
    existing=[]
    for relative in paths:
        dst=REPO/relative
        if dst.exists():
            (backup/relative).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dst,backup/relative);existing.append(str(relative))
    (backup/'backup-manifest.json').write_text(json.dumps({'existing':existing,'new':[str(p) for p in paths if str(p) not in existing]},indent=2)+'\n')
    installed=[]
    try:
        for relative in paths:
            dst=REPO/relative;dst.parent.mkdir(parents=True,exist_ok=True)
            temp=dst.with_name(dst.name+'.gemini-tmp');shutil.copyfile(stage/relative,temp);temp.replace(dst);installed.append(relative)
        subprocess.run([sys.executable,str(REPO/'pipeline/verify_library.py'),'--expected-imports','24'],check=True,cwd=REPO)
    except BaseException:
        for relative in reversed(installed):
            dst=REPO/relative
            if (backup/relative).exists():shutil.copy2(backup/relative,dst)
            elif dst.exists():dst.unlink()
        raise
    shutil.rmtree(backup)
    durable=REPO/'_work/gemini-polish';durable.mkdir(exist_ok=True)
    for name in ('jobs','results','receipts'):
        shutil.copytree(RUN/name,durable/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('*.stderr.txt','*.validation.txt'))
    for name in ('manifest.json','schema.json','completion.json','progress.json'):
        if (RUN/name).exists():shutil.copy2(RUN/name,durable/name)
    print('APPLIED',json.dumps(completion,ensure_ascii=False))
    print('No old translation backup retained.')

if __name__=='__main__':main()
