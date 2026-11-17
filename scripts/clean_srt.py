"""srt → プレーンテキスト。タイムコード・番号・タグ・重複行を除去する。"""
import re
import sys
from pathlib import Path

TIME = re.compile(r"^\d{1,2}:\d{2}:\d{2}[,.]\d{3}\s*-->")
TAG = re.compile(r"<[^>]+>|\{[^}]*\}")


def clean_srt(text: str) -> str:
    lines = []
    for raw in text.replace("﻿", "").splitlines():
        line = TAG.sub("", raw).strip()
        if not line or line.isdigit() or TIME.match(line):
            continue
        if lines and line in lines[-1]:
            continue  # 自動字幕のローリング重複: 同一行、または前行に含まれる行は捨てる
        if lines and line.startswith(lines[-1]):
            lines[-1] = line  # 前行を含んで伸びた行は置換
            continue
        lines.append(line)
    return "\n".join(lines) + ("\n" if lines else "")


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: clean_srt.py <in.srt> <out.txt>", file=sys.stderr)
        return 2
    out = clean_srt(Path(sys.argv[1]).read_text(encoding="utf-8"))
    Path(sys.argv[2]).write_text(out, encoding="utf-8")
    return 0 if out.strip() else 1


if __name__ == "__main__":
    sys.exit(main())
