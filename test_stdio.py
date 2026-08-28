"""stdio 链路复现测试：用真实 MCP 客户端连本地 patent_server，
完全模拟 dsh 的调用路径，验证协议层可用。

用法：python test_stdio.py
"""

import asyncio
import sys
import time
from pathlib import Path

SERVER = [sys.executable,
          str(Path(__file__).resolve().parent / "mcp_server" / "patent_server.py")]


def _server_env():
    import os

    env = dict(os.environ)
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONUNBUFFERED", "1")
    return env


async def main() -> None:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    t0 = time.time()
    params = StdioServerParameters(command=SERVER[0], args=SERVER[1:],
                                   env=_server_env())
    async with stdio_client(params) as (read, write):
        print(f"[1] 进程启动 {time.time()-t0:.1f}s")
        async with ClientSession(read, write) as session:
            await session.initialize()
            print(f"[2] initialize 完成 {time.time()-t0:.1f}s")

            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            print(f"[3] 工具列表 {time.time()-t0:.1f}s: {names}")

            t1 = time.time()
            res = await asyncio.wait_for(
                session.call_tool("get_terminology", {"term": "漏磁检测"}),
                timeout=90)
            print(f"[4] get_terminology 返回（等待 {time.time()-t1:.1f}s，"
                  f"总 {time.time()-t0:.1f}s）: {res.content[0].text[:200]}")

            t2 = time.time()
            res2 = await asyncio.wait_for(
                session.call_tool("search_patents",
                                  {"query": "高温蒸汽管道缺陷评估", "top_k": 3}),
                timeout=90)
            print(f"[5] search_patents 返回（等待 {time.time()-t2:.1f}s，"
                  f"总 {time.time()-t0:.1f}s）: "
                  f"{res2.content[0].text[:150]}")

    print("stdio 链路 OK ✔")


if __name__ == "__main__":
    asyncio.run(main())
