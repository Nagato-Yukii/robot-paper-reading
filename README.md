# 机器人论文双语精读 · Robotics Paper Reading

把机器人领域的论文（**软件算法** + **硬件系统**）做成 **逐段中英对照** 的可浏览页面：左英文原文、右中文译文，插图与表格从原 PDF 高清裁出，精编页公式用 KaTeX 本地渲染，批量导入页保留原版公式裁图。支持「对照 / 仅中文 / 仅英文」切换、字号调整、点击放大图片，以及一键打印成双语 PDF。

---

## 预览

| RAX（77 页） | BCG（8 页） |
|---|---|
| <img src="site/rax/preview.png" width="480" alt="RAX bilingual reader"> | <img src="site/bcg/preview.png" width="480" alt="BCG bilingual reader"> |

左列英文原文、右列中文译文；页首可切换「对照 / 仅中文 / 仅英文」，点击图片可放大，左侧目录随滚动高亮。

## 已收录

| 论文 | 方向 | 规模 | 位置 |
|---|---|---|---|
| **Scaling Online Exploration for Robot Agents**（RAX） | 软件 · 智能体 / 机器人学习 · VLA · 操作 | 77 页 · 34 图 · 21 表 · 261 段对照 | [`site/rax/`](site/rax/) |
| **Bundled Contact Gradients: Stabilizing Differentiable Simulation for Deployable Dynamic Tasks**（BCG） | 硬件 · 可微分仿真 · 接触 · 足式/人形 | 8 页 · 5 图 · 2 表 · 1 算法 · 公式 (1)–(5) | [`site/bcg/`](site/bcg/) |
| **Active Inference: A Process Theory** | 主动推断 · 贝叶斯神经科学 · Neural Computation 2017 | 49 页论文及附录 + 7 页被引列表 · 179 段 Gemini 译文 | [`site/active-inference-process-theory/`](site/active-inference-process-theory/) |
| **ControlVAE: Model-Based Learning of Generative Controllers for Physics-Based Characters** | 世界模型 · 生成式动作控制 · SIGGRAPH Asia 2022 | 16 页 · 192 段 Astra High 译文 | [`site/controlvae/`](site/controlvae/) |
| **SuperTrack: Motion Tracking for Physically Simulated Characters using Supervised Learning** | 世界模型 · 监督式动作跟踪 · SIGGRAPH Asia 2021 | 13 页 · 130 段 Astra High 译文 | [`site/supertrack/`](site/supertrack/) |
| **Dream to Control: Learning Behaviors by Latent Imagination** | 世界模型 · 潜空间策略学习 · ICLR 2020 | 20 页 · 98 段 Astra High 译文 | [`site/dreamer/`](site/dreamer/) |
| **High-Dimensional Continuous Control Using Generalized Advantage Estimation**（GAE） | 强化学习 · 优势估计 · ICLR 2016 | 14 页 · 130 段 Astra High 译文 | [`site/gae/`](site/gae/) |
| **Proximal Policy Optimization Algorithms**（PPO） | 强化学习 · 策略优化 · arXiv | 12 页 · 85 段 Astra High 译文 | [`site/ppo/`](site/ppo/) |
| **SuperMimic: Scaling Humanoid Whole-Body Control with One Differentiable World Model** | 世界模型 · 人形全身控制 · CoRL 2026 Oral | 19 页 · 136 段 Gemini 译文 | [`site/supermimic/`](site/supermimic/) |
| **Blind Precise Assembly: Proprioceptive Sim-to-Real Peg-in-Hole for Diverse Parts** | 机器人装配 · 本体感知 | 21 页 · 105 段 Gemini 译文 | [`site/blind-precise-assembly/`](site/blind-precise-assembly/) |
| **Blind Dexterity: Whole-Body Humanoid Manipulation via Pure Proprioception** | 人形机器人 · 本体感知操作 | 9 页 · 116 段 Gemini 译文 | [`site/blind-dexterity/`](site/blind-dexterity/) |
| **Minimizing Energy Consumption Leads to the Emergence of Gaits in Legged Robots** | 足式运动 · 能效 | 10 页 · 86 段 Gemini 译文 | [`site/energy-gaits/`](site/energy-gaits/) |
| **Adaptive Energy Regularization for Autonomous Gait Transition and Energy-Efficient Quadruped Locomotion** | 足式运动 · 能效 | 7 页 · 111 段 Gemini 译文 | [`site/adaptive-energy/`](site/adaptive-energy/) |
| **The Duke Humanoid: Design and Control For Energy Efficient Bipedal Locomotion Using Passive Dynamics** | 人形机器人 · 被动动力学 | 8 页 · 91 段 Gemini 译文 | [`site/duke-humanoid/`](site/duke-humanoid/) |
| **ECO: Energy-Constrained Optimization with Reinforcement Learning for Humanoid Walking** | 约束强化学习 · 能效 | 16 页 · 165 段 Gemini 译文 | [`site/eco/`](site/eco/) |

