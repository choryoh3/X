"""字幕なし時のフォールバック: Gladia API(v2)で音声を文字起こしする。キーは .env の GLADIA_API_KEY。"""
import json
import mimetypes
import os
import time
import urllib.request
import uuid
from pathlib import Path

API = "https://api.gladia.io/v2"


def _req(url, key, data=None, headers=None):
    h = {"x-gladia-key": key, **(headers or {})}
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=120) as r:
        return json.loads(r.read())


def transcribe(audio: Path, timeout_s: int = 1800) -> str:
    key = os.environ.get("GLADIA_API_KEY")
    if not key:
        raise RuntimeError("GLADIA_API_KEY が未設定です。.env に設定してください（.env.example 参照）。")
    boundary = uuid.uuid4().hex
    ctype = mimetypes.guess_type(audio.name)[0] or "application/octet-stream"
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"audio\"; filename=\"{audio.name}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n").encode() + audio.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    up = _req(f"{API}/upload", key, body, {"Content-Type": f"multipart/form-data; boundary={boundary}"})
    job = _req(f"{API}/pre-recorded", key, json.dumps({"audio_url": up["audio_url"], "language": "ja"}).encode(),
               {"Content-Type": "application/json"})
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        res = _req(job["result_url"], key)
        if res["status"] == "done":
            return res["result"]["transcription"]["full_transcript"]
        if res["status"] == "error":
            raise RuntimeError(f"Gladiaがエラーを返しました: {res}")
        time.sleep(5)
    raise TimeoutError("Gladiaの文字起こしがタイムアウトしました")
