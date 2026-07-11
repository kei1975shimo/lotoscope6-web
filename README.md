# LOTOSCOPE 6 公開用Flask版 v1.0.16

ロトスコープ6の公開テスト用Webアプリです。ロト6の数字選びを補助し、生成した買い目を抽せん結果と照合できます。

## 方針

- Flask + Gunicornで公開する前提
- 生成履歴・HTML・CSVをサーバーに保存しない
- ユーザーに任意ファイルパスを入力させない
- 好きな数字・避けたい数字は各5個まで
- 1回の生成口数は各モード最大10口まで
- 結果照合は、署名付き・期限付きの一時データを使う
- POSTフォームはCSRFトークンで保護する
- 簡易レート制限で連続送信を抑制する

## ローカル起動

```bash
pip install -r requirements.txt
python app.py
```

ブラウザで以下を開きます。

```text
http://127.0.0.1:8786/
```

## Renderでの公開

詳しい手順は `PUBLISH_STEPS_JA.md` を参照してください。`render.yaml` を使うBlueprint公開に対応しています。

### 手動設定する場合


Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
gunicorn app:app
```

## 必須の環境変数

本番公開時は必ず設定してください。

```text
APP_ENV=production
SECRET_KEY=十分に長いランダム文字列
```

`APP_ENV=production` の状態で `SECRET_KEY` が未設定の場合は、危険なデフォルトキーで起動しないようにアプリが停止します。

## 任意の環境変数

```text
TICKET_TOKEN_MAX_AGE_SECONDS=86400
RATE_LIMIT_PER_MINUTE=30
```

- `TICKET_TOKEN_MAX_AGE_SECONDS`: 生成した買い目照合トークンの有効期限。標準は24時間です。
- `RATE_LIMIT_PER_MINUTE`: IPごとのPOST操作上限。標準は1分30回です。0以下にすると無効化します。

## データ更新

同梱データは `data/raw/loto6_results.csv` を参照しています。抽せん結果を追加・更新したあとは、以下で数字別スコアを再作成してください。

```bash
python src/analyze_numbers.py --input data/raw/loto6_results.csv --stats-output data/processed/number_stats.csv
```

アプリ画面には、過去データが14日以上古い場合に注意表示が出ます。購入・当せん確認は必ず公式情報をご確認ください。

## 注意

このツールは数字選びを補助するものです。当選を保証するものではありません。宝くじの購入・当せん確認は公式情報をご確認ください。


## 公開用パッケージでの追加対応

- Renderの現行Blueprint仕様に合わせて `runtime: python` を使用
- Pythonバージョンを `.python-version` で固定
- `/health` をRenderのヘルスチェック対象に設定
- 本番環境でセッションCookieに `Secure` / `HttpOnly` / `SameSite=Lax` を設定
- `__pycache__`、`*.pyc`、未使用の重複テンプレートを除外

## v1.0.13

- 本番環境で `SECRET_KEY` 未設定の場合は起動停止
- 生成結果トークンを期限付き署名へ変更
- POSTフォームにCSRF対策を追加
- 簡易レート制限を追加
- セキュリティヘッダーを追加
- データ鮮度の注意表示を追加
- ZIP配布物から `__pycache__` / `*.pyc` を除外


## v1.0.14
- スマホアプリ向けにUIを再調整
- 上部アプリバー、セクションナビ、固定操作ボタンを追加
- 入力欄・モードカード・照合画面をタップしやすいサイズに調整


## v1.0.15
- iPhoneアプリらしい明るいUIに再調整
- 白カード / 青ボタン / すりガラス風バー / iOS風配色に変更
- 入力・結果・照合画面をネイティブアプリ寄りの見た目に最適化

## v1.0.16
- 占星術ロータスUIを唯一の正式デザインとして再構築(重ね上書きのCSSを整理統合)
- ボタンの高さ・余白がバラついてずれて見えていた問題を修正
- スクロール時に固定ナビ同士が重なっていた問題を修正
- タップ時の縮小フィードバックなど、スマホアプリらしいモーションを追加
- 詳細は `v1_0_16_lotus_rebuild.md` を参照
