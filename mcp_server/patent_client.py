"""patent MCP 服务器的 stdio 客户端桥（供 agent 在无 MCP 工具暴露时调用）。

用法:
    python patent_client.py <tool> '<json args>'
    python patent_client.py search_patents '{"query": "高温蒸汽管道缺陷检测", "top_k": 5}'
    python patent_client.py save_draft_section '{"section": "摘要", "content": "..."}'

返回：工具输出文本（JSON 或全文）打印到 stdout。
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = str(Path(__file__).resolve().parent / "patent_server.py")
PYTHON = os.environ.get("PATENT_PYTHON", sys.executable)


async def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python patent_client.py <tool> '<json args>'", file=sys.stderr)
        return 2
    tool = sys.argv[1]
    # 便捷模式：python patent_client.py save_draft_section --section 摘要 --file x.txt
    if tool == "save_draft_section" and "--section" in sys.argv:
        i = sys.argv.index("--section")
        section = sys.argv[i + 1]
        j = sys.argv.index("--file")
        with open(sys.argv[j + 1], encoding="utf-8") as f:
            content = f.read()
        args = {"section": section, "content": content}
    else:
        raw = sys.argv[2] if len(sys.argv) > 2 else ""
        if raw.startswith("@"):
            with open(raw[1:], encoding="utf-8") as f:
                raw = f.read()
        try:
            args = json.loads(raw) if raw else {}
        except json.JSONDecodeError as e:
            print(f"bad json args: {e}", file=sys.stderr)
            return 2
    if not isinstance(args, dict):
        print("args must be a json object", file=sys.stderr)
        return 2

    env = dict(os.environ)
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONUNBUFFERED", "1")
    params = StdioServerParameters(command=PYTHON, args=[SERVER], env=env)

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool, args)
    for c in result.content:
        text = getattr(c, "text", None)
        if text:
            print(text)
        else:
            structured = getattr(c, "structuredContent", None)
            if structured is not None:
                print(json.dumps(structured, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
