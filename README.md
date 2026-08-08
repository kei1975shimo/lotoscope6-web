# ロト・スコープ 公開用Flask版 v1.9.8

生年月日と生成日の七天体から、数字選択式宝くじの候補を導くWebアプリです。
現在の生成方式では、過去の抽せんデータ・コールド数字・旧バランス設定は使用しません。

## 対応している宝くじ

- ミニロト：1〜31から異なる5個
- ロト6：1〜43から異なる6個
- ロト7：1〜37から異なる7個

## 現在の主な構成

```text
app.py
requirements.txt
render.yaml
Procfile
config/
  app_settings.json
src/
  astrology_numbers.py
  product_numbers.py
  utils.py
templates/
  base.html
  index.html
  result.html
  error.html
static/
  css/style.css
  js/app.js
tests/
  smoke_test.py
```

## Windows Terminal / PowerShell で初回起動

Python 3.10以降を使用してください。`.python-version` は 3.12.7 です。

1. ZIPを展開し、Windows TerminalまたはPowerShellを開きます。
2. `cd` でこのフォルダへ移動します。
3. 次を順番に実行します。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
$env:SECRET_KEY='local-dev-secret'
python app.py
```

起動後、ブラウザで次を開きます。

```text
http://127.0.0.1:8786
```

終了するときはターミナルで `Ctrl + C` を押します。

### 2回目以降

```powershell
.\.venv\Scripts\Activate.ps1
$env:SECRET_KEY='local-dev-secret'
python app.py
```

ローカル環境では `SECRET_KEY` を設定しなくても起動できますが、公開時との違いを減らすため上記では設定しています。

### PowerShellでActivate.ps1が拒否された場合

仮想環境を有効化せず、直接Pythonを呼び出せます。

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:SECRET_KEY='local-dev-secret'
.\.venv\Scripts\python.exe app.py
```

## テスト

依存関係をインストールした状態で、次を実行します。

```powershell
python -m unittest tests.smoke_test -v
```

## Renderへの公開

`render.yaml`、`Procfile`、`requirements.txt`、`app.py` を含むフォルダ全体をデプロイします。
本番では `APP_ENV=production` と `SECRET_KEY` が必要です。`render.yaml` は `SECRET_KEY` を自動生成する設定です。

## 星読みについて

出生時刻と出生地を使わない簡易星読みです。生年月日と生成日の正午（日本時間）における太陽、月、水星、金星、火星、木星、土星の位置と主要アスペクトを、選んだロトの数字範囲へ変換します。

合言葉による再現は「生成日」も条件に含まれるため、同じ日に同じ生年月日・券種・口数・合言葉を使った場合に同じ数字になります。

生成結果や点数は、数字選びを楽しむための独自の目安です。当せん確率や当せんを保証するものではありません。


## v1.9.7
生年月日の太陽星座を大きな星座記号と12星座のシンボル列で表示し、結果画面の太陽・月・生成日の太陽にも星座記号を追加しました。


## v1.9.8

UIを「古い星図・天球儀・占星術盤」の意匠へ寄せたCelestial Patterns版です。

- 画像を背景として貼らず、星座盤・幾何学線・装飾枠をHTML/CSSで描画
- スマホのヒーローに薄い12星座リングと星図線を追加
- ミニロト／ロト6／ロト7のスイッチ左側に券種別の天体シンボルを追加
- 誕生日欄に薄い星座盤パターンを追加
- 生成ボタンを金色のオラクル風デザインへ強化
- 結果画面にも同じ星図・金線の意匠を適用
- 縦方向のレイアウト寸法は大きく増やさず、装飾を主に背景・重ね描画で実装
