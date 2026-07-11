# LOTOSCOPE 6 公開手順（GitHub + Render）

このZIPは、解凍後のファイル一式をGitHubへ置き、RenderのBlueprintとして読み込めば公開できます。

## 先に確認すること

- 同梱の抽せん結果は **第2100回・2026年5月7日まで** です。
- 古いデータのままでもアプリは起動しますが、画面に注意表示が出ます。
- 一般公開前に、公式結果を確認して `data/raw/loto6_results.csv` を更新し、数字別統計を再作成することを推奨します。
- このツールは当せんを保証するものではありません。購入・当せん確認は必ず公式情報で行ってください。

## 1. GitHubへ登録

1. GitHubにログインします。
2. 「New repository」で新しいリポジトリを作成します。
3. リポジトリ名は例として `lotoscope6` とします。
4. 公開範囲は、まず試すなら `Private` でも構いません。
5. このZIPを解凍し、**解凍したフォルダの中身全部**をリポジトリ直下へアップロードします。
6. `app.py`、`render.yaml`、`requirements.txt` がリポジトリの一番上に見えていれば正しい配置です。

## 2. Renderで公開

1. Renderへログインします。
2. 「New」から「Blueprint」を選びます。
3. 先ほど作ったGitHubリポジトリを接続します。
4. Renderが `render.yaml` を読み取ったら、内容を確認してデプロイします。
5. デプロイ完了後、`https://○○.onrender.com` 形式のURLが発行されます。
6. URLを開き、数字生成と抽せん結果照合を試します。

`SECRET_KEY` はRender側で自動生成されます。手動で文字列を用意する必要はありません。

## 3. 動作確認

- トップ画面が表示される
- 好きな数字・避けたい数字を入力できる
- 「買い目候補を作成する」で結果が表示される
- 「全買い目を照合」へ進める
- `/health` を開くと `OK` と表示される

## 4. データ更新

`data/raw/loto6_results.csv` に公式結果を追加した後、プロジェクト直下で次を実行します。

```bash
python src/analyze_numbers.py --input data/raw/loto6_results.csv --stats-output data/processed/number_stats.csv
```

更新した2つのCSVをGitHubへ反映すると、Renderが自動で再デプロイします。

## 無料プランについて

Render無料プランは、しばらくアクセスがないと停止し、最初のアクセス時だけ起動に時間がかかることがあります。常時すぐ開く必要が出た段階で有料プランを検討してください。
