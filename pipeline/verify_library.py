#!/usr/bin/env python3
"""Validate all local assets, fragment callbacks, and imported page coverage."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
from collections import Counter
import json
import argparse
import hashlib
ROOT=Path(__file__).resolve().parents[1]

class Document(HTMLParser):
    def __init__(self,path):
        super().__init__(convert_charrefs=True)
        self.ids=[];self.refs=[];self.path=path
        self.feed(path.read_text())
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key=='id':self.ids.append(value)
            elif key in ('src','href') and value:self.refs.append(value)

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--expected-imports",type=int);args=parser.parse_args()
    errors=[];refs=0;fragment_refs=0;equation_refs=0
    documents={p:Document(p) for p in (ROOT/'site').rglob('*.html')}
    for path,doc in documents.items():
        dup=[key for key,n in Counter(doc.ids).items() if n>1]
        if dup:errors.append(f'{path.relative_to(ROOT)} duplicate IDs: {dup}')
        for ref in doc.refs:
            url=urlsplit(ref)
            if url.scheme or url.netloc:continue
            target=(path.parent/unquote(url.path)).resolve() if url.path else path
            refs+=1
            if not target.exists():errors.append(f'{path.relative_to(ROOT)} missing: {ref}');continue
            if url.fragment and target.suffix=='.html':
                fragment_refs+=1
                parsed=documents.get(target)
                if parsed and unquote(url.fragment) not in parsed.ids:errors.append(f'{path.relative_to(ROOT)} broken fragment: {ref}')
            if ref.startswith('#eq-'):equation_refs+=1
    manifest=json.loads((ROOT/'content/library-manifest.json').read_text())
    if args.expected_imports is not None and len(manifest)!=args.expected_imports:errors.append(f'Expected {args.expected_imports} unique imports, got {len(manifest)}')
    for cfgpath in (ROOT/'pipeline/configs').glob('*.json'):
        cfg=json.loads(cfgpath.read_text())
        if not cfg.get('imported'):continue
        data=json.loads((ROOT/'content'/cfg['id']/'document.json').read_text())
        if not data['title']:errors.append(cfg['id']+' missing English title')
        if hashlib.sha256((ROOT/cfg['pdf']).read_bytes()).hexdigest()!=cfg['sha256']:errors.append(cfg['id']+' PDF checksum mismatch')
        if len(data['pages'])!=data['page_count']:errors.append(cfg['id']+' missing pages')
        for page in data['pages']:
            if not page['blocks']:errors.append(f'{cfg["id"]} p{page["number"]}: no extracted content')
            for b in page['blocks']:
                if 'image' not in b and not b.get('zh'):errors.append(f'{cfg["id"]}/{b["id"]} missing translation')
    print(json.dumps({'html_pages':len(documents),'imports':len(manifest),'pdf_pages':sum(x['pages'] for x in manifest),
                      'local_references':refs,'fragment_references':fragment_refs,'equation_references':equation_refs,
                      'numbered_equations':sum(len(x['equations']) for x in manifest),'errors':errors},ensure_ascii=False,indent=2))
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