**RAX** 让一个通用编程智能体通过在线探索自行编写机器人控制程序，跨五种本体（单臂 / 双臂 / 灵巧手 / 移动 / 人形）在仿真与真机上完成精密插入、铰接物体、可变形物体与长时序移动操作。
**BCG** 在刚性接触处对邻近扰动分支做局部随机平滑以稳定一阶策略梯度，把可微分仿真训练的人形动态动作零样本部署到真实 Unitree G1。

## 目录结构

```
.
├── sources/                 # 原始 PDF（仅作学习/评注用途）
├── pipeline/                # 可复用工具链
│   ├── build.py             # 配置驱动：content/<id> + template → site/<id>
│   ├── template.html        # 阅读器模板（CSS/JS，{{...}} 占位符）
│   ├── crop.py              # 按 JSON 框位从 PDF 裁图（图/表/算法框）
│   ├── extract_floats.py    # 单栏论文的图表自动检测
│   ├── vendor/katex/        # 本地 KaTeX（离线公式渲染，含 woff2 字体）
│   └── configs/{rax,bcg}.json
├── content/<id>/            # 分节译文源文件（HTML 片段，按文件名排序拼接）
├── site/                    # 成品站点（纯静态，可直接双击打开）
│   ├── index.html           # 入口页
│   ├── rax/{index.html, figs/}
│   └── bcg/{index.html, figs/, vendor/katex/}
└── README.md
```

## 下载与阅读

**方式一（最简单）**：在 GitHub 页面点 **Code → Download ZIP**，解压后双击 `site/index.html`。
全站是纯静态文件，图片与 KaTeX 都在本地，**无需联网、无需服务器**。

**方式二**：`git clone` 后同样双击 `site/index.html`；若想用本地服务器：

```bash
cd robot-paper-reading
python3 pipeline/serve.py
# 浏览器打开 http://127.0.0.1:8000/site/index.html
```

### 划词高亮

在主页或论文正文中拖选文字，即可标为淡黄色；右下角可撤销上一处。通过本机服务阅读时，高亮与评分共用 `_data/ratings.sqlite3`，刷新、重启服务或更换浏览器后均可读取。服务暂时不可用时，高亮暂存在当前访问地址的浏览器存储中，恢复后同步；直接以 file:// 打开时，仅保存在该浏览器。

### 我的评语

主页每张论文卡片都有空白的“我的评语”输入框，由你填写。停止输入片刻或离开输入框后自动保存到本机数据库 `_data/ratings.sqlite3`；刷新、重启服务或更换本机浏览器后仍可读取和编辑。保存失败时保留浏览器草稿，并提供重试。

### 数据库评分

需要评分时，使用上面的本机服务打开主页；每项可直接点击 1–5 颗星，再次点击当前分数可清空。页面从数据库读取评分，保存成功后显示“已保存到数据库”。首次打开会将同一访问地址下原有的浏览器评分补入数据库，不覆盖已经保存的评分。

评分持久保存在 `_data/ratings.sqlite3`，重启服务、刷新或更换本机浏览器后仍会读取同一数据库。此目录已被 Git 忽略，不会随 PR 上传。保留该数据库文件即可保留评分；更换电脑时需要自行迁移该文件。本服务仅监听本机地址，不提供跨设备同步。直接双击静态页面仍可阅读，但无法连接数据库评分。

