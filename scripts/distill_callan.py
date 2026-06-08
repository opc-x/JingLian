#!/usr/bin/env python3
"""蒸馏为教材块结构（Lesson → Block → 词项 + 对练问答）。"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTRACTED_DIR = ROOT / "sources" / "callan" / "extracted"
DISTILLED_DIR = ROOT / "distilled" / "callan"
CEFR_PATH = ROOT / "data" / "callan" / "cefr.json"


def load_extracted(book: int) -> dict:
    src = EXTRACTED_DIR / f"book-{book:02d}.json"
    if not src.exists():
        raise SystemExit(f"Missing extracted file: {src}")
    data = json.loads(src.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {"book": book, "chartManifest": {}, "lessons": data}
    return data


def distill_lesson(lesson: dict, book: int, chart_manifest: dict) -> dict:
    blocks = []
    for b in lesson.get("blocks", []):
        chart_ref = b.get("chartRef")
        chart_file = chart_manifest.get(str(chart_ref)) if chart_ref else None
        if chart_ref and not chart_file:
            chart_file = chart_manifest.get(chart_ref)
        blocks.append({
            **b,
            "chartFile": chart_file,
            "title": _block_title(b),
        })

    return {
        "source": f"callan/book-{book:02d}/lesson-{lesson['lessonId']:02d}",
        "distilledAt": date.today().isoformat(),
        "book": book,
        "lessonId": lesson["lessonId"],
        "title": lesson.get("title", f"Lesson {lesson['lessonId']}"),
        "blockCount": len(blocks),
        "stats": {
            "vocabulary": sum(len(b["vocabulary"]) for b in blocks),
            "drills": sum(len(b["drills"]) for b in blocks),
            "blocks": len(blocks),
        },
        "blocks": blocks,
        "reviewNotes": "按教材原块学习：每块先读词条带，再练对练问答；遇 See Chart 请对照图表。",
    }


def _block_title(block: dict) -> str:
    words = block.get("focusWords") or []
    if not words:
        return f"块 {block.get('blockId', '?')}"
    preview = " · ".join(words[:6])
    if len(words) > 6:
        preview += " …"
    return preview


def distill_book(book: int) -> dict:
    raw = load_extracted(book)
    chart_manifest = raw.get("chartManifest", {})
    lessons = [distill_lesson(ls, book, chart_manifest) for ls in raw["lessons"]]

    cefr = "—"
    if CEFR_PATH.exists():
        cefr_data = json.loads(CEFR_PATH.read_text(encoding="utf-8"))
        cefr = cefr_data.get("bookCefr", {}).get(str(book), "—")

    return {
        "book": book,
        "title": f"Callan Method Book {book}",
        "cefr": cefr,
        "chartManifest": chart_manifest,
        "distilledAt": date.today().isoformat(),
        "lessonCount": len(lessons),
        "stats": {
            "vocabulary": sum(l["stats"]["vocabulary"] for l in lessons),
            "drills": sum(l["stats"]["drills"] for l in lessons),
            "blocks": sum(l["stats"]["blocks"] for l in lessons),
        },
        "lessons": lessons,
    }


def generate_path(catalog_books: list[dict]) -> dict:
    cefr_data = json.loads(CEFR_PATH.read_text(encoding="utf-8"))
    nodes = []
    for b in catalog_books:
        book_num = b["book"]
        cefr = cefr_data.get("bookCefr", {}).get(str(book_num), "?")
        book_path = DISTILLED_DIR / b["file"]
        if not book_path.exists():
            continue
        book_data = json.loads(book_path.read_text(encoding="utf-8"))
        for les in book_data["lessons"]:
            nodes.append({
                "book": book_num,
                "lessonId": les["lessonId"],
                "title": les["title"],
                "cefr": cefr,
                "blocks": les["stats"]["blocks"],
                "vocabulary": les["stats"]["vocabulary"],
                "drills": les["stats"]["drills"],
            })

    return {
        "title": "Callan Method 学习路径",
        "updatedAt": date.today().isoformat(),
        "totalLessons": len(nodes),
        "cefrLevels": cefr_data.get("levels", []),
        "nodes": nodes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", type=int)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    books = range(1, 13) if args.all else [args.book or 1]

    catalog_entries: list[dict] = []
    for book in books:
        src = EXTRACTED_DIR / f"book-{book:02d}.json"
        if not src.exists():
            print(f"Book {book}: SKIP")
            continue
        catalog_entries.append(_distill_and_save(book))

    if catalog_entries:
        index_path = DISTILLED_DIR / "index.json"
        index = {"books": [], "updatedAt": date.today().isoformat()}
        if index_path.exists():
            index = json.loads(index_path.read_text(encoding="utf-8"))
        books_map = {b["book"]: b for b in index.get("books", [])}
        for e in catalog_entries:
            books_map[e["book"]] = e
        index["books"] = sorted(books_map.values(), key=lambda b: b["book"])
        index["updatedAt"] = date.today().isoformat()
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
        (DISTILLED_DIR / "path.json").write_text(
            json.dumps(generate_path(index["books"]), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if CEFR_PATH.exists():
            (DISTILLED_DIR / "cefr.json").write_text(
                CEFR_PATH.read_text(encoding="utf-8"), encoding="utf-8"
            )


def _distill_and_save(book: int) -> dict:
    data = distill_book(book)
    DISTILLED_DIR.mkdir(parents=True, exist_ok=True)
    book_path = DISTILLED_DIR / f"book-{book:02d}.json"
    book_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Book {book} [{data['cefr']}]: {data['lessonCount']} lessons, "
        f"{data['stats']['blocks']} blocks, {data['stats']['drills']} drills"
    )
    return {
        "book": book,
        "title": data["title"],
        "file": f"book-{book:02d}.json",
        "lessonCount": data["lessonCount"],
        "cefr": data["cefr"],
        "stats": data["stats"],
        "distilledAt": data["distilledAt"],
    }


if __name__ == "__main__":
    main()
