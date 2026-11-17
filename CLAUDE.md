# YouTube → X投稿案パイプライン（エージェント向け地図）

YouTube URL 1本から、X投稿案を5パターン生成して `outputs/` に保存する。
方針: **LLMの外側を固める**。決定的な処理はスクリプト、LLMは文章生成だけ、品質は検証スクリプトで保証。

## コマンド
- `make setup` : yt-dlp導入・ディレクトリ作成・`.env`作成
- `make run URL=<URL>` または `/post <URL>` : 全工程を実行（Windowsは `python scripts/pipeline.py <URL>`）
- `make validate` : 最新の outputs を検証
- `make test` : ユニットテスト（ネットワーク・APIキー不要）

## 構成
- `scripts/fetch.py` yt-dlpで字幕取得（手動→自動）/ `clean_srt.py` srt整形 / `transcribe.py` Gladiaフォールバック
- `scripts/validate_posts.py` 検証センサー（0=合格, 1=不合格, 理由は1行ずつ）
- `scripts/pipeline.py` 取得→整形→生成→検証(最大3回)→保存。`state/processed.json` で冪等
- `prompts/post_template.md` 指示文 / `config.yaml` ターゲット・トーン・NGワード・字数モード
- `videos/ subtitles/ transcripts/ outputs/ state/` 生成物（gitignore）

## 規約
- 依存は Python3標準ライブラリ + yt-dlp のみ。フレームワーク・DB・Web UIは追加しない。
- 1スクリプト1責務（約100行）。全処理は冪等。秘密情報は `.env` のみ（コミット禁止）。
- Xの字数は重み付け（日本語1文字=2、上限280）が既定。`config.yaml` の `count_mode` で単純140字に切替。
- 投稿は動画の転載でなく要点の再構成。医療・金融・法律はWARN（要目視確認）。
- 生成コマンドは `POST_GENERATOR`（既定 `claude -p`）。テストでは偽の生成器に差し替える。

## 完了条件
`make test` が通り、`make run` で outputs に保存され、再実行がスキップされ、`validate` が OK を返すこと。
