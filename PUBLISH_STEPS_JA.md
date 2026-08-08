# ロト・スコープ v1.9.2 公開手順（GitHub + Render）

1. このフォルダ全体をGitHubリポジトリへ配置します。
2. Renderでリポジトリを接続します。
3. `render.yaml` を使ってWeb Serviceを作成します。
4. Build Command は `pip install -r requirements.txt`、Start Command は `gunicorn app:app` です。
5. `/health` が `OK` を返すことを確認します。
6. トップ画面からミニロト・ロト6・ロト7の3券種すべてで生成できることを確認します。

現在の公開版は過去抽せんCSVを必要としません。
