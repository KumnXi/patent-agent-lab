<div align="center">

# 专利撰写 Agent

**让 AI 像专利工程师一样写交底书：自己查资料、自己写、自己改，直到通过全部校验。**

基于 [DeepSeek Harness (dsh)](https://github.com/deepseek-ai/deepseek-harness) 与
[patent-aid](https://github.com/KumnXi/patent-aid) 的垂类 Agent 实验项目 · MIT 协议

</div>

---

## 它能做什么

你说一句技术想法，agent 会：

1. **自己检索**你的专利库（多角度查 3-4 次）、查知识图谱、查规范术语
2. **自己写**出 1.2-1.9 万字的完整交底书（发明名称/摘要/权利要求书/技术领域/背景技术/发明内容/附图说明/具体实施方式）
3. **自己改**：回读全文查跨章一致性，跑三项自动校验（权利要求格式 / 专利合规 / 数据真实性），按缺陷清单逐条修复

实测效果（同一真实病例、同一把尺子——patent-aid 自带校验器）：

| 产物 | 字数 | 章节 | 质检分 | 合规问题 |
|---|---|---|---|---|
| patent-aid 固定流水线 | 12230 | 7/8 | 84.5（B） | 2 |
| **本 agent** | **13425** | **8/8** | **86.8（A）** | **0** |

> 和传统"点按钮跑流水线"的区别：agent 是对话式的——你说想法，它干活，你随时插嘴
> （"背景技术多引两篇""这个参数改成 X"），它接着改。每一步在 dsh 界面里可见、可回放。

---

## 三步上手（小白版）

### 第 0 步：准备环境（每台电脑只做一次）

| 需要 | 版本 | 从哪来 |
|---|---|---|
| Node.js | ≥ 22（LTS） | [nodejs.org](https://nodejs.org/) 一路下一步 |
| Python 环境 | 3.10+，装好 patent-aid 的依赖 | 见下方说明 |
| DeepSeek API Key | sk- 开头 | [platform.deepseek.com](https://platform.deepseek.com/) 注册后在 API Keys 页创建 |

Python 环境怎么准备（复制粘贴即可）：

```bash
# 安装 Miniconda 后，在 Anaconda Prompt 里：
conda create -n patent python=3.10 -y
conda activate patent
git clone https://github.com/KumnXi/patent-aid
cd patent-aid
pip install -r requirements.txt
```

记下这个环境的 python.exe 路径（形如 `C:/Users/你/miniconda3/envs/patent/python.exe`）。

### 第 1 步：下载本项目

```bash
git clone https://github.com/KumnXi/patent-agent-lab
cd patent-agent-lab
```

### 第 2 步：双击 `启动专利Agent.bat`

首次启动会自动弹出配置文件让你填三项（都有注释说明）：

```json
{
  "patent_project_path": "D:/code/patent-aid",       ← patent-aid 项目的本地路径
  "python": "C:/Users/你/miniconda3/envs/patent/python.exe",
  "deepseek_api_key": "sk-你的Key"
}
```

填好保存，重新双击。脚本会自动检查环境、自动装缺的依赖、启动服务并打开浏览器。

### 第 3 步：在浏览器里下指令

服务地址 http://127.0.0.1:3080 ，在对话框输入：

```
用 patent-writer 技能，帮我写一份交底书，技术想法是：一种基于深度学习的管道缺陷检测机器人
```

然后看它干活就行。成品在 `output/` 目录，过程可在 dsh 界面回放。

---

## 常见问题

**Q：双击后窗口一闪就没 / 报"未检测到 Node.js"？**
先装 Node.js LTS（第 0 步），或用命令行运行 `启动专利Agent.bat` 看完整报错。

**Q：提示"专利撰写助手项目路径不对"？**
配置里的 `patent_project_path` 要指向能在其中找到 `src/core/__init__.py` 的目录，
也就是 patent-aid 项目的根目录。路径分隔符用 `/` 或 `\\` 都行。

**Q：agent 说"工具不可用/未暴露 MCP 工具"？**
说明启动时没带 MCP 注册参数。**始终用 `启动专利Agent.bat` 启动**，它会自动带上
`--patch .cordis.local.yml`。手动启动请照抄：

```bash
DSH_PERMISSION_MODE=danger-full-access DEEPSEEK_API_KEY=sk-xxx \
npx -y @deepseek-ai/dsh --profile web --patch .cordis.local.yml
```

**Q：启动报 `EADDRINUSE: address already in use 127.0.0.1:3080`？**
上一次的 dsh 没关干净（占着端口），或别的程序占了 3080。先关掉旧的启动窗口
再试；顽固残留就在任务管理器结束 node.exe，或换端口启动：
`npx -y @deepseek-ai/dsh --profile web --port 3081 --patch .cordis.local.yml`

**Q：第一次生成时 agent 说"引擎预热中，请稍后重试"？**
正常现象。专利引擎首次初始化约 20-60 秒，agent 会自己重试，不用管。

**Q：为什么需要 `DSH_PERMISSION_MODE=danger-full-access`？**
dsh 默认沙箱只允许写本目录，而专利引擎初始化时要写 patent-aid 自己的日志与
图谱缓存。本项目是本地实验性质，启动脚本已统一注入该变量。

**Q：生成的交底书能导出 Word 吗？**
本项目先产出 Markdown。Word 导出（公式/附图）在 patent-aid 里已实现，
桥接一条工具命令即可接入，见 `mcp_server/patent_server.py` 的工具注册方式。

---

## 架构：为什么这样设计

```
dsh（agent 循环 / Web UI / 轨迹回放 / 模型接入）
 ├─ MCP（stdio 协议）
 │   mcp_server/patent_server.py（FastMCP，10 个工具）
 │    └─ import patent-aid 的检索、知识图谱与三个校验器（零修改复用）
 └─ .dsh/skills/patent-writer/SKILL.md（交底书格式 / 文风 / 流程 / 闸门规则）
```

| 文件 | 作用 |
|---|---|
| `启动专利Agent.bat` + `start_patent_agent.ps1` | 一键启动：自检环境、装依赖、注入配置、拉起服务 |
| `config/settings.example.json` | 配置模板（复制为 `settings.local.json` 后填写，**不入库**） |
| `.cordis.yml.template` | dsh 的 MCP 注册模板（启动脚本渲染为 `.cordis.local.yml`） |
| `mcp_server/patent_server.py` | MCP 服务器：检索/图谱/术语/草稿/三个校验器共 10 个工具 |
| `mcp_server/draft_state.py` | agent 写作草稿的工作区（章节持久化，中断可续） |
| `.dsh/skills/patent-writer/SKILL.md` | 撰写规范：流程约束 + 字数配额 + 文风硬规则 |
| `run_compare.py` / `verify_output.py` | 成品对比与独立验收（用 patent-aid 校验器做尺子） |
| `cases/` | 测试病例（来自真实使用记录） |
| `notes/dsh_setup.md` | dsh 装机记录与踩坑（导入死锁、stdout 代理、沙箱等） |

设计取舍：**领域逻辑全在 Python 和 SKILL.md 里，与 harness 解耦**——dsh 将来
破坏性升级时，迁移成本只剩换一个启动方式；MCP 桥对任何支持 MCP 的 harness 通用。

---

## 已知限制（诚实清单）

- 单病例深验证（case1），统计意义上的对比还需要更多病例（`cases/` 已备 case2）
- patent-aid 当前 gz 轻量库缺全文语料，知识图谱工具暂为空载，检索靠 RAG（3.2 万块）支撑
- 产出为 Markdown，Word 导出待桥接
- dsh 处于 v0.1 开发者预览期，官方声明后续有破坏性变更（本项目的 skill/MCP 层已解耦，影响可控）

## 致谢

- [DeepSeek Harness (dsh)](https://github.com/deepseek-ai/deepseek-harness) — DeepSeek 官方开源的 agent harness，"一切皆插件"
- [patent-aid](https://github.com/KumnXi/patent-aid) — 专利撰写流水线，本项目复用其检索与校验资产
- [MathModelAgent](https://github.com/jihe520/MathModelAgent) — 架构参考（workflow + 多层容错 + HIL）

## License

[MIT](LICENSE)
