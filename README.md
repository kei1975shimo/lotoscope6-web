# ロト・スコープ v1.17.8

生年月日と日本時間の日付から、占い（西洋占星術・カバラ数秘術・タロット）でミニロト／ロト6／ロト7／ナンバーズ3／ナンバーズ4の数字を導くFlask製Webアプリです。
運営者：下地 恵雄　問い合わせ：keiyuu1975@yahoo.co.jp

## 構成（公開用）

| パス | 内容 |
|---|---|
| `app.py` | Flask本体・画面ルート・セキュリティ設定 |
| `src/` | 占術計算・数字生成 |
| `config/app_settings.json` | 口数の既定値・上限（上限10は変更しない） |
| `templates/` `static/` | 画面・CSS・JavaScript・画像 |
| `requirements.txt` `Procfile` `render.yaml` `.python-version` | Render用設定 |

## v1.17.8 の変更

数字の生成・点数・順番、画面のデザインは変更していません。

- カバラ数秘術の演出を強化：生命の樹を王冠から順に光の稲妻が下り、10の球が段階的に点灯。周囲を1〜9・11・22・33の数字の環が回り、最後に中心から光が広がります。
- タロット選択時、誕生日を入れた段階で大アルカナが先に表示されないようにしました（画面とサーバーの両方で非表示）。カードは抽選演出で初めて開きます。
- 画像を表示サイズに合わせて縮小・再圧縮（約11MB→約3.7MB）。
- 使われていないCSSを削除。JavaScript無効時の説明文・ボタン名が選択中の占術と一致するよう修正。
- 公開に不要なファイル（テスト、開発用資料、Node.js設定）を除外。

## Renderの既存サイトを更新する

1. 現在のリポジトリをバックアップします。
2. このZIPの中身を既存リポジトリへ上書きします。
3. **次の旧ファイル・フォルダーを削除します**（上書きだけでは消えません）：
   `docs/`、`tests/`、`package.json`、`package-lock.json`、`LOCAL_RUN_JA.md`、`UPDATE_EXISTING_SITE_JA.md`、`node_modules/`（あれば）、旧版の `src/utils.py`、`static/img/cosmic-zodiac-wheel.webp`、`PUBLISH_STEPS_JA.md`
4. Renderの環境変数を確認します。

   | 項目 | 設定 |
   |---|---|
   | APP_ENV | production |
   | SECRET_KEY | 設定済みの値を維持 |
   | RATE_LIMIT_PER_MINUTE | 30 |
   | TRUSTED_PROXY_HOPS | 1 |
   | PREMIUM_PREVIEW_ENABLED | 1（一時無料開放。0でロック） |

5. Build Command `pip install -r requirements.txt`、Start Command `gunicorn --workers 1 --threads 4 app:app`。
6. コミット・pushし、デプロイ完了後に `/health` が `OK`、画面下部に `v1.17.8-mystic-oracle` が出ることを確認します。

## PCでの起動（Windows）

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:APP_ENV='development'; $env:TRUSTED_PROXY_HOPS='0'
.\.venv\Scripts\python.exe app.py
```

ブラウザーで `http://127.0.0.1:8786` を開きます。

## 注意

- 点数は占いとの結びつき78%と数字構成22%の独自指標で、当せん確率ではありません。
- 有料プランは未実装です（ストア課金・購入検証・所在地／電話番号の掲載が必要）。準備中の表記を消すだけで販売を開始しないでください。
- テスト・開発資料は別ZIP（`loto_scope_v1.17.8_devtools.zip`）にあります。公開用リポジトリには含めません。
