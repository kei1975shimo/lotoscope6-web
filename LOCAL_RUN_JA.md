# Windowsターミナルで起動する方法

## 初回だけ

```powershell
cd "展開したフォルダの場所\loto_scope_v1.9.2_compact"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
$env:SECRET_KEY='local-dev-secret'
python app.py
```

ブラウザで `http://127.0.0.1:8786` を開きます。
終了は `Ctrl + C` です。

## 2回目以降

```powershell
cd "展開したフォルダの場所\loto_scope_v1.9.2_compact"
.\.venv\Scripts\Activate.ps1
$env:SECRET_KEY='local-dev-secret'
python app.py
```

## Activate.ps1 が実行できない場合

```powershell
cd "展開したフォルダの場所\loto_scope_v1.9.2_compact"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:SECRET_KEY='local-dev-secret'
.\.venv\Scripts\python.exe app.py
```
