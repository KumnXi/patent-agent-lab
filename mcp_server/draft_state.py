"""agent 写作草稿的工作区。

dsh agent 通过 patent_server 的工具读写这里的草稿状态；校验类工具读取
同一状态，避免大段文本在工具参数里来回传。

状态文件：data/draft_state.json（UTF-8，不入库）。
"""

import json
import re
import threading
from datetime import datetime
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = LAB_ROOT / "data" / "draft_state.json"

# 标准章节顺序（与旧项目 _assemble 一致：名称→摘要→权利要求→说明书五部分）
SECTION_ORDER = [
    "发明名称", "摘要", "权利要求书",
    "技术领域", "背景技术", "发明内容", "附图说明", "具体实施方式",
]

_lock = threading.Lock()


def _load() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"idea": "", "title": "", "sections": {}, "updated_at": ""}


def _save(state: dict) -> None:
    state["updated_at"] = datetime.now().isoformat(timespec="seconds")
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8"
    )


def start(idea: str, title: str) -> dict:
    """开新草稿：记录想法与发明名称，清空已有章节。"""
    with _lock:
        state = {"idea": idea, "title": title, "sections": {}, "updated_at": ""}
        _save(state)
    return stats()


def save_section(name: str, content: str) -> dict:
    """保存/覆盖一个章节。"""
    with _lock:
        state = _load()
        state["sections"][name] = content.strip()
        _save(state)
    return stats()


def replace_full_text(text: str) -> dict:
    """按 "## 标题" 切分整篇文本并覆盖全部章节（自动修复后回写用）。"""
    sections = {}
    for part in re.split(r"\n(?=##\s)", text.strip()):
        m = re.match(r"##\s+(.+?)\s*\n", part)
        if m:
            sections[m.group(1).strip()] = part[m.end():].strip()
        elif part.strip():
            sections.setdefault("未命名", part.strip())
    with _lock:
        state = _load()
        state["sections"] = sections
        _save(state)
    return stats()


def full_text() -> str:
    """按标准章节顺序拼装全文。"""
    state = _load()
    sections = state.get("sections", {})
    ordered = [s for s in SECTION_ORDER if s in sections]
    ordered += [s for s in sections if s not in SECTION_ORDER]
    parts = []
    if state.get("title"):
        parts.append(f"# {state['title']}")
    for name in ordered:
        parts.append(f"## {name}\n\n{sections[name]}")
    return "\n\n".join(parts)


def idea() -> str:
    return _load().get("idea", "")


def stats() -> dict:
    state = _load()
    sections = state.get("sections", {})
    return {
        "title": state.get("title", ""),
        "sections_saved": list(sections.keys()),
        "total_chars": sum(len(v) for v in sections.values()),
        "updated_at": state.get("updated_at", ""),
    }
