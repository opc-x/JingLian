#!/usr/bin/env python3
"""
基于页图 + 原文行，用 Vision 模型生成结构化批注（词汇/句型/语法/用法）。
写入 annotations/callan/book-XX.json，不修改教材正文。
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAITHFUL_DIR = ROOT / "sources" / "callan" / "faithful"
PAGES_DIR = ROOT / "sources" / "callan" / "pages"
ANN_DIR = ROOT / "annotations" / "callan"

SCHEMA_HINT = """{
  "summaryZh": "本页通过哪些问答句练哪些词（一句话）",
  "chartRef": null,
  "blocks": {
    "patterns": [{
      "en": "Is the … long?",
      "zh": "……长吗？",
      "why": "为什么用一般疑问句+否定纠正：Callan 用问答固化形容词对比",
      "when": "比较两个性质、纠正对方预设时用",
      "how": "老师问 Is the pen long? 学生答 No, the pen isn't long; it's short。先否定再给出正确项",
      "drills": ["Is the table small?", "No, the table isn't small; it's large."],
      "realLife": "购物时说 Is this too large? 拒绝错误理解后给出正确尺寸"
    }],
    "vocab": [{
      "word": "city", "ipa": "/ˈsɪti/", "pos": "n.", "zh": "城市",
      "inDrill": "Is London a city? — No, London isn't a village; it's a city."
    }],
    "grammar": [{"title": "标题", "body": "简明"}],
    "usage": [{"title": "离开教材后", "body": "真实场景怎么开口"}]
  }
}"""


def load_faithful(book: int) -> dict:
    p = FAITHFUL_DIR / f"book-{book:02d}.json"
    return json.loads(p.read_text(encoding="utf-8"))


def load_annotations(book: int) -> dict:
    p = ANN_DIR / f"book-{book:02d}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"book": book, "annotations": []}


def save_annotations(book: int, data: dict) -> None:
    ANN_DIR.mkdir(parents=True, exist_ok=True)
    (ANN_DIR / f"book-{book:02d}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def page_context_lines(page: dict, max_lines: int = 80) -> str:
    lines = []
    for ln in page.get("lines", [])[:max_lines]:
        t = ln.get("text", "").strip()
        if not t or t in {" ", "\x01"} or len(t) == 1 and t.isdigit():
            continue
        t = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", t)
        if t:
            lines.append(t)
    return "\n".join(lines)


def image_to_b64(image_rel: str) -> str:
    path = ROOT / "sources" / "callan" / image_rel
    if not path.exists():
        raise FileNotFoundError(path)
    return base64.standard_b64encode(path.read_bytes()).decode()


def call_vision(
    image_b64: str,
    context: str,
    book: int,
    lesson_id: int,
    page_num: int,
    cefr: str,
) -> dict:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("需要 OPENAI_API_KEY 环境变量")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    model = os.environ.get("ANNOTATE_MODEL", "gpt-4o-mini")

    prompt = f"""分析这页 Callan Method 教材（Book {book} Lesson {lesson_id} PDF p.{page_num}，CEFR {cefr}）。

下方是从 PDF 提取的原文行（辅助，以截图为准）：
---
{context[:4000]}
---

Callan Method 教学法：词不是孤立背的，而是通过本页问答句反复练会。批注目标是学完能在真实场景开口用。

请生成中文学习批注 JSON，结构严格如下：
{SCHEMA_HINT}

要求（重要）：
- patterns（核心）：本页每个主要问答案型必须含 why / when / how 三个字段，用中文写清楚：
  · why：为什么教材用这个句型（教学意图）
  · when：什么情况下用（触发场景）
  · how：怎么问、怎么答（含 Callan 先否定再纠正的节奏）
  · drills：从本页教材摘 1-3 组真实问答
  · realLife：离开课堂后的真实用法一句
- vocab：每条必须有 inDrill，标明这个词在本页哪句问答里练到；含 IPA
- grammar：1-2 条，支撑上述句型
- usage：标题侧重「实战」，写真实生活怎么开口
- chartRef：若页上有 See Chart N 则填数字，否则 null
- 只输出 JSON 对象，不要 markdown"""

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}", "detail": "high"},
                    },
                ],
            }
        ],
        response_format={"type": "json_object"},
        max_tokens=2800,
    )
    raw = resp.choices[0].message.content or "{}"
    return json.loads(raw)


def merge_page_ann(
    data: dict, lesson_id: int, page_num: int, payload: dict, model: str
) -> None:
    anns = data.setdefault("annotations", [])
    entry = {
        "lessonId": lesson_id,
        "pageNum": page_num,
        "summaryZh": payload.get("summaryZh", ""),
        "chartRef": payload.get("chartRef"),
        "blocks": payload.get("blocks", {}),
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "model": model,
    }
    for i, a in enumerate(anns):
        if a.get("lessonId") == lesson_id and a.get("pageNum") == page_num:
            anns[i] = {**a, **entry}
            return
    anns.append(entry)


def annotate_book(
    book: int,
    lesson_filter: int | None = None,
    page_filter: int | None = None,
    force: bool = False,
) -> int:
    faithful = load_faithful(book)
    ann_data = load_annotations(book)
    cefr = faithful.get("cefr", "A1")
    model = os.environ.get("ANNOTATE_MODEL", "gpt-4o-mini")
    count = 0

    for lesson in faithful.get("lessons", []):
        lid = lesson["lessonId"]
        if lesson_filter and lid != lesson_filter:
            continue
        for page in lesson.get("pages", []):
            pnum = page["pageNum"]
            if page_filter and pnum != page_filter:
                continue

            if not force:
                existing = next(
                    (
                        a
                        for a in ann_data.get("annotations", [])
                        if a.get("lessonId") == lid
                        and a.get("pageNum") == pnum
                        and a.get("blocks", {}).get("patterns")
                        and (a.get("blocks", {}).get("patterns") or [{}])[0].get("why")
                    ),
                    None,
                )
                if existing:
                    print(f"  skip Book {book} L{lid} p.{pnum} (已有批注)")
                    continue

            print(f"  annotating Book {book} L{lid} p.{pnum}…")
            ctx = page_context_lines(page)
            b64 = image_to_b64(page["image"])
            try:
                payload = call_vision(b64, ctx, book, lid, pnum, cefr)
            except Exception as e:
                print(f"    ERROR: {e}")
                continue
            merge_page_ann(ann_data, lid, pnum, payload, model)
            count += 1

    save_annotations(book, ann_data)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Vision 批注生成")
    parser.add_argument("--book", type=int, required=True)
    parser.add_argument("--lesson", type=int)
    parser.add_argument("--page", type=int)
    parser.add_argument("--all-lessons", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.all_lessons:
        n = annotate_book(args.book, force=args.force)
    else:
        n = annotate_book(
            args.book,
            lesson_filter=args.lesson,
            page_filter=args.page,
            force=args.force,
        )
    print(f"Done: {n} pages annotated → {ANN_DIR / f'book-{args.book:02d}.json'}")


if __name__ == "__main__":
    main()
