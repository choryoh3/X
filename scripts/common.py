"""共通ユーティリティ: パス・設定・状態・.env。標準ライブラリのみ。"""
import json
import os
import re
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DIRS = ("videos", "subtitles", "transcripts", "outputs", "state")


def root() -> Path:
    """データの置き場。テストでは XPIPE_ROOT で差し替える。"""
    return Path(os.environ.get("XPIPE_ROOT", REPO))


def ensure_dirs() -> None:
    for d in DIRS:
        (root() / d).mkdir(parents=True, exist_ok=True)


def load_env() -> None:
    """.env を読み込む（既存の環境変数は上書きしない）。"""
    path = REPO / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip("\"'"))


def load_config() -> dict:
    """config.yaml の最小サブセット（key: value / key: + '- item' リスト）を読む。"""
    cfg, key = {}, None
    for raw in (REPO / "config.yaml").read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.lstrip().startswith("- ") and key:
            cfg[key].append(line.lstrip()[2:].strip().strip("\"'"))
        elif ":" in line and not line.startswith(" "):
            key, val = line.split(":", 1)
            key, val = key.strip(), val.strip().strip("\"'")
            cfg[key] = val if val else []
    return cfg


def state_path() -> Path:
    return root() / "state" / "processed.json"


def load_state() -> dict:
    p = state_path()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save_state(state: dict) -> None:
    p = state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def video_id(url: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{11})", url)
    if not m:
        raise ValueError(f"YouTubeのURLから動画IDを取れません: {url}")
    return m.group(1)


def slugify(title: str, limit: int = 50) -> str:
    s = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "", title)
    s = re.sub(r"\s+", "_", s.strip())
    return (s[:limit] or "untitled").strip("._")


def today() -> str:
    return datetime.now().strftime("%Y%m%d")
