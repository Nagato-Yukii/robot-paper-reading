#!/usr/bin/env python3
"""Normalize reading order, protect inline math/citations, and refine draft terms."""
import argparse
import json
import re
from pathlib import Path
from import_library import ROOT, OfflineTranslator, render, repair_numbered_equations
from build import build

MATH_CHARS=r'[\u0370-\u03ff\u1d00-\u1fff\u2100-\u22ff\ufffd\U0001d400-\U0001d7ff=|{}∈]'


def protect(text):
    values=[]
    def hold(value):
        token='MATH'+str(len(values));values.append(value);return token
    # Preserve citation author names, years, URLs, and numerical citations verbatim.
    text=re.sub(r'https?://\S+|\[[^\[\]]{1,500}\]',lambda m:hold(m.group(0)),text)
    words=list(re.finditer(r'[A-Za-z]{2,}[A-Za-z0-9]*',text))
    out=[];last=0
    for word in words:
        gap=text[last:word.start()]
        if re.search(MATH_CHARS,gap):
            left=len(gap)-len(gap.lstrip());right=len(gap.rstrip())
            if right>left:gap=gap[:left]+hold(gap[left:right])+gap[right:]
        out.extend([gap,word.group(0)]);last=word.end()
    gap=text[last:]
    if re.search(MATH_CHARS,gap):
        left=len(gap)-len(gap.lstrip());right=len(gap.rstrip())
        if right>left:gap=gap[:left]+hold(gap[left:right])+gap[right:]
    out.append(gap)
    return ''.join(out),values


def restore(text,values):
    missing=[]
    for n,value in enumerate(values):
        pattern=r'MATH\s*'+str(n)+r'(?!\d)'
        if re.search(pattern,text,re.I):text=re.sub(pattern,lambda m:value,text,flags=re.I)
        else:missing.append(value)
    # A failed copied token must remain visible instead of silently losing math.
    if missing:text+=' 【原文符号 / 引文：'+'；'.join(missing)+'】'
    return text


def terms(en,zh):
    always={
        '政策':'策略','奖励功能':'奖励函数','客观功能':'目标函数','国家过渡':'状态转移',
        '状态过渡':'状态转移','国家访问':'状态访问','歧视者':'判别器','机动技能':'运动技能',
        '低级策略':'低层策略','高级策略':'高层策略','低水平策略':'低层策略','高级别策略':'高层策略',
        '无结构':'非结构化','预训':'预训练','培训前阶段':'预训练阶段','培训前目标':'预训练目标',
        '自然主义':'自然','物理学人物动画':'基于物理的角色动画','物理学角色动画':'基于物理的角色动画',
        '对抗式仿真学习':'对抗模仿学习','对抗性仿真学习':'对抗模仿学习','运动仿真':'运动模仿',
        '模式碰撞':'模式坍缩','模式崩溃':'模式坍缩','不受监督':'无监督',
        '可重复使用':'可复用','可再利用':'可复用','奖励工程':'奖励设计','回报功能':'回报函数',
        '对抗性技能嵌入':'对抗技能嵌入','大规模平行':'大规模并行','培训':'训练',
        '联合位置':'关节位置','联合速度':'关节速度','联合扭矩':'关节力矩',
    }
    for a,b in always.items():zh=zh.replace(a,b)
    if re.search(r'\bagents?\b',en,re.I):
        for x in ['代理商','代理人','特工','特效人员','物剂','该剂','代理']:zh=zh.replace(x,'智能体')
    if re.search(r'\bcharacters?\b',en,re.I):zh=zh.replace('字符','角色').replace('人物','角色')
    if re.search(r'\bpriors?\b',en,re.I):zh=zh.replace('前奏','先验').replace('前身','先验')
    if re.search(r'\bheuristics?\b',en,re.I):zh=zh.replace('热力学','启发式规则')
    if 'adversarial' in en.lower():zh=zh.replace('横向学习','对抗学习').replace('反常模仿','对抗模仿')
    return zh

HEADINGS={
 'introduction':'引言','related work':'相关工作','related works':'相关工作','background':'背景',
 'reinforcement learning background':'强化学习背景','reinforcement learning':'强化学习',
 'overview':'概述','method':'方法','methods':'方法','methodology':'方法',
 'adversarial skill embeddings':'对抗技能嵌入','imitation objective':'模仿目标',
 'skill discovery objective':'技能发现目标','surrogate objective':'代理目标',
 'experiments':'实验','experimental results':'实验结果','results':'结果',
 'discussion':'讨论','conclusion':'结论','conclusions':'结论','limitations':'局限性',
 'limitations and future work':'局限性与未来工作','references':'参考文献',
 'acknowledgments':'致谢','acknowledgements':'致谢','hyperparameters':'超参数',
 'implementation details':'实现细节','training details':'训练细节','appendix':'附录',
 'motion tracking':'运动跟踪','motion imitation':'动作模仿','policy learning':'策略学习',
 'domain randomization':'域随机化','observations':'观测','actions':'动作','rewards':'奖励',
 'reward function':'奖励函数','reward functions':'奖励函数','ablation study':'消融实验',
 'ablation studies':'消融实验','training':'训练','abstract':'摘要',
 'task rewards':'任务奖励','sim-to-real transfer':'仿真到现实迁移',
 'network architecture':'网络架构','termination and reset':'终止与重置',
 'adaptive sampling':'自适应采样','joint impedance and actions':'关节阻抗与动作',
 'tracking objective':'跟踪目标','scaleable motion tracking':'可扩展的运动跟踪',
 'trajectory synthesis via guided diffusion':'通过引导扩散合成轨迹',
}


