"""yt-dlpで字幕を取得する。手動字幕を優先し、なければ自動生成字幕。"""
import os
import shlex
import subprocess
from pathlib import Path

from common import root


def _run(args: list) -> str:
    extra = shlex.split(os.environ.get("YTDLP_ARGS", ""))  # 例: --cookies-from-browser chrome
    r = subprocess.run(["yt-dlp", *extra, *args], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        hint = ""
        if "Sign in" in r.stderr or "cookies" in r.stderr:
            hint = "\n  → YouTubeのボット判定です。.env に YTDLP_ARGS=--cookies-from-browser chrome を設定してください。"
        raise RuntimeError(f"yt-dlp失敗: {r.stderr.strip()[-300:]}{hint}")
    return r.stdout


def get_title(url: str) -> str:
    return _run(["--skip-download", "--no-playlist", "--print", "%(title)s", url]).strip().splitlines()[0]


def fetch_subs(url: str, vid: str, lang: str = "ja"):
    """字幕srtのPathを返す。取得できない/空なら None。"""
    out = root() / "subtitles" / f"{vid}.%(ext)s"
    _run(["--skip-download", "--no-playlist", "--write-subs", "--write-auto-subs",
          "--sub-langs", lang, "--convert-subs", "srt", "-o", str(out), url])
    for p in sorted((root() / "subtitles").glob(f"{vid}.*.srt")):
        if p.read_text(encoding="utf-8", errors="ignore").strip():
            return p
    return None


def download_audio(url: str, vid: str) -> Path:
    """字幕なし時のフォールバック用に音声だけ保存する（videos/）。"""
    out = root() / "videos" / f"{vid}.%(ext)s"
    _run(["--no-playlist", "-x", "--audio-format", "mp3", "-o", str(out), url])
    return root() / "videos" / f"{vid}.mp3"
