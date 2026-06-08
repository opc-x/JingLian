#!/usr/bin/env python3
"""从 Callan Method PDF 提取 Lesson / 词汇 / 问答对（支持 Book 1–12 自动探测）。"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "sources" / "callan" / "raw"
OUT_DIR = ROOT / "sources" / "callan" / "extracted"


def decrypt_vocab_eng(text: str) -> str:
    res = []
    for c in text:
        val = ord(c)
        if 35 <= val <= 60:
            res.append(chr(val + 29))
        elif 61 <= val <= 126:
            res.append(chr(val - 3))
        else:
            res.append(c)
    return "".join(res)


def decrypt_vocab_zh(text: str) -> str:
    res = []
    for c in text:
        val = ord(c)
        if val >= 0x2000:
            res.append(chr(val + 0x1E58))
        else:
            res.append(c)
    return "".join(res)


def is_encrypted_line(line: str) -> bool:
    has_ctrl = any(0 < ord(c) < 32 and c not in "\r\n\t" for c in line)
    has_lowercase = any(97 <= ord(c) <= 122 for c in line)
    return (has_ctrl or "*" in line) and not has_lowercase


def is_question(line: str) -> bool:
    if is_encrypted_line(line):
        return True
    if line.endswith("?"):
        return True
    prefixes = [
        "Am I", "Are you", "Is ", "Where's", "Where is", "Which", "What",
        "How many", "What's", "Is", "Where", "What", "Do ", "Does ", "Did ",
        "Have ", "Has ", "Can ", "Will ", "Would ",
    ]
    return any(line.startswith(p) for p in prefixes)


def clean_text(text: str) -> str:
    text = text.replace("'", "'").replace("'", "'").replace(""", '"').replace(""", '"')
    text = text.replace("`", "'").replace("´", "'")
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
    text = "".join(c for c in text if ord(c) >= 32 or c in "\n\t")
    return re.sub(r"\s+", " ", text).strip()


def can_be_continued(text: str) -> bool:
    text = text.strip().lower()
    if not text:
        return False
    if text.endswith((",", ";", ":")):
        return True
    words = re.findall(r"[a-zA-Z']+", text)
    if not words:
        return False
    incomplete = {
        "the", "a", "an", "of", "in", "under", "behind", "front", "on", "at", "to", "from",
        "isn't", "aren't", "is", "are", "am", "was", "were", "will", "would", "should",
        "could", "have", "has", "had", "do", "does", "did", "with", "about", "by", "for",
        "first", "second", "third", "fourth", "fifth", "last",
        "you're", "he's", "she's", "it's", "we're", "they're", "i'm",
    }
    return words[-1] in incomplete


def format_vocab_word(w: str) -> str:
    w = w.strip()
    return w[0].upper() + w[1:] if w else ""


def decrypt_qa_part(part: str) -> str:
    if not is_encrypted_line(part):
        return part
    dec_part = []
    for c in part:
        val = ord(c)
        if val == 509:
            dec_part.append("'")
        elif val == 511:
            dec_part.append('"')
        elif val < 127:
            dec_part.append(chr(val + 31))
        else:
            dec_part.append(c)
    return "".join(dec_part)


def build_vocab_map(doc: fitz.Document) -> dict[str, str]:
    """全书扫描加密词汇表。"""
    vocab_map: dict[str, str] = {}
    for page_num in range(len(doc)):
        for line in doc[page_num].get_text("text").split("\n"):
            line_str = line.strip()
            if not line_str or len(line_str) < 2:
                continue
            eng_dec = decrypt_vocab_eng(line_str)
            eng_cleaned = "".join(
                c for c in eng_dec
                if ord(c) < 127
                and c not in "\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\x0b\x0c\x0e\x0f"
                "\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f"
            )
            eng_cleaned = (
                eng_cleaned.replace("\x11", "")
                .replace("\x03", " ")
                .replace("\x0b", "")
                .replace("\x0c", "")
                .strip()
            )
            eng_final = "".join(
                c for c in eng_cleaned if c.isalnum() or c in " ,()'·.-/"
            ).strip()
            eng_final = re.sub(r" +", " ", eng_final)
            if not eng_final or len(eng_final) > 50:
                continue
            zh_dec = decrypt_vocab_zh(line_str)
            zh_final = "".join(
                c for c in zh_dec if 0x4E00 <= ord(c) <= 0x9FFF
            ).strip()
            if eng_final and zh_final:
                vocab_map[eng_final.upper()] = zh_final
    return vocab_map


def detect_lesson_sequence(doc: fitz.Document) -> tuple[list[int], int, int]:
    """探测主课次序列与页码范围。"""
    occurrences: list[tuple[int, int]] = []
    scan_end = min(len(doc), 110)

    for page_num in range(10, scan_end):
        blocks = doc[page_num].get_text("blocks")
        blocks = sorted(blocks, key=lambda b: (round(b[1] / 10), b[0]))
        for b in blocks:
            lines = [l.strip() for l in b[4].strip().split("\n") if l.strip()]
            if not lines:
                continue
            m = re.match(r"^LESSON\s+(\d+)\s*$", lines[0], re.IGNORECASE)
            if m:
                occurrences.append((page_num, int(m.group(1))))
                break

    if not occurrences:
        return [], 12, 40

    best_seq: list[int] = []
    best_start_page = 12
    best_end_page = 40

    for i, (start_page, start_id) in enumerate(occurrences):
        seq = [start_id]
        pages = [start_page]
        prev = start_id
        for j in range(i + 1, len(occurrences)):
            p2, lid = occurrences[j]
            if lid > prev and lid - prev <= 5:
                seq.append(lid)
                pages.append(p2)
                prev = lid
        if len(seq) > len(best_seq):
            best_seq = seq
            best_start_page = pages[0]
            best_end_page = min(scan_end - 1, pages[-1] + 8)

    return best_seq, best_start_page, best_end_page


def _page_lines(doc: fitz.Document, page_num: int) -> list[str]:
    blocks = doc[page_num].get_text("blocks")
    blocks = sorted(blocks, key=lambda b: (round(b[1] / 10), b[0]))
    lines: list[str] = []
    for b in blocks:
        for line in b[4].split("\n"):
            s = line.strip()
            if s:
                lines.append(s)
    return lines


def _lesson_page_map(
    doc: fitz.Document, valid_set: set[int], page_start: int, page_end: int
) -> dict[int, list[str]]:
    """按课收集页面文本行。"""
    lesson_lines: dict[int, list[str]] = {}
    current_id: int | None = None

    for page_num in range(page_start, page_end + 1):
        for line in _page_lines(doc, page_num):
            m = re.match(r"^LESSON\s+(\d+)\s*$", line, re.I)
            if m:
                lid = int(m.group(1))
                if lid in valid_set:
                    current_id = lid
                    lesson_lines.setdefault(lid, [])
                continue
            if current_id is not None:
                if line.upper().startswith("REVISION EXERCISE"):
                    continue
                lesson_lines[current_id].append(line)
    return lesson_lines


def extract_charts(doc: fitz.Document, book: int) -> dict[int, str]:
    """导出 Chart 页为 PNG，返回 chartNo → 相对路径。"""
    from block_parser import CHART_RE  # noqa: F401

    chart_dir = ROOT / "sources" / "callan" / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[int, str] = {}
    current_chart: int | None = None

    for page_num in range(len(doc)):
        lines = _page_lines(doc, page_num)
        if not lines:
            continue
        head = lines[0].strip()
        m = re.match(r"^Chart\s+(\d+)\s*$", head, re.I)
        if m:
            current_chart = int(m.group(1))
        if current_chart is None:
            continue
        # 跳过 Index / 词汇索引页
        if head.lower() in {"index", "chart 1"} and page_num > 50:
            pass
        rel = f"charts/book-{book:02d}-chart-{current_chart:02d}-p{page_num:03d}.png"
        out = chart_dir / rel.replace("charts/", "")
        if not out.exists():
            pix = doc[page_num].get_pixmap(matrix=fitz.Matrix(2, 2))
            out.parent.mkdir(parents=True, exist_ok=True)
            pix.save(str(out))
        if current_chart not in manifest:
            manifest[current_chart] = f"charts/book-{book:02d}-chart-{current_chart:02d}-p{page_num:03d}.png"

    meta_path = chart_dir / f"book-{book:02d}-charts.json"
    meta_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def parse_pdf(pdf_path: Path, output_path: Path) -> int:
    from block_parser import finalize_block, parse_page_blocks

    doc = fitz.open(pdf_path)
    book = int(re.search(r"book-(\d+)", pdf_path.name).group(1))
    vocab_map = build_vocab_map(doc)
    valid_ids, page_start, page_end = detect_lesson_sequence(doc)
    valid_set = set(valid_ids)
    lesson_lines = _lesson_page_map(doc, valid_set, page_start, page_end)
    chart_manifest = extract_charts(doc, book)

    lessons: list[dict] = []
    for lesson_id in sorted(lesson_lines.keys()):
        lines = lesson_lines[lesson_id]
        raw_blocks = parse_page_blocks(
            lines, decrypt_qa_part, is_question, clean_text
        )
        blocks = [
            finalize_block(rb, idx, vocab_map)
            for idx, rb in enumerate(raw_blocks, start=1)
        ]
        # 扁平汇总（兼容统计）
        all_vocab = [v for b in blocks for v in b["vocabulary"]]
        all_drills = [d for b in blocks for d in b["drills"]]

        lessons.append({
            "lessonId": lesson_id,
            "title": f"Lesson {lesson_id}",
            "blocks": blocks,
            "blockCount": len(blocks),
            "vocabulary": all_vocab,
            "drills": all_drills,
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "book": book,
        "chartManifest": chart_manifest,
        "lessons": lessons,
    }
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    doc.close()
    return len(lessons)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Callan Method PDF to JSON")
    parser.add_argument("--book", type=int, help="Book number 1-12")
    parser.add_argument("--all", action="store_true", help="Extract all 12 books")
    args = parser.parse_args()

    books = range(1, 13) if args.all else [args.book or 1]

    for book in books:
        if not 1 <= book <= 12:
            raise SystemExit("book must be 1-12")
        pdf_path = RAW_DIR / f"book-{book:02d}.pdf"
        if not pdf_path.exists():
            print(f"Book {book}: SKIP (no PDF)")
            continue
        out_path = OUT_DIR / f"book-{book:02d}.json"
        count = parse_pdf(pdf_path, out_path)
        print(f"Book {book}: extracted {count} lessons → {out_path}")


if __name__ == "__main__":
    main()