> 原始 PDF 与高清裁图构成主要体积，`sources/` 中的 PDF 供页面内「跳转到原文页码」使用。只想看译文的话，下载后删掉 `sources/` 也不影响阅读，只是页码链接会失效。

## 重新构建

```bash
python3 pipeline/build.py pipeline/configs/rax.json
python3 pipeline/build.py pipeline/configs/bcg.json
```

产物写入 `site/<id>/`。每个 `site/<id>/` 目录自带 `figs/` 与 `vendor/katex/`，可单独拷走。

## 新增一篇论文

1. **放 PDF**：`sources/<name>.pdf`。
2. **写配置** `pipeline/configs/<id>.json`：

   ```json
   {
     "id": "xxx",
     "pdf": "sources/xxx.pdf",
     "title": "中文标题 · 中英对照",
     "brand": "XXX 双语精读",
     "brand_sub": "English Title",
     "accent": "#0f766e",
     "accent_soft": "#e6f4f1",
     "math": true
   }
   ```
   `math: true` 会把 KaTeX 复制进产物目录并启用 `\(...\)` / `\[...\]`。

3. **取文本 / 裁图**：

   ```bash
   pdftotext -f 1 -l N sources/xxx.pdf -        # 逐页文本（双栏按阅读顺序）
   pdftotext -bbox sources/xxx.pdf bbox.html    # 需要坐标时
   python3 pipeline/crop.py --pdf sources/xxx.pdf \
       --spec floats.json --out site/xxx/figs --dpi 200
   ```
   `floats.json` 里每项为 `{"name","page","x0","y0","x1","y1"}`（单位 pt，原点在页面左上角）。

4. **写译文** `content/xxx/00_front.html`、`01_intro.html`…… 每段一对：

   ```html
   <h2 data-num="1">1&nbsp;&nbsp;中文标题<span class="en-h">English Title</span>
       <a class="pg" href="{{PDF}}#page=5" target="_blank">p.5</a></h2>

   <div class="pair">
     <p class="en">English paragraph…</p>
     <p class="zh">中文段落…</p>
   </div>
   ```
   - 显示公式：`<div class="eq">\[ ... \tag{1} \]</div>`
   - 单栏图限宽：`<figure class="float narrow">`；通栏图用 `figure.float`
   - `{{PDF}}` 由构建脚本替换为指向 `sources/` 的相对路径

5. **构建**：`python3 pipeline/build.py pipeline/configs/xxx.json`。

### 约定

- **切分粒度**：一个原文自然段 = 一个 `.pair`；跨页断开的段落合并；题注、表注与正文一样成对翻译。
- **专名**：方法名（RAX、BCG、SHAC、ADD…）、代码标识符与变量名保留英文；术语首现用「中文（English）」。
- **参考文献**：保留英文原貌，双栏排版，便于按原文检索。
- **代码清单 / 算法框**：保留英文与原始缩进，仅翻译说明文字。


## 本地论文库导入

已从 `paperlearning` 导入 24 份去重 PDF，另加入 Blind Precise Assembly、Blind Dexterity 和 SuperMimic，另加入 GAE 和 PPO，再加入 ControlVAE、SuperTrack 和 Dreamer，另加入 Active Inference: A Process Theory，合计 **37 份导入 PDF，共 591 页**：36 篇英文论文和 1 篇中文资料；原有 RAX、BCG 精编页继续保留。首页不再展示“计划中”。完整清单与原始文件哈希见 `content/library-manifest.json`，同一 PDF 在原目录的重复位置保存在各篇配置的 `source_aliases` 中。

**译文状态**：原先导入的 23 篇英文论文的 3,349 段译文，已经通过本机 Antigravity CLI 使用 **Gemini 3.8 Flash（Medium）**（模型 ID `gemini-3.8-flash-medium`，`--effort medium`）逐段对照英文重译与润色。尚未经过逐段人工校对。每篇 `content/<id>/polish_provenance.json` 保存批次、会话、token 使用和调用记录的校验摘要；完整结果按段落 ID 校验后才应用。数学公式与图表继续使用原 PDF 裁图；无法确定的行内数学缺损明确标记为“行内公式见原版”，请对照原图或 PDF 核对。参考文献及原中文资料保留原貌。

