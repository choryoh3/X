# X

YouTube動画のURLを1つ渡すと、X（旧Twitter）向けの投稿案を5パターン自動生成するパイプライン。
字幕取得（yt-dlp）→ 整形 → 生成（Claude Code）→ 機械検証 → 保存、までを1コマンドで実行します。

## セットアップ（約5分）

必要: Python 3.9+、[Claude Code](https://docs.claude.com/en/docs/claude-code)（`npm install -g @anthropic-ai/claude-code`）

```bash
make setup
```

`make` がない環境（Windows）では `pip install -U yt-dlp` を実行し、`.env.example` を `.env` にコピーしてください。

## 使い方

```bash
make run URL="https://www.youtube.com/watch?v=XXXXXXXXXXX"
```

Claude Code 内からは `/post <URL>` でも実行できます。結果は `outputs/YYYYMMDD_<タイトル>_posts.md` に保存されます。
同じURLを再実行すると処理済みとしてスキップされます（やり直すなら `python3 scripts/pipeline.py <URL> --force`）。

## 字幕が取得できない場合

音声を取得して Gladia API で文字起こしします。[gladia.io](https://gladia.io) でキーを取得し、`.env` の `GLADIA_API_KEY` に設定してください。

## カスタマイズ

- `config.yaml`: ターゲット像、トーン、NGワード、字数モード（`weighted` / `simple`）
- `prompts/post_template.md`: 指示文テンプレート

## 検証と注意

生成後に `scripts/validate_posts.py` が、5本構成・字数・NG/誇張表現・重複を検証し、不合格なら理由を添えて最大3回再生成します。
医療・金融・法律のキーワードは警告（要目視確認）になります。固有名詞の誤変換は必ず目視で確認し、動画の転載ではなく要点を再構成して使ってください。

## 開発

```bash
make test
```

構成と規約は [CLAUDE.md](CLAUDE.md) を参照。
