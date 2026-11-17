import unittest
import helpers
from common import load_config
from validate_posts import count, validate

CFG = load_config()


def with_post(n, text):
    out, cur = [], 0
    for line in helpers.GOOD.splitlines():
        if line.startswith("## "):
            cur = int(line[3])
        if cur == n and not line.startswith("## ") and line.strip():
            line = text
        out.append(line)
    return "\n".join(out)


class Validate(unittest.TestCase):
    def test_good_passes(self):
        errors, _ = validate(helpers.GOOD, CFG)
        self.assertEqual(errors, [])

    def test_weighted_count(self):
        self.assertEqual(count("abc"), 3)
        self.assertEqual(count("あいう"), 6)
        self.assertEqual(count("あいう", "simple"), 3)

    def test_too_long_weighted(self):
        errors, _ = validate(with_post(2, "あ" * 141), CFG)  # 282 > 280
        self.assertTrue(any("字数超過" in e for e in errors))

    def test_simple_mode_limit(self):
        errors, _ = validate(with_post(2, "あ" * 141), {**CFG, "count_mode": "simple"})
        self.assertTrue(any("字数超過" in e for e in errors))
        errors, _ = validate(with_post(2, "あ" * 140), {**CFG, "count_mode": "simple"})
        self.assertEqual(errors, [])

    def test_wrong_count_and_order(self):
        errors, _ = validate("## 1. 共感型\nこんにちは", CFG)
        self.assertTrue(any("5本" in e for e in errors))
        swapped = helpers.GOOD.replace("学び型", "TMP").replace("気づき型", "学び型").replace("TMP", "気づき型")
        errors, _ = validate(swapped, CFG)
        self.assertTrue(any("見出し" in e for e in errors))

    def test_hype_and_ng_words(self):
        errors, _ = validate(with_post(3, "これで絶対に成功します"), CFG)
        self.assertTrue(any("絶対" in e for e in errors))
        errors, _ = validate(with_post(3, "情弱は損をします"), CFG)
        self.assertTrue(any("情弱" in e for e in errors))

    def test_duplicates(self):
        errors, _ = validate(with_post(2, "毎日ネタに悩むの、わかります。動画の字幕を使うと楽になります。"), CFG)
        self.assertTrue(any("酷似" in e for e in errors))

    def test_review_keyword_warns_not_fails(self):
        errors, warns = validate(with_post(3, "投資の話は慎重に聞きたいですね"), CFG)
        self.assertEqual(errors, [])
        self.assertTrue(any("要目視確認" in w for w in warns))


if __name__ == "__main__":
    unittest.main()
