# 既存のRenderサイトをv1.16.0へ更新

このZIPは更新用のファイル一式です。今回の作業では公開中のRenderサイトには反映していません。

1. 現在のリポジトリをバックアップします。
2. ZIPを展開し、`app.py` がある階層のファイルを既存リポジトリへ反映します。`templates/`、`static/`、`src/`も一式更新します。
3. 旧版の `src/utils.py`、`static/img/cosmic-zodiac-wheel.webp`、`PUBLISH_STEPS_JA.md` を削除します。もしさらに古いCSV分析・答え合わせ用ファイルを残している場合は、現行構成で参照されていないことを確認して削除します。
4. Renderの環境変数を確認します。

| 項目 | 設定 |
|---|---|
| APP_ENV | production |
| SECRET_KEY | 設定済みの秘密鍵を維持。未設定なら新規生成 |
| RATE_LIMIT_PER_MINUTE | 30 |
| TRUSTED_PROXY_HOPS | 1（本ZIPに含む構成。実際の転送経路に合わせる） |

5. Build Commandを `pip install -r requirements.txt`、Start Commandを `gunicorn --workers 1 --threads 4 app:app` にします。
6. Gitへコミット・pushし、Renderのデプロイ完了を待ちます。
7. `/health` が `OK` になり、画面下部に `v1.16.0-mystic-oracle` が出ることを確認します。
8. 占い3種類、くじ5種類、再確認ボタンを操作します。同じ条件で1口・3口・10口を比較し、先頭と順番が一致することを確認します。

`render.yaml`を使った新規作成でも同じ構成になります。既存サービスでは、ファイルを置くだけで環境変数やStart Commandが更新されるとは限らないため、ダッシュボードも確認します。

プロキシの設定は `docs/security_notes.md` を参照してください。Renderの前に別のCDNやプロキシを追加した場合、構成を再確認します。
レート制限は1プロセス内で共有します。複数ワーカー・複数インスタンスへ拡張する際は、Redis等の共有ストアが必要です。

プレビューAPIはGETからPOSTへ変更されています。古いHTML/JSを混在させず、同じ版のファイルをまとめて反映してください。
