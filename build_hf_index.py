# -*- coding: utf-8 -*-
"""把 HF 52万篇中文专利 CSV 建成 SQLite FTS5 查新索引（jieba 分词）。

用法：python build_hf_index.py
产物：data/hf_patents/patents_hf.db（约 10-20 分钟，幂等——已存在则跳过）
"""

import csv
import sqlite3
import sys
import time
from pathlib import Path

import jieba

LAB = Path(__file__).resolve().parent
CSV_PATH = LAB / "data" / "hf_patents" / "patents_sample_500k.csv"
DB_PATH = LAB / "data" / "hf_patents" / "patents_hf.db"

BATCH = 3000


def seg(text: str) -> str:
    """jieba 搜索引擎模式分词，空格连接（FTS 索引/查询统一用此分词）"""
    return " ".join(jieba.cut_for_search(text or ""))


def main() -> None:
    if DB_PATH.exists():
        print("索引已存在，跳过（删除 patents_hf.db 可重建）")
        return
    if not CSV_PATH.exists():
        raise SystemExit(f"CSV 不存在: {CSV_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE patents (
            id INTEGER PRIMARY KEY,
            ptype TEXT, title TEXT, abstract TEXT,
            applicant_type TEXT, applicant_city TEXT,
            app_number TEXT, app_date TEXT, app_year TEXT, ipc TEXT
        )""")
    conn.execute("CREATE INDEX idx_ipc ON patents(ipc)")
    conn.execute("CREATE INDEX idx_appno ON patents(app_number)")
    conn.execute("""
        CREATE VIRTUAL TABLE patents_fts USING fts5(
            title_seg, abstract_seg,
            tokenize='unicode61'
        )""")

    t0 = time.time()
    rows = []
    total = 0
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append((
                row.get("专利类型", ""), row.get("专利名称", ""),
                row.get("摘要文本", ""), row.get("申请人类型", ""),
                row.get("申请人城市", ""), row.get("申请号", ""),
                row.get("申请日", ""), row.get("申请年份", ""),
                row.get("IPC主分类号", ""),
            ))
            if len(rows) >= BATCH:
                total += _flush(conn, rows)
                rows = []
                elapsed = time.time() - t0
                print(f"[{total}] 已入库 {elapsed:.0f}s", flush=True)
    if rows:
        total += _flush(conn, rows)

    conn.execute("INSERT INTO patents_fts(patents_fts) VALUES('optimize')")
    conn.commit()
    conn.execute("PRAGMA optimize")
    print(f"=== 建库完成：{total} 行，耗时 {time.time()-t0:.0f}s ===")
    conn.close()


def _flush(conn, rows):
    """插入一批：先写主表，再写 FTS（jieba 分词后）。

    主表自增 id 与 FTS rowid 同步递增（同批同序），检索侧按 p.id = f.rowid 关联。"""
    segmented = []
    for (ptype, title, abstract, atype, city, appno, adate, ayear, ipc) in rows:
        segmented.append((seg(title), seg(abstract)))
    cur = conn.cursor()
    cur.executemany(
        "INSERT INTO patents(ptype,title,abstract,applicant_type,applicant_city,"
        "app_number,app_date,app_year,ipc) VALUES (?,?,?,?,?,?,?,?,?)", rows)
    cur.executemany(
        "INSERT INTO patents_fts(title_seg,abstract_seg) VALUES (?,?)",
        segmented)
    conn.commit()
    return len(rows)


if __name__ == "__main__":
    main()
