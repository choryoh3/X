---
description: YouTube URLからX投稿案を5パターン生成して outputs/ に保存する
argument-hint: <YouTubeのURL>
---

次のコマンドを実行し、結果を報告してください。

```
python3 scripts/pipeline.py $ARGUMENTS
```

- 「保存しました」と出たら、保存先のパスと5案を要約して見せる。
- 「エラー」で終わった場合は、原因と次の一手（yt-dlp更新、GLADIA_API_KEY設定など）を伝える。
- 投稿案の本文は自分で書き換えない。直したいときは検証 (`python3 scripts/validate_posts.py <file>`) を通すこと。
- WARN（要目視確認）が出た場合は、医療・金融・法律の内容として確認が必要と伝える。
