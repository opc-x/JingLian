"""修复提取后的问答：省略号、多答案合并、残缺句补全。"""

from __future__ import annotations

import re
from collections import defaultdict

ELLIPSIS = re.compile(r"\.{3}|…")
TRAILING_JUNK = re.compile(
    r"\s+(men women say|name|my your|action|assassinate)$", re.IGNORECASE
)

# 常见骨架答法补全
GENERIC_ANSWER_FILLS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^Yes, I think \.\.\.$", re.I), "Yes, I think so"),
    (re.compile(r"^No, I don’t think \.\.\.$", re.I), "No, I don’t think so"),
    (re.compile(r"^No, I don't think \.\.\.$", re.I), "No, I don't think so"),
    (re.compile(r"^Yes, I believe \.\.\.$", re.I), "Yes, I believe so"),
    (re.compile(r"^No, I don’t believe \.\.\.$", re.I), "No, I don’t believe so"),
    (re.compile(r"^Yes, I usually \.\.\.$", re.I), "Yes, I usually do"),
    (re.compile(r"^No, I don’t usually \.\.\.$", re.I), "No, I don’t usually"),
    (re.compile(r"^Yes, I generally \.\.\.$", re.I), "Yes, I generally do"),
    (re.compile(r"^No, I don’t generally \.\.\.$", re.I), "No, I don’t generally"),
    (re.compile(r"^Yes, I’d like \.\.\.$", re.I), "Yes, I’d like to"),
    (re.compile(r"^No, I wouldn’t like \.\.\.$", re.I), "No, I wouldn’t like to"),
    (re.compile(r"^Yes, I notice something different \.\.\.$", re.I), "Yes, I notice something different today"),
    (re.compile(r"^The plural of \.\.\.$", re.I), "The plural of “life” is “lives”"),
    (re.compile(r"^We translate .+ with \.\.\.$", re.I), None),  # handled separately
    (re.compile(r"standing \.\.\.; it’s lying \.\.\.$", re.I), "standing up; it’s lying down"),
    (re.compile(r"isn't standing \.\.\.; it's lying \.\.\.$", re.I), "isn't standing up; it's lying down"),
]


def _has_ellipsis(text: str) -> bool:
    return bool(ELLIPSIS.search(text))


def _clean(text: str) -> str:
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("'", "'").replace("'", "'").replace(""", '"').replace(""", '"')
    return re.sub(r"\s+", " ", text.strip())


def _strip_junk(answer: str) -> str:
    return TRAILING_JUNK.sub("", _clean(answer))


def _split_answer_variants(answer: str) -> list[str]:
    """Callan 常用 ~ 分隔正反答法。"""
    parts = re.split(r"\s*~\s*", answer)
    return [_strip_junk(p) for p in parts if _strip_junk(p)]


def _extract_names(text: str) -> list[tuple[str, str]]:
    return re.findall(r"\b(Mr|Mrs|Ms|Miss)\s+([A-Z][a-z]+)\b", text)


def _extract_numbers_from_lesson(lesson_drills: list[dict]) -> list[str]:
    nums = []
    for d in lesson_drills:
        for m in re.findall(
            r"\b(\d+|twenty|thirty|forty|fifty|hundred|thousand)\b",
            d.get("answer", ""),
            re.I,
        ):
            nums.append(m)
    return nums


def _fill_from_question_options(question: str, answer: str) -> str | None:
    if not _has_ellipsis(answer):
        return None
    m = re.search(
        r"(?:on the |on a )?(\w[\w\s-]*?)\s+or\s+(?:on the |on a )?(\w[\w\s-]*?)(?:\?|$)",
        question,
        re.I,
    )
    if m:
        opt2 = m.group(2).strip().rstrip("?")
        return ELLIPSIS.sub(opt2.split()[0] if opt2 else "online", answer, count=1)
    return None


def _fill_translate_pattern(question: str, answer: str) -> str | None:
    m = re.search(r'translate [“"](.+?)[”"]', question, re.I)
    if not m or not _has_ellipsis(answer):
        return None
    phrase = m.group(1)
    # 常见 Callan 翻译套路
    if "must" in phrase:
        return answer.replace("...", "must + infinitive")
    if "should" in phrase:
        return answer.replace("...", "should + infinitive")
    if "had better" in phrase.lower():
        return answer.replace("...", "had better + infinitive")
    return answer.replace("...", f"「{phrase}」的对应表达")


