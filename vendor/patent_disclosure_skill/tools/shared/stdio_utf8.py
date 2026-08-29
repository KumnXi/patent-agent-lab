"""Windows 终端 UTF-8：当前进程 stdio 设为 UTF-8，并为子进程准备 PYTHONUTF8。

PowerShell 5 会把写入 stderr 标成 NativeCommandError，但退出码仍可能是 0。
Agent 应以退出码和机读前缀为准，不要把 stderr 当失败。

注：本文件从上游 patent-disclosure-skill 裁剪而来——移除了其通用
subprocess 透传助手（run/child_env），本仓库内只用 ensure_utf8_stdio。
"""
from __future__ import annotations

import os
import sys


def ensure_utf8_stdio() -> None:
    """当前进程 stdout/stderr 按 UTF-8；并为子进程准备 PYTHONUTF8。"""
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    for stream in (sys.stdout, sys.stderr):
        try:
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError, TypeError):
            pass
