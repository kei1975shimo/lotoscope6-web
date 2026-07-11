# 公開済みサイトを v1.3.0 へ更新する手順

1. `lotoscope6_v1.3.0_horoscope_fortune.zip` を右クリックし、「すべて展開」を選びます。
2. GitHubの `lotoscope6-web` を開きます。
3. `Add file` → `Upload files` を選びます。
4. 展開したフォルダを開き、その中のファイルとフォルダをすべてアップロードします。
5. コミット名へ次を入力します。

```text
Update horoscope fortune UI to v1.3.0
```

6. `Commit directly to the main branch` のまま `Commit changes` を押します。
7. Renderが自動で再公開します。`Live`になったら公開サイトを `Ctrl + F5` で再読み込みしてください。

GitHubの最上位に `app.py`、`render.yaml`、`requirements.txt` が並ぶ配置を維持してください。
