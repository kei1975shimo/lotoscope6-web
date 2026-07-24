# 公開済みサイトを v1.5.5 へ更新する手順

1. `lotoscope6_v1.5.5_astrology_mode_hotfix.zip` を右クリックし、「すべて展開」を選びます。
2. GitHubの `lotoscope6-web` を開きます。
3. `Add file` → `Upload files` を選びます。
4. 展開したフォルダを開き、その中のファイルとフォルダをすべてアップロードします。
5. コミット名へ次を入力します。

```text
Fix astrology mode generation v1.5.5
```

6. `Commit directly to the main branch` のまま `Commit changes` を押します。
7. Renderが自動で再公開します。
8. `Live`になったら公開サイトを `Ctrl + F5` で再読み込みしてください。

GitHubの最上位に `app.py`、`render.yaml`、`requirements.txt` が並ぶ配置を維持してください。

## 更新後の確認

- Renderの最新デプロイが `Live` になる
- 公開サイトを `Ctrl + F5` で再読み込みする
- 生年月日を選んで「六つの数字を受け取る」を押す
- `Unknown mode_id: astrology` が表示されず、数字が生成される
- Renderのログで `POST /generate` が `200` になる
- 公開ページのCSSまたはJavaScript URLに `v=v1.5.5-public` が表示される
