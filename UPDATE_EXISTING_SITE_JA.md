# 公開済みサイトを v1.5.6 へ更新する手順

1. `lotoscope6_v1.5.6_birthdate_visibility_fix.zip` を右クリックし、「すべて展開」を選びます。
2. GitHubの `lotoscope6-web` を開きます。
3. `Add file` → `Upload files` を選びます。
4. 展開したフォルダを開き、その中のファイルとフォルダをすべてアップロードします。
5. コミット名へ次を入力します。

```text
Fix birth date visibility v1.5.6
```

6. `Commit directly to the main branch` のまま `Commit changes` を押します。
7. Renderが自動で再公開します。
8. `Live`になったら公開サイトを `Ctrl + F5` で再読み込みしてください。

GitHubの最上位に `app.py`、`render.yaml`、`requirements.txt` が並ぶ配置を維持してください。

## 更新後の確認

- Renderの最新デプロイが `Live` になる
- 公開サイトを `Ctrl + F5` で再読み込みする
- 生年月日を `2000年10月11日` にして、選択欄が `2000年`・`10月`・`11日` と完全に見える
- `12月31日` も2桁目が隠れずに表示される
- 「六つの数字を受け取る」を押し、数字が正常に生成される
- `Unknown mode_id: astrology` が表示されない
- Renderのログで `POST /generate` が `200` になる
- 公開ページのCSSまたはJavaScript URLに `v=v1.5.6-public` が表示される
