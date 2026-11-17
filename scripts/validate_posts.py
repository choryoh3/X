"""検証センサー。終了コード 0=合格 / 1=不合格。理由は1行ずつ標準出力へ（LLMへそのまま返せる形）。"""
import difflib
import re
import sys
from pathlib import Path

from common import load_config, root

ANGLES = ["共感型", "学び型", "気づき型", "刺さる一言型", "問いかけ型"]
HEADING = re.compile(r"^##\s*(\d+)\.\s*(.+?)\s*$")
LIMITS = {"weighted": 280, "simple": 140}
SIMILARITY = 0.8


def _weight(ch: str) -> int:
    """Xの重み付け: Latin等(U+0000-10FF, 2000-200D, 2010-201F, 2032-2037)=1、他=2。"""
    c = ord(ch)
    return 1 if (c <= 0x10FF or 0x2000 <= c <= 0x200D or 0x2010 <= c <= 0x201F or 0x2032 <= c <= 0x2037) else 2


def count(text: str, mode: str = "weighted") -> int:
    return sum(_weight(c) for c in text) if mode == "weighted" else len(text)


def parse(md: str) -> list:
    """[(番号, 切り口, 本文)] を返す。"""
    posts, cur = [], None
    for line in md.splitlines():
        m = HEADING.match(line)
        if m:
            cur = [int(m.group(1)), m.group(2), []]
            posts.append(cur)
        elif cur is not None:
            cur[2].append(line)
    return [(n, a, "\n".join(b).strip()) for n, a, b in posts]


def validate(md: str, cfg: dict):
    """(errors, warnings) を返す。"""
    errors, warns = [], []
    posts = parse(md)
    if len(posts) != 5:
        errors.append(f"投稿は見出し付きでちょうど5本必要です（現在{len(posts)}本）。")
    for i, (n, angle, _) in enumerate(posts[:5]):
        if n != i + 1 or angle != ANGLES[i]:
            errors.append(f"{i + 1}番目の見出しは「## {i + 1}. {ANGLES[i]}」にしてください（現在: {n}. {angle}）。")
    mode = cfg.get("count_mode", "weighted")
    limit = LIMITS.get(mode, 280)
    banned = list(cfg.get("ng_words", [])) + list(cfg.get("hype_words", []))
    for n, angle, body in posts:
        tag = f"投稿{n}（{angle}）"
        if not body:
            errors.append(f"{tag}: 本文が空です。")
            continue
        c = count(body, mode)
        if c > limit:
            errors.append(f"{tag}: {c}/{limit}（{mode}）で字数超過です。短くしてください。")
        for w in banned:
            if w in body:
                errors.append(f"{tag}: 禁止/誇張表現「{w}」を含みます。言い換えてください。")
        for k in cfg.get("review_keywords", []):
            if k in body:
                warns.append(f"{tag}: 「{k}」を含みます。要目視確認（誤情報リスク）。")
    for i in range(len(posts)):
        for j in range(i + 1, len(posts)):
            r = difflib.SequenceMatcher(None, posts[i][2], posts[j][2]).ratio()
            if posts[i][2] and r > SIMILARITY:
                errors.append(f"投稿{posts[i][0]}と投稿{posts[j][0]}が酷似しています（類似度{r:.2f}）。切り口を変えてください。")
    return errors, warns


def main() -> int:
    args = sys.argv[1:]
    hook = "--hook" in args
    args = [a for a in args if a != "--hook"]
    if args and args[0] == "--latest":
        files = sorted((root() / "outputs").glob("*_posts.md"), key=lambda p: p.stat().st_mtime)
        if not files:
            return 0
        path = files[-1]
    elif args:
        path = Path(args[0])
    else:
        print("usage: validate_posts.py <file.md> | --latest [--hook]", file=sys.stderr)
        return 2
    errors, warns = validate(path.read_text(encoding="utf-8"), load_config())
    out = sys.stderr if hook else sys.stdout
    for e in errors:
        print(f"NG: {e}", file=out)
    for w in warns:
        print(f"WARN: {w}", file=out)
    if not errors:
        print(f"OK: {path.name}", file=out)
    return (2 if hook else 1) if errors else 0


if __name__ == "__main__":
    sys.exit(main())