def order_blocks(blocks,width):
    wide=[b for b in blocks if b['bbox'][0]<width*.45 and b['bbox'][2]>width*.55]
    narrow=[b for b in blocks if b not in wide]
    def columns(items):
        left=[b for b in items if (b['bbox'][0]+b['bbox'][2])/2<width/2]
        right=[b for b in items if b not in left]
        return sorted(left,key=lambda b:b['bbox'][1])+sorted(right,key=lambda b:b['bbox'][1])
    out=[]
    for block in sorted(wide,key=lambda b:b['bbox'][1]):
        before=[b for b in narrow if (b['bbox'][1]+b['bbox'][3])/2<(block['bbox'][1]+block['bbox'][3])/2]
        out.extend(columns(before));narrow=[b for b in narrow if b not in before]
        out.append(block)
    return out+columns(narrow)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--model',type=Path,required=True);ap.add_argument('--only',nargs='+');args=ap.parse_args()
    translator=OfflineTranslator(args.model)
    translator.cache_file=ROOT/'_work/translation-cache-protected.json'
    translator.cache=json.loads(translator.cache_file.read_text()) if translator.cache_file.exists() else {}
    report=[]
    import pymupdf
    for path in sorted((ROOT/'pipeline/configs').glob('*.json')):
        cfg=json.loads(path.read_text())
        if not cfg.get('imported'):continue
        if args.only and cfg['id'] not in args.only:continue
        datafile=ROOT/'content'/cfg['id']/'document.json';data=json.loads(datafile.read_text())
        fixes={
          'rt1':('RT-1: Robotics Transformer for Real-World Control at Scale','RT-1：面向规模化真实机器人控制的 Robotics Transformer','RT-1'),
          'vla-transfer':('RT-2: Vision-Language-Action Models Transfer Web Knowledge to Robotic Control','RT-2：将网络知识迁移到机器人控制的视觉语言动作模型','RT-2'),
          'wham':('WHAM: World-grounded Humans with Accurate Motion','WHAM：世界坐标下的准确人体运动重建','WHAM'),
          'h-infinity':('Learning H-Infinity Locomotion Control','学习 H∞ 运动控制','H∞ Locomotion'),
          'dreamwaq':('DreamWaQ: Learning Robust Quadrupedal Locomotion With Implicit Terrain Imagination via Deep Reinforcement Learning','DreamWaQ：通过隐式地形想象与深度强化学习实现鲁棒四足运动','DreamWaQ'),
          'him':('Hybrid Internal Model: Learning Agile Legged Locomotion with Simulated Robot Response','HIM：通过仿真机器人响应学习敏捷足式运动的混合内部模型','HIM'),
          'robust-walking':('Robust Humanoid Walking on Compliant and Uneven Terrain with Deep Reinforcement Learning','通过深度强化学习在柔顺与不平坦地形上实现鲁棒人形行走','Robust Humanoid Walking'),
          'visualmimic':('VisualMimic: Visual Humanoid Loco-Manipulation via Motion Tracking and Generation','VisualMimic：通过运动跟踪与生成实现视觉人形移动操作','VisualMimic'),
        }
        if cfg['id'] in fixes:
            data['title'],cfg['zh_title'],cfg['brand']=fixes[cfg['id']]
            cfg['title']=cfg['zh_title']+' · 中英对照';cfg['brand_sub']=data['title']
        if cfg['id']=='him':cfg['category']='足式运动 · 内部模型'
        elif not data['title']:
            candidates=[b['en'] for b in data['pages'][0]['blocks'] if b['kind'] in ('title','section-header') and b['en'].lower() not in ('abstract','introduction')]
            data['title']=candidates[0] if candidates else cfg['brand']
            cfg['brand_sub']=data['title']
        pdf=pymupdf.open(ROOT/cfg['pdf'])
        repair_numbered_equations(data,pdf,ROOT/'site'/cfg['id'])
        in_refs=False;jobs=[];owners=[];protected=[]
        for n,page in enumerate(data['pages']):
            page['blocks']=order_blocks(page['blocks'],pdf[n].rect.width)
            for b in page['blocks']:
                if b['kind'] in ('section-header','title'):
                    in_refs=bool(re.search(r'\b(references|bibliography)\b',b['en'],re.I))
                b['reference']=in_refs
                if 'image' in b:continue
                if in_refs or cfg['source_language']=='zh':b['zh']=b['en'];continue
                if b['kind']=='title':b['zh']=cfg['zh_title'];continue
                stripped=re.sub(r'^\s*(?:(?:\d+(?:\.\d+)*|[IVX]+|[A-Z])\.?\s+)','',b['en']).strip().lower()
                if b['kind']=='section-header' and stripped in HEADINGS:
                    b['zh']=HEADINGS[stripped];continue
                masked,values=protect(b['en']);jobs.append(masked);owners.append(b);protected.append(values)
        print('REFINE',cfg['id'],len(jobs),'blocks',flush=True)
        for b,zh,values in zip(owners,translator.translate(jobs),protected):
            b['zh']=terms(b['en'],restore(zh,values))
        datafile.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        body,stats=render(data,cfg);(datafile.parent/'00_document.html').write_text(body)
        datafile.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        cfg['validation']=stats;path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
        build(str(path))
        report.append({'id':cfg['id'],'pages':data['page_count'],'sha256':cfg['sha256'],**stats})
        print('REFINED',cfg['id'],flush=True)
    (ROOT/'content/library-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
