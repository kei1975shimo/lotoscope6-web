# v1.0.11 draw animation

生成ボタン押下後に約3秒の抽選演出を追加。

- スコープ風オーバーレイ
- 数字ボールの発光・回転演出
- 生成ロジック・照合ロジックは変更なし
- 表示演出のみ

調整箇所:
- `static/js/app.js` の `setTimeout(..., 3000)`
- `static/css/style.css` の `loaderSpin` / `ballPulse`