- 每页按阅读顺序组织为中英对照，原始 PDF、段落裁图和整页图均可离线查看。
- 显示公式、插图、表格按原始 PDF 裁出，公式不重新生成编号。
- 页面提供原始编号公式索引；正文中的明确公式引用可点击跳转，公式下方可返回引用处。
- 对重复编号，目标包含页面标识，并按引用位置选择相邻的公式；子公式编号也保留。
- `content/<id>/document.json` 保存文本、译文、页码、原始框位和公式标签；HTML 片段及 `site/<id>/` 为可重建产物。

只重新构建现有内容（Python 标准库即可，无需翻译模型或 API Key）：

```bash
python3 pipeline/import_library.py --rebuild
python3 pipeline/build.py pipeline/configs/rax.json
python3 pipeline/build.py pipeline/configs/bcg.json
python3 pipeline/build_index.py
python3 pipeline/verify_library.py
```

如需重新生成最初的离线草稿（会覆盖当前润色结果），可使用原导入工具；通常只需前述重新构建命令。以下依赖和模型仅用于离线草稿导入：

```bash
python3 -m venv _work/import-env
_work/import-env/bin/pip install -r pipeline/requirements-import.txt
# 下载 https://argos-net.com/v1/translate-en_zh-1_9.argosmodel
# 将 ZIP 格式模型包解压到 _work/models/，不要提交模型或虚拟环境。
_work/import-env/bin/python pipeline/import_library.py \
  --library /path/to/paperlearning \
  --model _work/models/translate-en_zh-1_9
_work/import-env/bin/python pipeline/refine_library.py \
  --model _work/models/translate-en_zh-1_9
python3 pipeline/build_index.py
python3 pipeline/verify_library.py
```

批量工具也支持 `--only <id> ...` 分批运行；中间翻译缓存保存在被忽略的 `_work/`。新增其他论文前，需在 `pipeline/import_library.py` 的 `PAPERS` 中补充文件名、ID、中文标题和分类。

Argos / OPUS-MT 仅用于最初的离线草稿生成。当前英文译文已由上述 Gemini 模型对照英文重新润色；重新运行离线翻译会覆盖润色结果，操作前请保留备份。原离线模型来自 Jörg Tiedemann 与 Santhosh Thottingal 的 OPUS-MT（CC BY 4.0）；模型文件不随仓库发布。

### 使用指定 Gemini 模型继续润色

新增 Blind Precise Assembly（21 页）的正文、图注及附录共 105 个文本块由相同 Gemini Medium 模型直接翻译；调用与覆盖校验记录见 `content/blind-precise-assembly/polish_provenance.json`，没有使用离线初译。参考文献保留原文。

新增 Blind Dexterity（9 页）的 116 个文本块经相同 Gemini Medium 模型逐段处理，包含正文、图注和参考文献；保留原版图表及编号公式，调用与校验记录见 `content/blind-dexterity/polish_provenance.json`。

新增四篇能效与步态论文（共 41 页、453 个文本块），由 Gemini 3.8 Flash Medium 直接翻译；16 词角色提示与 14 词任务指令见各论文 `polish_provenance.json`。Energy & Gaits 采用 PMLR 164:928–937 (2022) 正式版，其余三篇采用配置中固定的 arXiv 版本。原文及其衍生译文遵循 CC BY 4.0，参见 `NOTICE.md`。

需要本机已登录的 `agy` CLI 且能调用 `gemini-3.8-flash-medium`。批量调用固定该模型及 medium，不做模型回退。运行目录和调用结果放在被忽略的 `_work/` 中，不保留旧译文备份。页面上的模型标记只在整批成功校验并应用后更新。

