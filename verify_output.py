"""独立验收：对 agent 产出的交底书跑完整校验 + 引用专利号核对。

用法：python verify_output.py <md路径>
需先设置 PATENT_PROJECT_PATH 环境变量（或使用默认路径）。
"""

import json
import os
import re
import sys
from pathlib import Path

OLD_PROJECT = Path(os.environ.get(
    "PATENT_PROJECT_PATH", r"D:\Jupyter code\专利撰写助手"))
sys.path.insert(0, str(OLD_PROJECT))

IDEA = "一种基于有限元仿真与人工智能的高温蒸汽管道缺陷评估及剩余寿命预测方法"
CITED = ["CN117890472A", "CN112233133B", "CN113284109B",
         "CN118129088B", "CN115272271B", "CN107748200B"]


def main() -> None:
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    print(f"总字符: {len(text)}")

    m = re.search(r"## 摘要\n\n(.+?)\n\n## ", text, re.DOTALL)
    if m:
        print(f"摘要字数: {len(m.group(1))}（限制300）")

    from src.core import PatentInnovationEngine
    engine = PatentInnovationEngine()
    engine.initialize()

    from src.core.claim_validator import validate_claims
    claims = validate_claims(text)
    print(f"[权利要求] total={claims.get('total')} valid={claims.get('valid')} "
          f"issues={claims.get('issues', [])}")

    from src.core.compliance_checker import ComplianceChecker
    comp = ComplianceChecker(engine.db_loader).check(text, IDEA)
    print(f"[合规] issues={len(comp.get('issues', []))}")
    for i in comp.get("issues", [])[:5]:
        print("   -", str(i)[:120])

    from src.core.data_authenticity_checker import DataAuthenticityChecker
    auth = DataAuthenticityChecker().check(text, IDEA, None)
    print(f"[真实性] issues={len(auth.get('issues', []))}")
    for i in auth.get("issues", [])[:8]:
        print("   -", str(i)[:150])

    from src.core.quality_reviewer import QualityReviewer
    review = QualityReviewer(engine).review(text, IDEA)
    print(f"[质检] total={review.get('total_score')} grade={review.get('grade')}")

    print("[引用核对] 逐个专利号在库内检索：")
    for pid in CITED:
        try:
            p = engine.db_loader.get_patent_by_id(pid)
            print(f"   {pid}: {'✔ 库内存在' if p else '✘ 库内不存在'}")
        except Exception as e:
            print(f"   {pid}: 查询异常 {e}")


if __name__ == "__main__":
    main()
