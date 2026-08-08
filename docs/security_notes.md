# セキュリティ方針 v1.9.2

## 実装済み

- 生成結果・生年月日をサーバー側のDBやCSVへ保存しない
- 本番環境では `SECRET_KEY` 未設定時に起動停止
- POSTフォームにCSRFトークンを使用
- IP単位の簡易レート制限
- 送信サイズを256KBに制限
- 1回の生成は最大10口
- Flask debugはOFF
- `HttpOnly` / `SameSite=Lax` Cookie
- 本番環境では `Secure` Cookie
- `Content-Security-Policy`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy` でカメラ・マイク・位置情報を無効化

## 補足

現在の公開版は、過去の抽せんCSV・数字別統計・答え合わせ機能を使用しません。
数字生成は、生年月日と生成日の七天体から作る星読みプロフィールを使います。

## 将来追加する場合の候補

- Redis等を利用した分散環境向けレート制限
- ログ監視
- DBや会員機能を導入する場合の認証・ユーザー分離
