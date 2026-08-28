"""patent_server 冒烟测试：绕过 MCP 传输，直接调工具函数验证引擎链路。

用法：python test_smoke.py
预期：引擎预热后检索可用；草稿写入与校验工具返回结构正确。
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "mcp_server"))

import patent_server as ps  # noqa: E402  (import 即触发引擎预热)


def main() -> None:
    t0 = time.time()
    eng = ps._engine_ready(240)
    assert eng is not None, "引擎 240s 内未就绪"
    if eng is None or not ps._ready.is_set():
        raise SystemExit("引擎预热失败")
    print(f"[1] 引擎就绪，耗时 {time.time() - t0:.0f}s")

    r = json.loads(ps.search_patents("高温蒸汽管道 缺陷评估 剩余寿命", top_k=3))
    assert "error" not in r, f"检索失败: {r}"
    print(f"[2] 检索 OK: 相关专利 {len(r.get('related_patents', []))} 条, "
          f"方案 {len(r.get('related_solutions', []))} 条")

    r2 = json.loads(ps.query_knowledge_graph("高温蒸汽管道缺陷评估"))
    assert "error" not in r2, f"图谱失败: {r2}"
    print(f"[3] 图谱 OK: 方案 {len(r2.get('solutions', []))} 条, "
          f"替代 {len(r2.get('alternatives', []))} 条")

    r3 = json.loads(ps.start_disclosure(
        "测试想法：基于深度学习的管道缺陷检测", "一种基于深度学习的管道缺陷检测方法"))
    print(f"[4] 开稿 OK: {r3}")

    filler = ("本发明涉及管道检测技术领域，具体涉及缺陷识别与量化评估方法，"
              "可用于长输管道的运行维护。") * 30
    r4 = json.loads(ps.save_draft_section("技术领域", filler))
    assert "error" not in r4, r4
    print(f"[5] 存章 OK: {r4['sections_saved']}")

    short = json.loads(ps.save_draft_section("摘要", "太短"))
    assert "error" in short, "过短内容应被拒绝"
    print("[6] 过短拦截 OK")

    full = ps.read_full_draft()
    assert "技术领域" in full and len(full) > 1000
    print(f"[7] 回读 OK: 全文 {len(full)} 字")

    r5 = json.loads(ps.validate_claims())
    print(f"[8] 权利要求校验返回结构 OK: {str(r5)[:150]}")

    print("\n全部通过 ✔")


if __name__ == "__main__":
    main()
