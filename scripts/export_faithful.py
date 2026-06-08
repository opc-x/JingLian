#!/usr/bin/env python3
"""
原样导出教材：PDF 页图 + 逐行原文（仅解密显示用字符，不改写、不删减、不修复）。
批注请写入 annotations/，不得修改此处内容。
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import fitz

from extract_callan import (
    RAW_DIR,
    ROOT,
    _page_lines,
    decrypt_qa_part,
    detect_lesson_sequence,
    is_encrypted_line,
)

FAITHFUL_DIR = ROOT / "sources" / "callan" / "faithful"
PAGES_DIR = ROOT / "sources" / "callan" / "pages"
ANNOTATIONS_DIR = ROOT / "annotations" / "callan"


def verbatim_line(line: str) -> dict:
    """保留原文；加密行仅做解密以便阅读，不做语义改写。"""
    if is_encrypted_line(line):
        return {
            "text": decrypt_qa_part(line),
            "encrypted": True,
        }
    return {"text": line, "encrypted": False}


def export_lesson_pages(
    doc: fitz.Document, book: int, lesson_id: int, page_nums: list[int]
) -> list[dict]:
    pages_out = []
    page_dir = PAGES_DIR / f"book-{book:02d}"
    page_dir.mkdir(parents=True, exist_ok=True)

    for pnum in page_nums:
        rel_img = f"pages/book-{book:02d}/lesson-{lesson_id:02d}-p{pnum:03d}.png"
        img_path = ROOT / "sources" / "callan" / rel_img
        if not img_path.exists():
            pix = doc[pnum].get_pixmap(matrix=fitz.Matrix(2, 2))
            img_path.parent.mkdir(parents=True, exist_ok=True)
            pix.save(str(img_path))

        lines = [verbatim_line(ln) for ln in _page_lines(doc, pnum)]
        pages_out.append({
            "pageNum": pnum,
            "image": rel_img,
            "lineCount": len(lines),
            "lines": lines,
        })
    return pages_out


def lesson_page_nums(
    doc: fitz.Document, valid_set: set[int], page_start: int, page_end: int
) -> dict[int, list[int]]:
    """每课包含哪些 PDF 页码。"""
    lesson_pages: dict[int, list[int]] = {}
    current: int | None = None

    for pnum in range(page_start, page_end + 1):
        lines = _page_lines(doc, pnum)
        for line in lines:
            m = re.match(r"^LESSON\s+(\d+)\s*$", line, re.I)
            if m:
                lid = int(m.group(1))
                if lid in valid_set:
                    current = lid
                    lesson_pages.setdefault(lid, [])
                break
        if current is not None:
            if pnum not in lesson_pages[current]:
                lesson_pages[current].append(pnum)

    return lesson_pages


def build_annotation_stub(book: int, lessons: list[dict], cefr: str) -> dict:
    """批注层：与原文分离，可随意增补，不触碰教材正文。"""
    items = []
    for les in lessons:
        for pg in les["pages"]:
            items.append({
                "lessonId": les["lessonId"],
                "pageNum": pg["pageNum"],
                "notes": [],
                "cefr": cefr,
                "hints": [
                    "灰色区域为教材原页图像，未经改写。",
                    "此处可追加 AI 批注、词项提示、复习建议等。",
                ],
            })
    return {"book": book, "annotations": items}


def export_book(book: int) -> None:
    pdf_path = RAW_DIR / f"book-{book:02d}.pdf"
    doc = fitz.open(pdf_path)
    valid_ids, page_start, page_end = detect_lesson_sequence(doc)
    valid_set = set(valid_ids)
    lmap = lesson_page_nums(doc, valid_set, page_start, page_end)

    cefr = "—"
    cefr_path = ROOT / "data" / "callan" / "cefr.json"
    if cefr_path.exists():
        cefr = json.loads(cefr_path.read_text(encoding="utf-8")).get("bookCefr", {}).get(str(book), "—")

    lessons = []
    for lid in sorted(lmap.keys()):
        pages = export_lesson_pages(doc, book, lid, lmap[lid])
        lessons.append({
            "lessonId": lid,
            "title": f"Lesson {lid}",
            "pageCount": len(pages),
            "pages": pages,
        })

    payload = {
        "book": book,
        "mode": "faithful",
        "policy": "教材原样保留：页图 + 逐行原文。禁止在此文件内做蒸馏/修复/删改。",
        "title": f"Callan Method Book {book}",
        "cefr": cefr,
        "lessonCount": len(lessons),
        "lessons": lessons,
    }

    FAITHFUL_DIR.mkdir(parents=True, exist_ok=True)
    out = FAITHFUL_DIR / f"book-{book:02d}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)
    ann = build_annotation_stub(book, lessons, cefr)
    (ANNOTATIONS_DIR / f"book-{book:02d}.json").write_text(
        json.dumps(ann, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    doc.close()
    print(f"Book {book}: faithful export {len(lessons)} lessons, {sum(l['pageCount'] for l in lessons)} pages → {out}")


def build_index(books: list[int]) -> None:
    entries = []
    for b in books:
        f = FAITHFUL_DIR / f"book-{b:02d}.json"
        if not f.exists():
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        lessons = data.get("lessons", [])
        page_count = sum(l.get("pageCount", len(l.get("pages", []))) for l in lessons)
        cover = None
        if lessons and lessons[0].get("pages"):
            cover = lessons[0]["pages"][0].get("image")
        entries.append({
            "book": b,
            "title": data["title"],
            "file": f"faithful/book-{b:02d}.json",
            "annotationFile": f"annotations/book-{b:02d}.json",
            "lessonCount": data["lessonCount"],
            "pageCount": page_count,
            "coverImage": cover,
            "cefr": data.get("cefr", "—"),
        })
    index = {
        "mode": "faithful",
        "books": sorted(entries, key=lambda x: x["book"]),
    }
    (FAITHFUL_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Faithful Callan export (zero content mutation)")
    parser.add_argument("--book", type=int)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    books = list(range(1, 13)) if args.all else [args.book or 1]
    done = []
    for b in books:
        if not (RAW_DIR / f"book-{b:02d}.pdf").exists():
            print(f"Book {b}: SKIP")
            continue
        export_book(b)
        done.append(b)
    if done:
        from merge_callan import build_catalog

        build_catalog(done)


if __name__ == "__main__":
    main()
