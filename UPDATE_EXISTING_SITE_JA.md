# 公開済みサイトを v1.9.2 へ更新する手順

1. 既存リポジトリのアプリ一式を、このクリーン版の内容で置き換えます。
2. 変更をGitへコミットし、公開ブランチへpushします。
3. RenderのAuto Deploy、またはManual Deployを実行します。
4. `/health` が `OK` を返すことを確認します。
5. ミニロト、ロト6、ロト7を各1回生成して動作確認します。

旧版の `data/`、`balance_rules.json`、`mode_rules.json`、旧ロト6分析Pythonファイルは不要です。
