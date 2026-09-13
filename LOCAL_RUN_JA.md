# Windowsでの起動

1. ZIPを展開します。
2. `app.py` があるフォルダで、ターミナルまたはPowerShellを開きます。
3. 初回は次を順番に実行します。Python 3.10以降が必要です。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:APP_ENV='development'
$env:TRUSTED_PROXY_HOPS='0'
.\.venv\Scripts\python.exe app.py
```

ブラウザーで `http://127.0.0.1:8786` を開きます。終了は `Ctrl + C` です。

2回目以降は、そのフォルダで次を実行します。

```powershell
$env:APP_ENV='development'
$env:TRUSTED_PROXY_HOPS='0'
.\.venv\Scripts\python.exe app.py
```

仮想環境のActivate.ps1を実行する必要はありません。
ローカル起動でSECRET_KEY未指定の場合は起動ごとに秘密鍵を作ります。再起動後は入力画面を再読み込みしてください。
VS Codeの実行メニューからも起動できます。

この手順はPC上の動作確認用です。外部公開は `UPDATE_EXISTING_SITE_JA.md` を参照してください。
