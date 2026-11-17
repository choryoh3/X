"""オーケストレーター: URL → 字幕 → 整形 → 生成 → 検証(最大3回) → 保存。冪等。

生成コマンドは環境変数 POST_GENERATOR（既定: "claude -p"）。プロンプトは標準入力、出力は標準出力。
"""
import argparse
import os
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import clean_srt
import fetch
import transcribe
import validate_posts
from common import (REPO, ensure_dirs, load_config, load_env, load_state, root,
                    save_state, slugify, today, video_id)

MAX_RETRY = 3


def build_prompt(transcript: str, cfg: dict) -> str:
    tpl = (REPO / "prompts" / "post_template.md").read_text(encoding="utf-8")
    return (tpl.replace("{target}", cfg.get("target", "")).replace("{tone}", cfg.get("tone", ""))
            .replace("{transcript}", transcript))


def generate(prompt: str) -> str:
    cmd = shlex.split(os.environ.get("POST_GENERATOR", "claude -p"), posix=os.name != "nt")
    if not shutil.which(cmd[0]):
        raise FileNotFoundError(f"生成コマンド「{cmd[0]}」が見つかりません。Claude Codeを入れるか POST_GENERATOR を設定してください。")
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8", timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f"生成コマンド失敗: {r.stderr.strip()[-300:]}")
    return re.sub(r"^```\w*\n|\n```\s*$", "", r.stdout.strip())


def generate_validated(transcript: str, cfg: dict):
    """生成→検証→差し戻しのループ。(本文, 警告) を返す。上限超過は RuntimeError。"""
    prompt, feedback = build_prompt(transcript, cfg), ""
    for attempt in range(1, MAX_RETRY + 1):
        out = generate(prompt + feedback)
        errors, warns = validate_posts.validate(out, cfg)
        if not errors:
            return out, warns
        print(f"[検証NG {attempt}/{MAX_RETRY}] " + " / ".join(errors), file=sys.stderr)
        feedback = ("\n\n# 前回の出力は次の検証に不合格でした。全て修正して、全文を出力し直してください。\n"
                    + "\n".join(f"- {e}" for e in errors) + f"\n\n# 前回の出力\n{out}\n")
    raise RuntimeError(f"{MAX_RETRY}回再生成しても検証に通りません。人間の確認が必要です:\n" + "\n".join(errors))


def run(url: str, srt: Path = None, title: str = None, force: bool = False) -> Path:
    load_env()
    ensure_dirs()
    cfg, state = load_config(), load_state()
    vid = video_id(url)
    rec = state.get(vid, {})
    done = root() / "outputs" / rec["output"] if rec.get("output") else None
    if done and done.exists() and not force:
        print(f"処理済み（スキップ）: {done}")
        return done

    # 1-2. 字幕（なければ音声→Gladia）→ 整形テキスト
    tx = root() / "transcripts" / f"{vid}.txt"
    if force or not (tx.exists() and tx.read_text(encoding="utf-8").strip()):
        title = title or rec.get("title") or fetch.get_title(url)
        srt = srt or fetch.fetch_subs(url, vid)
        if srt:
            text, source = clean_srt.clean_srt(Path(srt).read_text(encoding="utf-8")), "subtitles"
        else:
            print("字幕が取得できないため、音声の文字起こしに切り替えます。", file=sys.stderr)
            text, source = transcribe.transcribe(fetch.download_audio(url, vid)), "gladia"
        tx.write_text(text, encoding="utf-8")
        rec.update(title=title, transcript_source=source, fetched_at=datetime.now().isoformat(timespec="seconds"))
        state[vid] = rec
        save_state(state)
    title = title or rec.get("title") or vid

    # 3-4. 生成 + 検証ループ
    posts, warns = generate_validated(tx.read_text(encoding="utf-8"), cfg)

    # 5. 保存
    out = root() / "outputs" / f"{today()}_{slugify(title)}_posts.md"
    out.write_text(posts + "\n", encoding="utf-8")
    rec.update(url=url, output=out.name, generated_at=datetime.now().isoformat(timespec="seconds"))
    state[vid] = rec
    save_state(state)
    for w in warns:
        print(f"WARN: {w}", file=sys.stderr)
    print(f"保存しました: {out}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="YouTube URL から X投稿案を生成する")
    ap.add_argument("url")
    ap.add_argument("--srt", help="取得済みのsrtを使う（ネットワーク不要）")
    ap.add_argument("--title", help="動画タイトルを手動指定")
    ap.add_argument("--force", action="store_true", help="処理済みでも再実行")
    a = ap.parse_args()
    try:
        run(a.url, Path(a.srt) if a.srt else None, a.title, a.force)
    except (RuntimeError, FileNotFoundError, ValueError, TimeoutError) as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
