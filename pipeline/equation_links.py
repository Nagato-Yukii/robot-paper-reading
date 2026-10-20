"""Add stable anchors and backlinks to explicitly numbered KaTeX equations."""
import re


def link_numbered_math(body):
    labels={}
    def anchor(match):
        attrs,math=match.group(1),match.group(2)
        tag=re.search(r'\\tag\{([A-Z]?\.?\d+(?:\.\d+)*[a-z]?)\}',math)
        if not tag or re.search(r'\bid=',attrs):return match.group(0)
        label=tag.group(1);ident='eq-'+label.replace('.','-')
        labels[label]=[]
        return f'<div class="eq" id="{ident}"{attrs}>{math}__EQ_BACK_{label}__</div>'
    body=re.sub(r'<div class="eq"([^>]*)>(.*?)</div>',anchor,body,flags=re.S)
    if not labels:return body
    def paragraph(match):
        text=match.group(0)
        def ref(m):
            prefix,label=m.group(1),m.group(2)
            if label not in labels:return m.group(0)
            ident=f'ref-math-{label}-{len(labels[label])+1}'
            labels[label].append(ident)
            return f'{prefix}<a class="eq-ref" id="{ident}" href="#eq-{label.replace(".","-")}">({label})</a>'
        return re.sub(r'((?:\b[Ee]q(?:uation)?s?\.?|公式|方程|式)\s*)\(([A-Z]?\.?\d+(?:\.\d+)*[a-z]?)\)',ref,text)
    body=re.sub(r'<p\b[^>]*>.*?</p>',paragraph,body,flags=re.S)
    for label,refs in labels.items():
        links=' '.join(f'<a class="eq-backref" href="#{ref}">↩ 返回引用 {n}</a>' for n,ref in enumerate(refs,1))
        body=body.replace('__EQ_BACK_'+label+'__','<div class="eq-backlinks">'+links+'</div>' if links else '')
    return body
