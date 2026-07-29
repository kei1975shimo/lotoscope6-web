# 公開済みサイトを v1.7.9 へ更新する手順

## GitHubへアップロード

1. `loto_numbers_scope_v1.7.9_clear_retry_and_home_buttons.zip` を右クリックし、「すべて展開」を選びます。
2. GitHubの現在使用しているリポジトリ（例：`lotoscope6-web`）を開きます。
3. `Add file` → `Upload files` を選びます。
4. 展開したフォルダの中身をすべてアップロードし、既存ファイルを上書きします。
5. コミット名へ次を入力します。

```text
Clarify retry and home buttons v1.7.9
```

6. `Commit directly to the main branch` のまま `Commit changes` を押します。
7. Renderの自動デプロイが完了するまで、Render画面で状態を確認します。
8. `Live`になったら公開サイトを `Ctrl + F5` で再読み込みします。

GitHubの最上位に `app.py`、`render.yaml`、`requirements.txt` が並ぶ配置を維持してください。

## 更新後の確認

- ブランド表示が「ロトナンバーズ・スコープ」になっている
- 五つの券種それぞれに異なる儀式名が表示される
- ミニロトは月輪、ロト6は六星印、ロト7は七惑星の演出になる
- ナンバーズ3は三つの星盤、ナンバーズ4は四つの星門の演出になる
- ミニロトは5個、ロト6は6個、ロト7は7個生成される
- ナンバーズ3は3桁、ナンバーズ4は4桁で表示される
- `007`や`0038`のような先頭の0が保持される
- 結果画面に答え合わせボタンが表示されない
- Renderログで `POST /generate` が `200` になる
- 結果画面に「同じ条件でもう一度」と「最初から選び直す」が明確なボタンとして表示される
- 「同じ条件でもう一度」で券種別の星の儀式が再び始まる
- 「最初から選び直す」で入力を空にしたトップ画面へ戻る
- CSSとJavaScriptのURLに `v=v1.7.9-clear-retry-and-home-actions` が付く

## 以前のURLについて

Renderの既存サービスをそのまま更新する場合、公開URLは変わりません。`render.yaml`のサービス名 `lotoscope6-web` は、既存サービスとの互換性を保つためそのまま残しています。
