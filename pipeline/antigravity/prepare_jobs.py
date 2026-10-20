#!/usr/bin/env python3
"""Prepare isolated polish jobs; changing the source requires a new run directory."""
import argparse
import hashlib
import json
from pathlib import Path


def prepare(repo,run):
    manifest=[];(run/'jobs').mkdir(parents=True,exist_ok=True)
    for path in sorted((repo/'pipeline/configs').glob('*.json')):
        cfg=json.loads(path.read_text())
        if not cfg.get('imported') or cfg.get('source_language')!='en':continue
        source=repo/'content'/cfg['id']/'document.json';data=json.loads(source.read_text())
        rows=[{'id':b['id'],'page':pg['number'],'kind':b['kind'],'en':b['en'],'draft_zh':b['zh']}
              for pg in data['pages'] for b in pg['blocks'] if 'image' not in b and not b.get('reference')]
        chunks=[];chunk=[];size=0
        for row in rows:
            count=len(json.dumps(row,ensure_ascii=False))
            if chunk and (size+count>22000 or len(chunk)>=40):chunks.append(chunk);chunk=[];size=0
            chunk.append(row);size+=count
        if chunk:chunks.append(chunk)
        digest=hashlib.sha256(source.read_bytes()).hexdigest()
        for n,items in enumerate(chunks,1):
            job={'job_id':f'{cfg["id"]}-{n:03d}','paper_id':cfg['id'],'paper_title':data['title'],
                 'source_sha256':digest,'source_file':str(source),'items':items}
            (run/'jobs'/(job['job_id']+'.json')).write_text(json.dumps(job,ensure_ascii=False,indent=2)+'\n')
            manifest.append({k:v for k,v in job.items() if k!='items'}|{'paragraphs':len(items)})
    (run/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    schema={'type':'object','properties':{'translations':{'type':'array','items':{'type':'object','properties':{'id':{'type':'string'},'zh':{'type':'string'}},'required':['id','zh'],'additionalProperties':False}}},'required':['translations'],'additionalProperties':False}
    (run/'schema.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n')
    print('Prepared',len(manifest),'batches;',sum(x['paragraphs'] for x in manifest),'paragraphs')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--run-dir',type=Path,required=True);args=ap.parse_args()
    if (args.run_dir/'manifest.json').exists():raise SystemExit('Run already exists; resume it or choose a fresh --run-dir')
    prepare(args.repo.resolve(),args.run_dir.resolve())
