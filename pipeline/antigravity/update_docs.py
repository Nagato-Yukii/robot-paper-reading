from pathlib import Path
import json
from run_batches import ROOT
stage=ROOT/'staging'
summary=json.loads((ROOT/'completion.json').read_text())
p=stage/'README.md';s=p.read_text()
start=s.index('**译文状态**：');end=s.index('\n\n- 每页',start)
s=s[:start]+f'''**译文状态**：这批 {summary['papers']} 篇英文论文的 {summary['paragraphs']:,} 段译文，已经通过本机 Antigravity CLI 使用 **Gemini 3.8 Flash（Medium）**（模型 ID `{summary['model']}`，`--effort medium`）逐段对照英文重译与润色。尚未经过逐段人工校对。每篇 `content/<id>/polish_provenance.json` 保存批次、会话、token 使用和调用记录的校验摘要；完整结果按段落 ID 校验后才应用。数学公式与图表继续使用原 PDF 裁图；无法确定的行内数学缺损明确标记为“行内公式见原版”，请对照原图或 PDF 核对。参考文献及原中文资料保留原貌。'''+s[end:]
s=s.replace('重新从 PDF 提取/翻译时，需安装可选依赖并准备官方 Argos 模型包：','如需重新生成最初的离线草稿（会覆盖当前润色结果），可使用原导入工具；通常只需前述重新构建命令。以下依赖和模型仅用于离线草稿导入：')
s=s.replace('离线翻译模型来源：Argos Translate `translate-en_zh-1_9`；底层为 Jörg Tiedemann 与 Santhosh Thottingal 的 OPUS-MT，模型原始许可证 CC BY 4.0。模型与运行环境不属于本仓库发布内容。','''Argos / OPUS-MT 仅用于最初的离线草稿生成。当前英文译文已由上述 Gemini 模型对照英文重新润色；重新运行离线翻译会覆盖润色结果，操作前请保留备份。原离线模型来自 Jörg Tiedemann 与 Santhosh Thottingal 的 OPUS-MT（CC BY 4.0）；模型文件不随仓库发布。

### 使用指定 Gemini 模型继续润色

需要本机已登录的 `agy` CLI 且能调用 `gemini-3.8-flash-medium`。批量调用固定该模型及 medium，不做模型回退。运行目录、结果和原始备份均放在被忽略的 `_work/` 中。页面上的模型标记只在整批成功校验并应用后更新。

```bash
# 为新一轮润色选择一个全新的目录；已有目录直接续跑，不重复 prepare。
python3 pipeline/antigravity/prepare_jobs.py --repo . --run-dir _work/gemini-next
export RPR_GEMINI_RUN_DIR="$PWD/_work/gemini-next"
python3 pipeline/antigravity/run_batches.py --limit 10000 --workers 8
python3 pipeline/antigravity/apply_results.py
python3 pipeline/antigravity/update_docs.py
python3 pipeline/antigravity/commit_results.py
```

`apply_results.py` 仅生成已校验的暂存内容；`commit_results.py` 验证全文覆盖和源文件哈希后应用，备份原文档及译文，并运行资源/公式引用检查。任一批次不完整或未成功返回时，整批应用会被拒绝。''')
p.write_text(s)
p=stage/'NOTICE.md';s=p.read_text().replace('Imported library (23 English papers with unreviewed machine translation\nand one original Chinese article):','Imported library (23 English papers polished with Gemini 3.8 Flash Medium\nand one original Chinese article):')
start=s.index('Translation status:')
s=s[:start]+'''Translation status: RAX and BCG are curated reading pages. The imported
English library has been polished paragraph by paragraph against the source
English through the local Antigravity CLI using gemini-3.8-flash-medium with
medium effort. It has not been reviewed paragraph by paragraph by a human.
Per-paper polish_provenance.json records model requests, successful batch
sessions, output checksums, and token usage. Original formulas, diagrams,
and source crops remain available for verification. Where wording differs,
consult the original paper. The Chinese source article is unchanged.
'''
p.write_text(s)
print('Prepared current-model documentation')
