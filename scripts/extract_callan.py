#!/usr/bin/env python3
"""从 Callan Method PDF 提取 Lesson / 词汇 / 问答对（Book 1 逻辑已验证）。"""

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
        "How many", "What's", "Is", "Where", "What",
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
    last_word = words[-1]
    incomplete = {
        "the", "a", "an", "of", "in", "under", "behind", "front", "on", "at", "to", "from",
        "isn't", "aren't", "is", "are", "am", "was", "were", "will", "would", "should",
        "could", "have", "has", "had", "do", "does", "did", "with", "about", "by", "for",
        "first", "second", "third", "fourth", "fifth", "last",
        "you're", "he's", "she's", "it's", "we're", "they're", "i'm",
        "you're", "he's", "she's", "it's", "we're", "they're", "i'm",
    }
    return last_word in incomplete


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


def parse_pdf(pdf_path: Path, output_path: Path) -> int:
    doc = fitz.open(pdf_path)

    vocab_map: dict[str, str] = {}
    for page_num in range(59, 64):
        text = doc[page_num].get_text("text")
        for line in text.split("\n"):
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
            zh_dec = decrypt_vocab_zh(line_str)
            zh_final = "".join(
                c for c in zh_dec if 0x4E00 <= ord(c) <= 0x9FFF
            ).strip()
            if eng_final and zh_final:
                vocab_map[eng_final.upper()] = zh_final

    lessons = []
    current_lesson = None

    for page_num in range(12, 43):
        blocks = doc[page_num].get_text("blocks")
        blocks = sorted(blocks, key=lambda b: (round(b[1] / 10), b[0]))

        for b in blocks:
            text = b[4].strip()
            if not text:
                continue
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if not lines:
                continue

            header_match = re.search(r"LESSON\s+(\d+)", lines[0].upper())
            if header_match:
                lesson_id = int(header_match.group(1))
                if 1 <= lesson_id <= 9:
                    current_lesson = {
                        "lessonId": lesson_id,
                        "title": f"Lesson {lesson_id}",
                        "vocabulary": [],
                        "drills": [],
                    }
                    lessons.append(current_lesson)
                continue

            if not current_lesson:
                continue

            if len(lines) == 1 and lines[0].isdigit():
                continue
            upper = text.upper()
            if "SEE CHART" in upper or "REVISION EXERCISE" in upper:
                continue

            if is_question(lines[0]):
                q_parts, a_parts = [], []
                in_q = True
                for line in lines:
                    if in_q:
                        if is_question(line):
                            q_parts.append(line)
                        else:
                            in_q = False
                            a_parts.append(line)
                    else:
                        a_parts.append(line)

                decrypted_q = [decrypt_qa_part(p) for p in q_parts]
                q_text = (
                    ")".join(decrypted_q)
                    if any(is_encrypted_line(p) for p in q_parts)
                    else " ".join(decrypted_q)
                )
                q_text = clean_text(q_text).rstrip(") ?").strip() + "?"

                decrypted_a = [decrypt_qa_part(p) for p in a_parts]
                ans_text = clean_text(" ".join(decrypted_a))
                if q_text and ans_text:
                    current_lesson["drills"].append(
                        {"question": q_text, "answer": ans_text}
                    )
            else:
                cleaned_block_text = clean_text(text)
                if current_lesson["drills"] and can_be_continued(
                    current_lesson["drills"][-1]["answer"]
                ):
                    prev = current_lesson["drills"][-1]["answer"]
                    current_lesson["drills"][-1]["answer"] = clean_text(
                        prev + " " + cleaned_block_text
                    )
                else:
                    for line in lines:
                        word = clean_text(line)
                        word_clean = re.sub(r"[^a-zA-Z'-]", " ", word).strip()
                        word_clean = re.sub(r"\s+", " ", word_clean)
                        if (
                            not word_clean
                            or len(word_clean) < 2
                            or word_clean.lower()
                            in {"see chart", "revision exercise", "contraction", "plural", "etc."}
                        ):
                            continue
                        word_upper = word_clean.upper()
                        zh_trans = vocab_map.get(word_upper, "")
                        if not zh_trans and word_upper.endswith("S"):
                            zh_trans = vocab_map.get(word_upper[:-1], "")
                        current_lesson["vocabulary"].append(
                            {"word": format_vocab_word(word_clean), "meaningZh": zh_trans}
                        )

    for lesson in lessons:
        seen_vocab: set[str] = set()
        unique_vocab = []
        for v in lesson["vocabulary"]:
            w = v["word"].upper()
            if w not in seen_vocab:
                seen_vocab.add(w)
                unique_vocab.append(v)
        lesson["vocabulary"] = unique_vocab

        seen_drills: set[tuple[str, str]] = set()
        unique_drills = []
        for d in lesson["drills"]:
            k = (d["question"].upper(), d["answer"].upper())
            if k not in seen_drills:
                seen_drills.add(k)
                unique_drills.append(d)
        lesson["drills"] = unique_drills

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(lessons, f, ensure_ascii=False, indent=2)

    doc.close()
    return len(lessons)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Callan Method PDF to JSON")
    parser.add_argument("--book", type=int, default=1, help="Book number 1-12")
    args = parser.parse_args()

    if not 1 <= args.book <= 12:
        raise SystemExit("book must be 1-12")

    pdf_path = RAW_DIR / f"book-{args.book:02d}.pdf"
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    out_path = OUT_DIR / f"book-{args.book:02d}.json"
    count = parse_pdf(pdf_path, out_path)
    print(f"Book {args.book}: extracted {count} lessons → {out_path}")


if __name__ == "__main__":
    main()
