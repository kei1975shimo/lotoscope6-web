# 公開済みサイトを v1.5.4 へ更新する手順

1. `lotoscope6_v1.5.4_zodiac_layout_fix.zip` を右クリックし、「すべて展開」を選びます。
2. GitHubの `lotoscope6-web` を開きます。
3. `Add file` → `Upload files` を選びます。
4. 展開したフォルダを開き、その中のファイルとフォルダをすべてアップロードします。
5. コミット名へ次を入力します。

```text
Refresh fortune teller guidance copy v1.5.4
```

6. `Commit directly to the main branch` のまま `Commit changes` を押します。
7. Renderが自動で再公開します。
8. `Live`になったら公開サイトを `Ctrl + F5` で再読み込みしてください。

GitHubの最上位に `app.py`、`render.yaml`、`requirements.txt` が並ぶ配置を維持してください。

## 更新後の確認

- 生年月日を選ぶと「星図への刻印」が表示される
- `SEALED`がカード右上に表示される
- 星座カードが刻印欄の横幅いっぱいに表示される
- 星座名が1文字ずつ縦に折り返されない
- 星座マーク、日本語名、英語名が読める
- 生成後、約4秒間の星読み演出が動く
