# ロト6結果データ更新手順

このアプリは `data/raw/loto6_results.csv` を元に、数字別スコア `data/processed/number_stats.csv` を作ります。

## 1. 抽せん結果CSVを更新

`data/raw/loto6_results.csv` に新しい抽せん回を追加します。最低限、以下の列が必要です。

```text
draw_no,draw_date,weekday,main_1,main_2,main_3,main_4,main_5,main_6,bonus
```

既存CSVには `set_sum` などの集計列もありますが、スコア再作成時に整形できます。

## 2. 数字別スコアを再作成

```bash
python src/analyze_numbers.py --input data/raw/loto6_results.csv --stats-output data/processed/number_stats.csv
```

必要に応じて整形済み抽せん結果も出力します。

```bash
python src/analyze_numbers.py \
  --input data/raw/loto6_results.csv \
  --cleaned-output data/processed/cleaned_draws.csv \
  --stats-output data/processed/number_stats.csv
```

## 3. 画面で確認

トップ画面を開き、データ鮮度の警告が出ないか確認します。14日以上古い場合は、画面上に注意表示が出ます。

## 注意

このアプリは抽せん結果の公式取得までは自動化していません。公開運用では、公式情報からCSVを更新してからスコア再作成を行ってください。