def _fill_i_think_pattern(answer: str) -> str | None:
    if not _has_ellipsis(answer):
        return None
    if re.search(r"I think \.\.\. is", answer, re.I):
        return ELLIPSIS.sub("London", answer, count=1)
    if re.search(r"you'll still be \.\.\.", answer, re.I):
        return ELLIPSIS.sub("here", answer, count=1)
    if re.search(r"there's a \.\.\.", answer, re.I):
        return ELLIPSIS.sub("restaurant", answer, count=1)
    if re.search(r"there isn't a \.\.\.", answer, re.I):
        return ELLIPSIS.sub("restaurant", answer, count=1)
    if re.search(r"we're having \.\.\.", answer, re.I):
        return ELLIPSIS.sub("calm weather", answer, count=1)
    if re.search(r"we aren't having \.\.\.", answer, re.I):
        return ELLIPSIS.sub("stormy weather", answer, count=1)
    if re.search(r"it’s still \.\.\.", answer, re.I) or re.search(r"it's still \.\.\.", answer, re.I):
        return ELLIPSIS.sub("winter", answer, count=1)
    if re.search(r"I've sometimes woken up \.\.\.", answer, re.I):
        return ELLIPSIS.sub("too late", answer, count=1)
    if re.search(r"I've never woken up \.\.\.", answer, re.I):
        return ELLIPSIS.sub("too late", answer, count=1)
    if re.search(r"I've broken one/some of \.\.\.", answer, re.I):
        return ELLIPSIS.sub("the bones in my body", answer, count=1)
    if re.search(r"further than you can", answer, re.I) and _has_ellipsis(answer):
        return ELLIPSIS.sub("throw a stone", answer, count=1)
    return None


def _apply_generic_fills(answer: str) -> str:
    for pat, repl in GENERIC_ANSWER_FILLS:
        if repl and pat.search(answer):
            return repl
    return answer


def _fill_all_ellipsis(question: str, answer: str) -> str:
    a = answer
    for fn in (
        lambda: _fill_from_question_options(question, a),
        lambda: _fill_translate_pattern(question, a),
        lambda: _fill_i_think_pattern(a),
    ):
        result = fn()
        if result:
            a = result
    a = _apply_generic_fills(a)
    # 剩余省略号：用 so / do / 从问句摘词
    if _has_ellipsis(a):
        if a.rstrip().endswith("..."):
            if "prefer" in a.lower():
                a = ELLIPSIS.sub("online", a, count=1)
            elif re.search(r"(usually|generally|often) \.\.\.$", a, re.I):
                a = ELLIPSIS.sub("do", a, count=1)
            elif "think" in a.lower() or "believe" in a.lower():
                a = ELLIPSIS.sub("so", a, count=1)
            elif "like" in a.lower():
                a = ELLIPSIS.sub("to", a, count=1)
            else:
                a = ELLIPSIS.sub("", a).rstrip()
        else:
            a = ELLIPSIS.sub("…", a)
            a = a.replace("…", "").strip()
    return _clean(a)


def _is_pure_template(q: str, a: str) -> bool:
    q, a = _clean(q), _clean(a)
    q_core = ELLIPSIS.sub("", q).strip(" ?")
    a_core = ELLIPSIS.sub("", a).strip(" .;")
    if re.match(r"^(Am I|Are you|Is he|Is she)(\s*\.\.\.)?\s*$", q, re.I):
        if re.match(r"^Yes, (you|I|he|she)['']?re(\s*\.\.\.)?\s*\.?$", a, re.I):
            return True
    if _has_ellipsis(q) and _has_ellipsis(a):
        if re.match(r"^(Am I|Are you|Is he|Is she)\s*$", q_core, re.I):
            return bool(re.match(r"^Yes, (you|I|he|she)['']?re\s*$", a_core, re.I))
    return False


def _complete_negation_identity(q: str, a: str, names: list[tuple[str, str]]) -> str | None:
    m = re.match(r"^Am I (Mr|Mrs|Ms) (\w+)\?$", q, re.I)
    if not m or not _has_ellipsis(a):
        return None
    title, name = m.group(1), m.group(2)
    other_title = "Mrs" if title.lower() == "mr" else "Mr"
    for t, n in names:
        if n == name and t != title:
            other_title = t
            break
    return f"No, you aren't {title} {name}; you're {other_title} {name}"


def _complete_are_you_identity(q: str, a: str, names: list[tuple[str, str]]) -> str | None:
    m = re.match(r"^Are you (Mr|Mrs|Ms) (\w+)\?$", q, re.I)
    if not m or not _has_ellipsis(a):
        return None
    title, name = m.group(1), m.group(2)
    for t, n in names:
        if n != name:
            return f"No, I'm not {title} {name}; I'm {t} {n}"
    other = "Mrs" if title.lower() == "mr" else "Mr"
    return f"No, I'm not {title} {name}; I'm {other} {name}"


def _complete_am_i_in_front(q: str, a: str) -> str | None:
    if q == "Am I in front of him?" and a.rstrip().endswith("you're"):
        return "No, you aren't in front of him; you're behind him"
    return None


def _complete_there_are(q: str, a: str, numbers: list[str]) -> str | None:
    if not _has_ellipsis(a):
        return None
    if "there are" not in a.lower() and "there are" not in q.lower():
        return None
    num = numbers[0] if numbers else "many"
    return ELLIPSIS.sub(str(num), a, count=1)


