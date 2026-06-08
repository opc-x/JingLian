#!/usr/bin/env python3
"""从批注 JSON 提取词汇，用 edge-tts 生成英式发音 MP3。"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANN_DIR = ROOT / "annotations" / "callan"
AUDIO_DIR = ROOT / "jingyu" / "public" / "audio"


def slug(word: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", word.lower()).strip("-")
    return s[:60] or "word"


def collect_words(book: int) -> set[str]:
    p = ANN_DIR / f"book-{book:02d}.json"
    if not p.exists():
        return set()
    data = json.loads(p.read_text(encoding="utf-8"))
    words: set[str] = set()
    for ann in data.get("annotations", []):
        for v in ann.get("blocks", {}).get("vocab", []):
            w = v.get("word", "").strip()
            if w:
                words.add(w)
    return words


async def gen_one(word: str, out: Path) -> None:
    import edge_tts

    if out.exists():
        return
    comm = edge_tts.Communicate(word, "en-GB-SoniaNeural")
    await comm.save(str(out))


async def run(book: int) -> int:
    words = collect_words(book)
    out_dir = AUDIO_DIR / f"book-{book:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for w in sorted(words):
        path = out_dir / f"{slug(w)}.mp3"
        if path.exists():
            continue
        await gen_one(w, path)
        n += 1
        print(f"  {w} → {path.name}")
    return n


def patch_audio_paths(book: int) -> None:
    p = ANN_DIR / f"book-{book:02d}.json"
    if not p.exists():
        return
    data = json.loads(p.read_text(encoding="utf-8"))
    prefix = f"audio/book-{book:02d}"
    changed = False
    for ann in data.get("annotations", []):
        for v in ann.get("blocks", {}).get("vocab", []):
            w = v.get("word", "")
            if w and not v.get("audio"):
                v["audio"] = f"{prefix}/{slug(w)}.mp3"
                changed = True
    if changed:
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", type=int, required=True)
    args = parser.parse_args()
    n = asyncio.run(run(args.book))
    patch_audio_paths(args.book)
    print(f"Generated {n} new audio files")


if __name__ == "__main__":
    main()
