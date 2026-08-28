"""对比报告：旧流水线成品 vs patent-agent 成品，用同一把尺子度量。

尺子 = 旧项目自己的三个校验器 + 8 维质检评分，对两份交底书分别跑，
输出 output/compare_report.md。

用法：
    python run_compare.py \
        --old "patent-aid项目/output/流水线成品_高温蒸汽管道_公式增强版.docx" \
        [--agent output/xxx_agent.md]   # 缺省取 output/ 下最新 *_agent.md
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

OLD_PROJECT = Path(os.environ.get(
    "PATENT_PROJECT_PATH", r"D:\Jupyter code\专利撰写助手"))
sys.path.insert(0, str(OLD_PROJECT))

LAB = Path(__file__).resolve().parent

SECTIONS = ["发明名称", "摘要", "权利要求书", "技术领域",
            "背景技术", "发明内容", "附图说明", "具体实施方式"]

CASE1_IDEA = ("一种基于有限元仿真与人工智能的高温蒸汽管道缺陷评估及剩余寿命预测方法")


def extract_docx_text(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def latest_agent_md() -> Path:
    outs = sorted((LAB / "output").glob("*_agent.md"))
    if not outs:
        raise SystemExit("output/ 下没有 *_agent.md，先跑 agent 生成")
    return outs[-1]


def section_coverage(text: str) -> dict:
    return {s: (s in text) for s in SECTIONS}


def run_validators(text: str, engine) -> dict:
    from src.core.claim_validator import validate_claims
    from src.core.compliance_checker import ComplianceChecker
    from src.core.data_authenticity_checker import DataAuthenticityChecker
    from src.core.quality_reviewer import QualityReviewer

    out = {}
    claims = validate_claims(text)
    out["claims"] = {"total": claims.get("total"),
                     "valid": claims.get("valid"),
                     "issues": len(claims.get("issues", []))}
    comp = ComplianceChecker(engine.db_loader).check(text, CASE1_IDEA)
    out["compliance_issues"] = len(comp.get("issues", []))
    auth = DataAuthenticityChecker().check(text, CASE1_IDEA, None)
    out["authenticity_issues"] = len(auth.get("issues", []))
    review = QualityReviewer(engine).review(text, CASE1_IDEA)
    out["quality_score"] = review.get("total_score")
    out["quality_grade"] = review.get("grade")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True, help="旧流水线成品 docx 路径")
    ap.add_argument("--agent", default=None, help="agent 成品 md 路径")
    args = ap.parse_args()

    old_path = Path(args.old)
    agent_path = Path(args.agent) if args.agent else latest_agent_md()

    old_text = extract_docx_text(old_path)
    agent_text = agent_path.read_text(encoding="utf-8")

    print("初始化引擎（复用校验器，约 5-20s）...")
    from src.core import PatentInnovationEngine

    engine = PatentInnovationEngine()
    engine.initialize()

    print("对旧成品跑校验...")
    old_metrics = run_validators(old_text, engine)
    old_metrics["sections"] = section_coverage(old_text)
    print("对 agent 成品跑校验...")
    agent_metrics = run_validators(agent_text, engine)
    agent_metrics["sections"] = section_coverage(agent_text)

    def fmt(name, m, chars):
        sec = "".join("✔" if v else "✘" for v in m["sections"].values())
        return (f"| {name} | {chars} | {sec} "
                f"| {m['quality_score']}（{m['quality_grade']}） "
                f"| {m['claims']['total']}（issues {m['claims']['issues']}） "
                f"| {m['compliance_issues']} | {m['authenticity_issues']} |")

    lines = [
        "# 对比报告：旧流水线 vs patent-agent",
        "",
        f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}",
        f"- 旧成品：`{old_path.name}`",
        f"- agent 成品：`{agent_path.name}`",
        "",
        "章节覆盖顺序：发明名称/摘要/权利要求书/技术领域/背景技术/"
        "发明内容/附图说明/具体实施方式",
        "",
        "| 产物 | 字数 | 8章节 | 质检分 | 权利要求 | 合规issues | 真实性issues |",
        "|---|---|---|---|---|---|---|",
        fmt("旧流水线", old_metrics, len(old_text)),
        fmt("agent", agent_metrics, len(agent_text)),
        "",
    ]
    report = LAB / "output" / "compare_report.md"
    report.parent.mkdir(exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n报告已写入 {report}\n")
    print("\n".join(lines[6:]))


if __name__ == "__main__":
    main()