```bash
# 为新一轮润色选择一个全新的目录；已有目录直接续跑，不重复 prepare。
python3 pipeline/antigravity/prepare_jobs.py --repo . --run-dir _work/gemini-next
export RPR_GEMINI_RUN_DIR="$PWD/_work/gemini-next"
python3 pipeline/antigravity/run_batches.py --limit 10000 --workers 8
python3 pipeline/antigravity/apply_results.py
python3 pipeline/antigravity/update_docs.py
python3 pipeline/antigravity/commit_results.py
```

`apply_results.py` 仅生成已校验的暂存内容；`commit_results.py` 验证全文覆盖和源文件哈希后应用，并运行资源/公式引用检查；校验成功后不保留旧译文备份。任一批次不完整或未成功返回时，整批应用会被拒绝。

## English

A bilingual (English ↔ Chinese) reading site for robotics papers — covering both the **software** side (learning, control, agentic robot programming) and the **hardware** side (differentiable simulation, contact modelling, sim-to-real on humanoids).

Each paper becomes a single static page: original English paragraph on the left, Chinese translation on the right, figures and tables cropped at 200 dpi from the original PDF, inline mathematics rendered locally with KaTeX and numbered equations preserved as complete PDF crops. Toggle between parallel / Chinese-only / English-only, zoom into any figure, or print straight to a bilingual PDF.

## Copyright

- Code, templates and the Chinese translations: **MIT** (see `LICENSE`).
- Papers, figures and tables: © their original authors. They are included for study and commentary only, and will be removed promptly upon request (see `NOTICE.md`).

### 数学排版与裁图检查

行内变量、上下标和希腊字母使用本地 KaTeX。导入正文中的数学表达式依据作者 LaTeX（LSWM 使用出版社 MathML）恢复；编号公式保留原 PDF 图像和双向引用。

```bash
node pipeline/verify_math.cjs
python3 pipeline/verify_crops.py
python3 pipeline/verify_library.py --expected-imports 30
```

`verify_math.cjs` 实际解析数学表达式，并检查缺失公式占位符。`verify_crops.py` 检查裁图边界是否穿过 PDF 文字行，覆盖导入论文及 RAX、BCG。它不能替代对图片内部排版和数学含义的人工核对。

重新裁切某篇导入论文后重建页面：

```bash
python3 pipeline/repair_crops.py <paper-id>
python3 pipeline/import_library.py --rebuild
```

### GAE 与 PPO 译文

GAE（14 页）和 PPO（12 页）的正文、题注、脚注及附录共 215 段由 **GPT-6 Astra High**（`gpt-6-astra`，`model_reasoning_effort="high"`）翻译。GAE 对照作者 LaTeX 与原页恢复行内数学，PPO 对照原页图像恢复数学记号；参考文献、图表内文字与编号公式保留原文。每篇 `polish_provenance.json` 记录批次和调用摘要，完整调用记录保存在本机忽略目录 `_work/astra-gae-ppo/`。译文尚未逐段人工校对。

### ControlVAE、SuperTrack 与 Dreamer

三篇共 49 页、420 个文本块，使用 **GPT-6 Astra High**（`gpt-6-astra`，`model_reasoning_effort="high"`）逐段翻译。ControlVAE 与 Dreamer 同时对照作者 LaTeX 和原页，SuperTrack 对照作者公开 PDF 原页。Dreamer 收录完整附录；参考文献、图表内文字和编号公式保留原文。双栏阅读顺序、完整图组、原始公式编号及双向引用经过检查。各篇 `polish_provenance.json` 记录调用摘要，完整翻译输入和结果保存在本机忽略目录 `_work/astra-world-models/`。译文尚未逐段人工校对。

### Active Inference: A Process Theory

由用户提供的本地 `process_theory.pdf` 导入，用于个人学习。正式论文 49 页（含 A–F 附录），文件另附 7 页后续被引文献列表。正文与附录共 179 个文本块由 **Gemini 3.8 Flash Medium**（`gemini-3.8-flash-medium`，`--effort medium`）逐段翻译，对照原页恢复行内数学；图表及显示公式、参考文献与附加被引列表保留原貌。模型调用摘要见 `content/active-inference-process-theory/polish_provenance.json`；完整调用记录保存在本机忽略目录 `_work/gemini-active-inference/`。译文尚未逐段人工校对。