def _complete_name_drill(q: str, a: str) -> str | None:
    if re.match(r"^What's your name\?$", q, re.I) and _has_ellipsis(a):
        return "Your name's Anna"
    if re.match(r"^What's my name\?$", q, re.I) and _has_ellipsis(a):
        return "My name's Mr Brown"
    return None


def _complete_meaning_drill(q: str, a: str, vocab: list[dict]) -> str | None:
    m = re.search(r'meaning of (?:the )?(?:word )?["\u201c]?(\w+)', q, re.I)
    if not m or not _has_ellipsis(q):
        return None
    word = m.group(1).lower()
    for v in vocab:
        if v.get("word", "").lower().startswith(word):
            zh = v.get("meaningZh") or v.get("word")
            return f'The meaning of the word "{word}" is "{zh}"'
    return f'The meaning of the word "{word}" is "(see vocabulary)"'


def _complete_table_chairs(q: str, a: str) -> str | None:
    if "chairs are" in a.lower() and _has_ellipsis(a):
        return "Those chairs are black" if "those" in q.lower() else "These chairs are white"
    if "table" in q.lower() and _has_ellipsis(a):
        return ELLIPSIS.sub("on the floor", a, count=1)
    return None


def _complete_or_choice(q: str, a: str) -> str | None:
    """Is the table long or short? → The table's long"""
    if not _has_ellipsis(a):
        return None
    m = re.search(r"\b(long|short|large|small|high|low)\s+or\s+(long|short|large|small|high|low)\b", q, re.I)
    if m:
        chosen = m.group(1).lower()
        if "table" in q.lower():
            return f"The table's {chosen}"
        if "city" in q.lower():
            return f"A city's {chosen}"
        if "table's" in a.lower() or "table" in a.lower():
            return ELLIPSIS.sub(chosen, a, count=1)
    return None


def _repair_one_answer(
    q: str, a: str, vocab: list[dict], all_drills: list[dict]
) -> str | None:
    q = _clean(q)
    a = _strip_junk(a)
    if _is_pure_template(q, a):
        return None

    names: list[tuple[str, str]] = []
    for d in all_drills:
        names.extend(_extract_names(d.get("question", "")))
        names.extend(_extract_names(d.get("answer", "")))
    numbers = _extract_numbers_from_lesson(all_drills)

    completed = (
        _complete_negation_identity(q, a, names)
        or _complete_are_you_identity(q, a, names)
        or _complete_am_i_in_front(q, a)
        or _complete_there_are(q, a, numbers)
        or _complete_name_drill(q, a)
        or _complete_meaning_drill(q, a, vocab)
        or _complete_or_choice(q, a)
        or _complete_table_chairs(q, a)
    )
    if completed:
        a = completed
    elif _has_ellipsis(a) or _has_ellipsis(q):
        a = _fill_all_ellipsis(q, a)
        if _has_ellipsis(q):
            q = _fill_all_ellipsis("", q)

    if _has_ellipsis(a) or _has_ellipsis(q):
        return None
    if len(a) < 5:
        return None
    # 残缺缩写尾：Yes, you're / Yes, I'm
    if re.search(r"\b(you're|I'm|he's|she's|we're|they're)\s*$", a, re.I):
        return None
    if re.match(r"^(Am I|Are you|Is he|Is she)\s*(\.\.\.)?\s*\?$", q, re.I) and "..." in q:
        return None
    return a


def repair_drills(raw_drills: list[dict], vocab: list[dict]) -> list[dict]:
    repaired: list[tuple[str, str]] = []

    for item in raw_drills:
        q0 = item.get("question", "")
        a0 = item.get("answer", "")
        if not q0 or not a0:
            continue
        q = _clean(q0)
        if not q.endswith("?"):
            q = q.rstrip(".") + "?"

        for variant in _split_answer_variants(a0):
            fixed_a = _repair_one_answer(q, variant, vocab, raw_drills)
            if fixed_a:
                repaired.append((q, fixed_a))

    grouped: dict[str, list[str]] = defaultdict(list)
    order: list[str] = []
    for q, a in repaired:
        key = q.lower()
        if key not in grouped:
            order.append(key)
        if a not in grouped[key]:
            grouped[key].append(a)

    out: list[dict] = []
    for key in order:
        answers = grouped[key]
        q_display = next(q for q, _ in repaired if q.lower() == key)
        tip = ""
        if len(answers) > 1:
            tip = f"共 {len(answers)} 种答法（教材变体）"
        elif "isn't" in answers[0].lower() or "not" in answers[0].lower():
            tip = "否定回答：先 No，再纠正"

        entry: dict = {"question": q_display, "answer": answers[0], "tip": tip}
        if len(answers) > 1:
            entry["answers"] = answers
        out.append(entry)

    return out
