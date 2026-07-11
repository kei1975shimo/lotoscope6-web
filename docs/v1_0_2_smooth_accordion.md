# v1.0.2 Smooth Accordion

スマホでの操作感を改善するため、生成結果・照合結果のアコーディオンにスライド開閉アニメーションを追加。

- `details/summary` の中身を JavaScript で `.smooth-content` にラップ
- 高さを計算して滑らかに開閉
- 同一グループ内では、開いたアコーディオン以外を自動で閉じる
- `prefers-reduced-motion` に対応

ロジック、スコア計算、生成処理、照合処理は変更なし。
