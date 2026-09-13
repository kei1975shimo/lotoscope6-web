# セキュリティ方針 v1.16.0

## 実装

- 生年月日・生成結果をDBやCSVへ保存しない。Cookieの内容はCSRFトークンのみ。
- プレビューもPOSTに統一。通常操作で生年月日をURLに載せない。
- HTMLとJSONは `Cache-Control: no-store`。
- 本番は `SECRET_KEY` 必須、CookieはSecure / HttpOnly / SameSite=Lax。
- CSRF付きの生成・プレビュー。非ASCIIの偽トークンも400として処理。
- 送信サイズ256KiB、最大10口。入力はサーバーでも検証。
- `style-src 'self'` / `script-src 'self'` のCSP。インラインCSS/JSと外部配信フォントは不使用。
- フレーム埋め込み禁止、MIMEの推測防止、カメラ・マイク・位置情報を禁止。
- レート制限に排他ロック・単調時刻・期限切れ清掃を使用。429にはRetry-Afterを付与。

## IPの信用境界

転送ヘッダーの先頭を直接読む処理は削除しました。
ローカル・直接接続は `TRUSTED_PROXY_HOPS=0` とし、X-Forwarded-Forを無視します。
信頼できるリバースプロキシ経由だけで公開される構成では、そのプロキシが設定するヘッダー値の数を指定し、WerkzeugのProxyFixを経て `request.remote_addr` を使います。
X-Forwarded-Host・Proto・Port・Prefixはこのアプリでは信用しません。

同梱のRender設定は `TRUSTED_PROXY_HOPS=1` です。`RENDER=true` の場合も未指定時の既定値は1、それ以外は0です。
本作業では利用中のRenderの実際の経路は確認していません。「どの環境も必ず単段」とは扱わず、CDN等を追加している場合は実際の転送経路に合わせて設定してください。アプリ本体への直接接続を許したまま、転送ヘッダーを信用してはいけません。

偽装した先頭値＋固定の末尾クライアントIPの試験、および直接接続で偽装ヘッダーだけを変える試験は、どちらも4回成功後、5回目から429になることを確認しています。

設定の根拠：[Flaskのプロキシ設定](https://flask.palletsprojects.com/en/stable/deploying/proxy_fix/)、[Werkzeug ProxyFix](https://werkzeug.palletsprojects.com/en/stable/middleware/proxy_fix/)。信頼するプロキシ数は実際の構成と一致させる必要があります。

## 運用上の限界

簡易レート制限はメモリ上にあり、再起動で消えます。同梱のGunicorn設定は1ワーカー・4スレッドです。
複数ワーカー／複数インスタンスでは制限状態が共有されないため、Redis等へ移す必要があります。DDoS対策を置き換えるものではありません。

生年月日は計算と再確認フォームのため、通信本文と一時的なメモリ・DOMには存在します。プロキシや独自の監視機能でPOST本文を記録する設定は使用しないでください。
結果の点数は当せん確率ではありません。
