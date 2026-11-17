import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import helpers
import pipeline
from common import load_state

URL = "https://www.youtube.com/watch?v=abcdefghijk"


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        t = Path(self.tmp.name)
        self.srt = t / "in.srt"
        self.srt.write_text(helpers.SRT, encoding="utf-8")
        # 偽の生成器: カウンタファイルで1回目は不合格、2回目以降は合格を返す
        self.counter = t / "calls"
        gen = t / "gen.py"
        gen.write_text(
            "import sys, pathlib\n"
            f"c = pathlib.Path({str(self.counter)!r})\n"
            "n = int(c.read_text()) + 1 if c.exists() else 1\n"
            "c.write_text(str(n))\n"
            "sys.stdin.read()\n"
            f"good = {helpers.GOOD!r}\n"
            "print(good.replace('毎日', '絶対に毎日') if n == 1 else good)\n",
            encoding="utf-8")
        env = {"XPIPE_ROOT": str(t / "data"), "POST_GENERATOR": f'"{sys.executable}" "{gen}"'}
        p = mock.patch.dict(os.environ, env)
        p.start()
        self.addCleanup(p.stop)

    def calls(self):
        return int(self.counter.read_text())

    def test_end_to_end_retry_and_idempotent(self):
        out = pipeline.run(URL, srt=self.srt, title="テスト動画 #1")
        self.assertTrue(out.exists())
        self.assertIn("_テスト動画_#1_posts.md", out.name)
        self.assertEqual(self.calls(), 2)  # 1回目NG → 差し戻し → 2回目OK
        self.assertEqual(load_state()["abcdefghijk"]["output"], out.name)
        again = pipeline.run(URL, srt=self.srt, title="テスト動画 #1")
        self.assertEqual(again, out)
        self.assertEqual(self.calls(), 2)  # 再実行では生成しない

    def test_gives_up_after_three_failures(self):
        with mock.patch.dict(os.environ, {"POST_GENERATOR": f'"{sys.executable}" -c "print(1)"'}):
            with self.assertRaises(RuntimeError):
                pipeline.run(URL, srt=self.srt, title="x")

    def test_fallback_to_transcribe_when_no_subtitles(self):
        with mock.patch.object(pipeline.fetch, "get_title", return_value="無字幕動画"), \
             mock.patch.object(pipeline.fetch, "fetch_subs", return_value=None), \
             mock.patch.object(pipeline.fetch, "download_audio", return_value=Path("a.mp3")) as da, \
             mock.patch.object(pipeline.transcribe, "transcribe", return_value="音声からの文字起こし") as tr:
            out = pipeline.run(URL)
        da.assert_called_once()
        tr.assert_called_once()
        self.assertTrue(out.exists())
        self.assertEqual(load_state()["abcdefghijk"]["transcript_source"], "gladia")

    def test_missing_generator_is_clear_error(self):
        with mock.patch.dict(os.environ, {"POST_GENERATOR": "no-such-cmd-xyz"}):
            with self.assertRaises(FileNotFoundError):
                pipeline.run(URL, srt=self.srt, title="x")


if __name__ == "__main__":
    unittest.main()
