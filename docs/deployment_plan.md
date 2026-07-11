# デプロイ手順メモ

## 1. GitHubへアップロード

公開用フォルダ `lotoscope6_web_v1_0_public_flask` をGitHubリポジトリに入れる。

入れるもの:

- app.py
- requirements.txt
- render.yaml
- Procfile
- src/
- templates/
- static/
- config/
- data/raw/loto6_results.csv
- data/processed/number_stats.csv
- docs/

入れないもの:

- output/
- __pycache__/
- .env
- *.sqlite

## 2. Render Web Service作成

- New > Web Service
- GitHubリポジトリを選択
- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`

## 3. 環境変数

- `SECRET_KEY`: 長いランダム文字列
- `APP_ENV`: `production`

## 4. 動作確認

- `/` が開くか
- 買い目生成できるか
- 結果照合画面へ進めるか
- 回号照合できるか
- スマホ表示が崩れないか

## 5. 公開前チェック

- DebugがOFF
- Tracebackが画面に出ない
- 任意ファイルパスをユーザーに入力させない
- サーバーに生成履歴を保存しない
- 免責文が表示されている
