# v1.5.5 星読みモード生成エラー修正

## 症状

公開環境で生成ボタンを押すと、次のエラーが表示され、数字を生成できない場合がありました。

```text
Unknown mode_id: astrology
```

Renderのログでは `POST /generate` が `400` になっていました。

## 原因

画面と `app.py` は星読みモード `astrology` に対応していても、公開先の
`config/mode_rules.json` だけが古い状態で残ると、生成エンジンが
`astrology` のルールを見つけられませんでした。

## 修正

`app.py` に星読みモードの安全な既定ルールを追加しました。
`config/mode_rules.json` に星読み設定がある場合はその値を優先し、
設定が欠けている場合だけ既定値で補完します。

これにより、公開先でJSON設定の更新が一時的に不完全でも、
`mode_id=astrology` を正常に処理できます。
