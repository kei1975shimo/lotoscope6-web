# ローカル版と公開版の違い

## ローカル版

- `python src/web_app.py` で起動
- output/ にCSVやHTMLを保存
- データ取得ツールも同居
- ローカル検証向き

## 公開版 v1.0

- `gunicorn app:app` で起動
- output/ 保存なし
- 任意ファイルパス入力なし
- Flask + templates/static構成
- Render等へのデプロイ向き

## 次の段階

- GitHubへアップ
- Renderにデプロイ
- 独自ドメイン設定
- アクセスログ確認
