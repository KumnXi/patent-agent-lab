# dsh 装机与配置记录

## 环境（2026-08-28 核实）

- Node.js v22.18.0 / npm 10.9.3 ✅
- conda env（Python 3.10+），`pip install "mcp<2"` ✅
  （mcp 2.x 把 FastMCP 改名为 MCPServer，本项目钉 v1 用 FastMCP）
- dsh 拉取方式：`npx -y @deepseek-ai/dsh web`（版本随 npx 缓存，建议钉版本）

## 启动

见 README。手动等价命令：

```bash
DSH_PERMISSION_MODE=danger-full-access DEEPSEEK_API_KEY=sk-xxx \
npx -y @deepseek-ai/dsh --profile web --patch .cordis.local.yml
```

## MCP 注册

- 模板：`.cordis.yml.template`（格式对照官方示例
  `apps/cli/config/examples/mcp-memory/mcp-reference-memory.cordis.yml`），
  启动脚本渲染为 `.cordis.local.yml` 后经 `--patch` 挂载
- 服务器：stdio，配置里的 python 运行 `mcp_server/patent_server.py`
- dsh 只启动进程，不装依赖；服务器启动即后台预热旧引擎（约 20s 增量模式）
- **web 与 headless 都要带 `--patch`，漏了 MCP 工具不暴露**

## 实测踩坑（重要）

1. **后台线程导入死锁**：预热线程里 `from src.core import ...` 加载 numpy
   C 扩展时，与主线程 anyio/FastMCP 在 app.run 时的懒加载形成导入锁
   死锁（faulthandler 抓到卡在 `numpy _core/overrides create_module`）。
   解法：重量级导入全部放主线程，预热线程只跑纯计算。
2. **redirect_stdout 与 FastMCP 冲突**：`contextlib.redirect_stdout` 是
   进程级的，重定向期间 FastMCP 读 `sys.stdout.buffer` 直接崩
   （StringIO 没有 buffer）。解法：线程感知 stdout 代理（主线程直通、
   worker 线程吞 print），见 patent_server.py 的 `_WorkerQuietStdout`。
3. **沙箱挡住旧项目写盘**：dsh 默认 `workspace-write` 沙箱只允许写 cwd；
   旧引擎初始化要写自己的 `logs/` 和知识图谱缓存 → 报错。
   解法：`DSH_PERMISSION_MODE=danger-full-access`（本地实验可接受）。
4. **mcp 2.x 改 API**：FastMCP 改名 MCPServer，本项目钉 `"mcp<2"`。
5. **Windows 编码**：stdio 默认 GBK，服务器启动时 `reconfigure(utf-8)` +
   overlay 里 `PYTHONUTF8=1` 双保险。
6. **PS5.1 Get-Content 编码坑**：`-Encoding UTF8` 在部分环境仍按 GBK 解码，
   启动脚本统一用 `[IO.File]::ReadAllText/WriteAllText` 显式 UTF-8；
   ps1 需 UTF-8 BOM（bat 内置首次运行自动补 BOM 逻辑）。
7. **`--no-open` 不存在**：`dsh web` 实际只支持 --host/--port/--trusted-host，
   README 里的 `--no-open` 在 0.1.0-rc.6 会报 unknown option 退出。
8. **PS 里 `& npx -y "@pkg"` 首字母被吃**：调用符 & + 引号包裹的 scoped 包名
   会让 npm 收到 "px" 去装不相干的包（npm 日志 argv 可见）。启动脚本一律用
   裸写法 `npx -y @deepseek-ai/dsh ...`。
9. **bat 必须纯 ASCII + CRLF**：cmd 按 GBK 解析 UTF-8 中文注释会拼出幽灵
   命令行（报"不是内部或外部命令"）。

## 性能实测（2026-08-28）

- 引擎初始化（增量模式）：直连 4s / stdio 2s
- 工具响应：search_patents 0.6s，validate_claims 秒级
- dsh headless 单工具任务：约 40s（含 agent 推理两轮）
- case1 全量生成：headless 约 11 分钟 / web 会话约 8 分钟
