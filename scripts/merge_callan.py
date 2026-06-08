#!/usr/bin/env python3
"""生成书库目录：一级类目 → 分册卡片（首页直接展示）→ 课程列表。"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAITHFUL_DIR = ROOT / "sources" / "callan" / "faithful"
CAT_ID = "callan-method"


def build_catalog(books: list[int]) -> None:
    volumes: list[dict] = []
    total_lessons = 0
    total_pages = 0

    for b in sorted(books):
        f = FAITHFUL_DIR / f"book-{b:02d}.json"
        if not f.exists():
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        lessons = data.get("lessons", [])
        page_count = sum(l.get("pageCount", len(l.get("pages", []))) for l in lessons)
        vol_cover = lessons[0]["pages"][0]["image"] if lessons and lessons[0].get("pages") else None
        total_lessons += data["lessonCount"]
        total_pages += page_count
        volumes.append({
            "book": b,
            "title": f"Book {b}",
            "file": f"faithful/book-{b:02d}.json",
            "annotationFile": f"annotations/book-{b:02d}.json",
            "lessonCount": data["lessonCount"],
            "pageCount": page_count,
            "coverImage": vol_cover,
            "cefr": data.get("cefr", "—"),
        })

    catalog = {
        "mode": "faithful",
        "categories": [
            {
                "id": CAT_ID,
                "title": "Callan Method",
                "subtitle": "英语口语速成全系列",
                "cefr": "A1 → B2",
                "bookCount": len(volumes),
                "lessonCount": total_lessons,
                "pageCount": total_pages,
                "books": volumes,
            }
        ],
    }
    (FAITHFUL_DIR / "index.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"Catalog: {len(catalog['categories'])} 类目 · {len(volumes)} 册 · "
        f"{total_lessons} 课 · {total_pages} 页"
    )


if __name__ == "__main__":
    build_catalog(list(range(1, 13)))
