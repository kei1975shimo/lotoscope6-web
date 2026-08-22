# v1.13.1 Cleanup Report

現行 v1.13.0 の見た目・操作・生成ロジックを維持したまま、静的に参照されないコードだけを整理しました。

- CSS: 使用不能なセレクタルールを 361 件削除
- CSS: グループセレクタ内の未使用分岐を 77 件削除
- JavaScript: 現在のテンプレートに存在しない旧サマリーDOM向け更新処理と、口数変更時の不要なUI再計算を削除
- HTML: JavaScript/CSSから参照されない data-product-rule / data-product-kind / data-product-count / data-astrology-entry / data-astrology-fields / data-birth-part / data-result-product を削除
- Pythonの生成ロジック、星読みロジック、ルーティング、CSRF、レート制限は未変更
- 現行テンプレート上の表示部品は削除していません

## v1.13.3 ヘッダー星座盤化
- ヘッダー右側の「公開中」表示を削除。
- 同位置に既存 `cosmic-zodiac-wheel.webp` を使った回転式の星座盤を追加。
- 星座盤はスマホ標準で約88px（狭幅では76px）に設定。
- トップページの従来ヒーローをHTMLから完全に削除。
- トップはヘッダーから直接「ロトを選ぶ」パネルへ続く構成に変更。
- 生成ロジック、入力仕様、結果画面の機能は変更していません。
