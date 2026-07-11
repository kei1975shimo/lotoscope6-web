# セキュリティ方針 v1.0.13

## 実装済みの対策

- Flask公開用構成に分離
- サーバー側に生成結果を保存しない
- 照合時に任意CSVパスを受け取らない
- 生成結果は署名付き・期限付きトークンで一時的に受け渡し
- 本番環境では `SECRET_KEY` 未設定時に起動停止
- POSTフォームにCSRFトークンを追加
- IP単位の簡易レート制限を追加
- 好きな数字・避けたい数字は各5個まで
- 数字は1〜43に正規化
- 1回の口数は最大10口まで
- Flask debugはOFF
- `X-Content-Type-Options: nosniff` を付与
- `X-Frame-Options: DENY` を付与
- `Referrer-Policy: strict-origin-when-cross-origin` を付与
- `.gitignore`で `.env` や `__pycache__` などを除外

## 今後追加する候補

- Redisなど外部ストアを使った本格的なレート制限
- ログ監視
- 管理画面の認証
- 会員登録時のセッション管理
- DB導入時のユーザー分離
- 抽せん結果CSVの自動更新処理
