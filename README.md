# 机器人论文双语精读 · Robotics Paper Reading

把机器人领域的论文（**软件算法** + **硬件系统**）做成 **逐段中英对照** 的可浏览页面：左英文原文、右中文译文，插图与表格从原 PDF 高清裁出，公式用 KaTeX 本地渲染。支持「对照 / 仅中文 / 仅英文」切换、字号调整、点击放大图片，以及一键打印成双语 PDF。

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
python3 -m http.server 8000
# 浏览器打开 http://localhost:8000/site/
```

> 仓库体积约 41 MB，主要来自 `sources/` 里的两份原始 PDF（供页面内「跳转到原文页码」使用）。只想看译文的话，下载后删掉 `sources/` 也不影响阅读，只是页码链接会失效。

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

## English

A bilingual (English ↔ Chinese) reading site for robotics papers — covering both the **software** side (learning, control, agentic robot programming) and the **hardware** side (differentiable simulation, contact modelling, sim-to-real on humanoids).

Each paper becomes a single static page: original English paragraph on the left, Chinese translation on the right, figures and tables cropped at 200 dpi from the original PDF, equations rendered locally with KaTeX. Toggle between parallel / Chinese-only / English-only, zoom into any figure, or print straight to a bilingual PDF.

## Copyright

- Code, templates and the Chinese translations: **MIT** (see `LICENSE`).
- Papers, figures and tables: © their original authors. They are included for study and commentary only, and will be removed promptly upon request (see `NOTICE.md`).
