"""按 Callan 教材原结构解析：词块 + 对练问答 + Chart 引用。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from drill_repair import repair_drills

CHART_RE = re.compile(r"see\s+chart\s+(\d+)", re.I)
SECTION_NO_RE = re.compile(r"^\d{1,2}$")
VOCAB_PIPE_RE = re.compile(r"\|")
INTRO_RE = re.compile(r"^[A-Z][A-Za-z ,()'\-]{10,}\.\s*$")
SKIP_WORDS = {
    "see chart", "revision exercise", "plural", "etc.", "contraction",
    "index", "yes", "no",
}


@dataclass
class RawBlock:
    section_no: int | None = None
    chart_ref: int | None = None
    intro: str = ""
    vocabulary: list[str] = field(default_factory=list)
    grammar: list[str] = field(default_factory=list)
    drills_raw: list[dict] = field(default_factory=list)


def is_encrypted_line(line: str) -> bool:
    has_ctrl = any(0 < ord(c) < 32 and c not in "\r\n\t" for c in line)
    has_lower = any(97 <= ord(c) <= 122 for c in line)
    return (has_ctrl or "*" in line) and not has_lower


def _is_lesson_header(line: str) -> bool:
    return bool(re.match(r"^LESSON\s+\d+\s*$", line.strip(), re.I))


def _chart_no(line: str) -> int | None:
    m = CHART_RE.search(line)
    return int(m.group(1)) if m else None


def _is_vocab_token(line: str) -> bool:
    s = line.strip()
    if not s or len(s) > 35:
        return False
    if "?" in s or is_encrypted_line(s):
        return False
    if SECTION_NO_RE.match(s):
        return False
    if _chart_no(s) is not None:
        return False
    if s.lower() in SKIP_WORDS:
        return False
    if INTRO_RE.match(s):
        return False
    if re.match(r"^(Yes|No),", s, re.I):
        return False
    if VOCAB_PIPE_RE.search(s):
        return True
    # 单词/短语行（PDF 常拆成逐行）
    if len(s.split()) <= 4 and re.match(r"^[\w'(),\-.\s]+$", s):
        if re.search(r"[a-zA-Z]", s):
            return True
    return False


def _split_vocab_tokens(line: str) -> list[str]:
    if "|" in line:
        return [p.strip() for p in line.split("|") if p.strip()]
    return [line.strip()]


def _is_intro(line: str) -> bool:
    s = line.strip()
    if "?" in s or is_encrypted_line(s) or _chart_no(s):
        return False
    return bool(INTRO_RE.match(s))


def _looks_like_question(line: str, is_question_fn) -> bool:
    s = line.strip()
    if is_question_fn(s):
        return True
    if s.endswith("?"):
        return True
    if is_encrypted_line(s):
        return True
    if s.lower() in {"is this?"}:
        return True
    return False


def _looks_like_answer(line: str, is_question_fn) -> bool:
    s = line.strip()
    if not s or _looks_like_question(s, is_question_fn):
        return False
    if is_encrypted_line(s):
        return False
    if _is_vocab_token(s) and not s[0].isupper():
        return False
    return True


def parse_page_blocks(
    page_lines: list[str],
    decrypt_qa_part,
    is_question,
    clean_text,
) -> list[RawBlock]:
    blocks: list[RawBlock] = []
    current: RawBlock | None = None
    pending_q: str | None = None
    pending_enc_parts: list[str] = []

    def flush():
        nonlocal current, pending_q, pending_enc_parts
        if pending_q and current:
            current.drills_raw.append({"question": pending_q, "answer": ""})
        pending_q = None
        pending_enc_parts = []
        if current and (current.vocabulary or current.grammar or current.drills_raw or current.intro):
            blocks.append(current)
        current = None

    def ensure():
        nonlocal current
        if current is None:
            current = RawBlock()

    def add_drill(q: str, a: str):
        ensure()
        q = clean_text(q)
        a = clean_text(a)
        if q and not q.endswith("?"):
            q = q.rstrip(".") + "?"
        if q:
            current.drills_raw.append({"question": q, "answer": a})

    for raw in page_lines:
        line = raw.strip()
        if not line or _is_lesson_header(line):
            continue

        chart = _chart_no(line)
        if chart is not None:
            ensure()
            current.chart_ref = chart
            continue

        if "|" in line and "?" in line.split("|")[0]:
            parts = line.split("|", 1)
            add_drill(decrypt_qa_part(parts[0]), decrypt_qa_part(parts[1]))
            continue

        if SECTION_NO_RE.match(line):
            n = int(line)
            if current and current.drills_raw:
                flush()
            ensure()
            if current.section_no is None:
                current.section_no = n
            else:
                flush()
                current = RawBlock(section_no=n)
            continue

        if _is_intro(line):
            ensure()
            current.intro = clean_text(line)
            continue

        if _looks_like_question(line, is_question):
            q = clean_text(decrypt_qa_part(line))
            if pending_q:
                add_drill(pending_q, "")
            pending_q = q
            pending_enc_parts = []
            continue

        if pending_q and (_looks_like_answer(line, is_question) or is_encrypted_line(line)):
            if is_encrypted_line(line):
                pending_enc_parts.append(line)
                a = clean_text(decrypt_qa_part(" ".join(pending_enc_parts)))
                if a and not _looks_like_question(a, is_question):
                    add_drill(pending_q, a)
                    pending_q = None
                    pending_enc_parts = []
                continue
            add_drill(pending_q, decrypt_qa_part(line))
            pending_q = None
            pending_enc_parts = []
            continue

        if _is_vocab_token(line):
            tokens = _split_vocab_tokens(line)
            if current and current.drills_raw:
                flush()
                current = RawBlock()
            ensure()
            for tok in tokens:
                if "(" in tok and ")" in tok:
                    current.grammar.append(tok)
                else:
                    current.vocabulary.append(tok)
            continue

    flush()
    return blocks


def assign_focus_words(block: RawBlock) -> list[str]:
    focus: list[str] = []
    for w in block.vocabulary + block.grammar:
        core = re.sub(r"\(.*?\)", "", w).strip()
        for token in re.findall(r"[a-zA-Z']+", core):
            t = token.lower()
            if len(t) > 1 and t not in {"the", "and", "etc"}:
                focus.append(t)
    return list(dict.fromkeys(focus))


def tag_drill_focus(drill: dict, focus_words: list[str]) -> dict:
    text = (drill.get("question", "") + " " + drill.get("answer", "")).lower()
    matched = [w for w in focus_words if re.search(rf"\b{re.escape(w)}\b", text)]
    drill = dict(drill)
    drill["focusWords"] = matched
    return drill


def finalize_block(block: RawBlock, block_index: int, vocab_map: dict[str, str]) -> dict:
    focus = assign_focus_words(block)
    vocab_items = []
    seen: set[str] = set()
    for w in block.vocabulary + block.grammar:
        key = w.lower()
        if key in seen:
            continue
        seen.add(key)
        lookup = re.sub(r"\(.*?\)", "", w).strip().upper()
        zh = vocab_map.get(lookup, "")
        if not zh and lookup.endswith("S"):
            zh = vocab_map.get(lookup[:-1], "")
        vocab_items.append({"word": w.strip(), "meaningZh": zh, "example": ""})

    raw_vocab = [{"word": v["word"], "meaningZh": v["meaningZh"]} for v in vocab_items]
    drills = repair_drills(block.drills_raw, raw_vocab)
    drills = [tag_drill_focus(d, focus) for d in drills]

    return {
        "blockId": block_index,
        "sectionNo": block.section_no,
        "chartRef": block.chart_ref,
        "chartHint": f"See Chart {block.chart_ref}" if block.chart_ref else None,
        "intro": block.intro,
        "focusWords": focus,
        "vocabulary": vocab_items,
        "drills": drills,
    }
