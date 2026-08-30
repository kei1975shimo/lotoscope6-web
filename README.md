## v1.15.0 Daily Oracle

- Same birthday + same JST date + same divination + same lottery now returns the same numbers.
- The daily result changes automatically when the JST calendar date changes.
- Ritual animation speeds no longer switch between text phases, removing visible jerks.
- Ritual copy transitions now cross-fade inside a fixed-height area without forced layout.
- UI explains the “one daily guidance” concept without storing the birthday.


- Fixed the height of the changing ritual-copy area so the loader frame no longer grows/shrinks between phases.
- Added a subtle fade/slide transition to phase text only.
- Applied the same stable layout to Astrology, Kabbalah Numerology, and Tarot animations.

## v1.14.8 Sub-number removal

- 「サブ数字」機能を削除し、生成結果を本数字だけに統一しました。
- トップ画面のサブ数字選択、結果画面のサブ数字表示、フォーム値、生成処理、関連CSS・テストを削除しました。
- 現在の入力順は「誕生日 → 占い → くじ → 口数 → 生成」です。

## v1.14.7 Text balance + mobile divination cards

- 生成アニメーションを占術ごとに専用化
  - 西洋占星術: 星座盤・惑星軌道・太陽/月の天体演出
  - カバラ数秘術: 生命の樹・セフィラ点灯・数の収束演出
  - タロット: カードシャッフル・ドロー・反転・アルカナ番号演出
- 「結果をすぐに見る」ボタンを削除
- セッション内の自動短縮演出を削除し、毎回選択した占術の演出を表示
- 旧共通コンパス演出の不要コードを削除

## v1.14.3 Hero cleanup / code cleanup

- ホームのヒーロー内にあった星座盤・軌道アニメーション等の装飾を削除しました。
- ヘッダー右側の回転する星座盤はそのまま残しています。
- 現在のHTML/JavaScriptから参照されていない旧UI用CSSを整理しました。
- Pythonの `__pycache__` / `.pyc` と、過去バージョン用の履歴ドキュメントを公開ZIPから除外しました。
- 入力順「誕生日 → 占い → くじ → 口数 → 生成」と3占術の生成ロジックは変更していません。

## v1.14.2 Header zodiac wheel

- Removed the restored `公開中` status chip from the header.
- Restored a rotating zodiac-wheel visual in the header's right-side action area.
- Kept the v1.14.1 flow: birthday → divination → lottery → entries/options → generate.
- Rotation is disabled automatically when the OS requests reduced motion.

## v1.14.1 UI flow

- 入力順を「誕生日 → 占い → くじ → 口数 → 生成」に変更しました。
- 数字生成ロジック自体は v1.14.0 から変更していません。

# ロト・スコープ 公開用Flask版 v1.15.0

西洋占星術・カバラ数秘術・タロットの3つから占いを選び、生年月日をもとに数字選択式宝くじ・ナンバーズの候補を導くWebアプリです。
現在の生成方式では、過去の抽せんデータ・コールド数字・旧バランス設定は使用しません。

## 対応している宝くじ

- ミニロト：1〜31から異なる5個
- ロト6：1〜43から異なる6個
- ロト7：1〜37から異なる7個
- ナンバーズ3：0〜9から3桁（順序あり・重複可、ボックス目安も併記）
- ナンバーズ4：0〜9から4桁（順序あり・重複可、ボックス目安も併記）

## 現在の主な構成

```text
app.py
requirements.txt
render.yaml
Procfile
config/
  app_settings.json
src/
  astrology_numbers.py
  divination_numbers.py
  product_numbers.py
  utils.py
templates/
  base.html
  index.html
  result.html
  error.html
static/
  css/style.css
  js/app.js
tests/
  smoke_test.py
```

## Windows Terminal / PowerShell で初回起動

Python 3.10以降を使用してください。`.python-version` は 3.12.7 です。

1. ZIPを展開し、Windows TerminalまたはPowerShellを開きます。
2. `cd` でこのフォルダへ移動します。
3. 次を順番に実行します。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
$env:SECRET_KEY='local-dev-secret'
python app.py
```

起動後、ブラウザで次を開きます。

```text
http://127.0.0.1:8786
```

終了するときはターミナルで `Ctrl + C` を押します。

### 2回目以降

```powershell
.\.venv\Scripts\Activate.ps1
$env:SECRET_KEY='local-dev-secret'
python app.py
```

ローカル環境では `SECRET_KEY` を設定しなくても起動できますが、公開時との違いを減らすため上記では設定しています。

### PowerShellでActivate.ps1が拒否された場合

仮想環境を有効化せず、直接Pythonを呼び出せます。

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:SECRET_KEY='local-dev-secret'
.\.venv\Scripts\python.exe app.py
```

## テスト

依存関係をインストールした状態で、次を実行します。

```powershell
python -m unittest tests.smoke_test -v
```

## Renderへの公開

`render.yaml`、`Procfile`、`requirements.txt`、`app.py` を含むフォルダ全体をデプロイします。
本番では `APP_ENV=production` と `SECRET_KEY` が必要です。`render.yaml` は `SECRET_KEY` を自動生成する設定です。

## 星読みについて

出生時刻と出生地を使わない簡易星読みです。生年月日と生成日の正午（日本時間）における太陽、月、水星、金星、火星、木星、土星の位置と主要アスペクトを、選んだロトの数字範囲へ変換します。

生成結果や点数は、数字選びを楽しむための独自の目安です。当せん確率や当せんを保証するものではありません。


## v1.9.7
生年月日の太陽星座を大きな星座記号と12星座のシンボル列で表示し、結果画面の太陽・月・生成日の太陽にも星座記号を追加しました。


## v1.9.8

UIを「古い星図・天球儀・占星術盤」の意匠へ寄せたCelestial Patterns版です。

- 画像を背景として貼らず、星座盤・幾何学線・装飾枠をHTML/CSSで描画
- スマホのヒーローに薄い12星座リングと星図線を追加
- ミニロト／ロト6／ロト7のスイッチ左側に券種別の天体シンボルを追加
- 誕生日欄に薄い星座盤パターンを追加
- 生成ボタンを金色のオラクル風デザインへ強化
- 結果画面にも同じ星図・金線の意匠を適用
- 縦方向のレイアウト寸法は大きく増やさず、装飾を主に背景・重ね描画で実装


## v1.9.9

ナンバーズ3・ナンバーズ4を星読み対応の新規実装として追加しました。

- 券種スイッチにナンバーズ3・ナンバーズ4を追加
- 桁ごとに星の重みを畳み込んで抽選する専用の生成ロジックを実装
- 結果はストレート（生成順）を主表示、ボックス（並べ替え）を参考情報として併記
- 結果画面・読み込み演出とも、既存CSSのデザイン言語（`.digit-tile`／星読盤／星の門）を使用


## v1.10.0

配色を「ダーク×ゴールド」から「深い青紫・オーロラ調」へ一新しました（ボタンの構造・機能は変更なし）。

- 星座・惑星シンボルは維持しつつ、光・線・グラデーションで神秘性を強化
- 5券種のテーマカラーをオーロラスペクトラム（氷青／紫〜マゼンタ／ティーン／藍紫／ローズ）へ再構成
- ヒーローに「オーロラ・リボン」のグラデーションSVGを新規追加
- 背景にゆっくり揺らめくオーロラの光アニメーションを追加（reduced-motion対応）


## v1.10.1

「背景の動く宇宙」と「手前のガラス状カード」の2層構造で、重なり感・立体感を追加しました。

- 固定背景レイヤーに、漂う星雲と瞬く星（32個）を追加。スクロールしても背景はその場に留まり視差を生む
- ヒーロー・パネル類に `backdrop-filter: blur()` と半透明の背景を適用し、磨りガラス調に
- 影を強化してカードが宇宙背景から浮き上がって見えるように調整


## v1.10.2

v1.10.1の効果が控えめすぎたため、スクロールしなくても最初の画面から分かるレベルへ強化しました。

- 星雲を3個に増やし、不透明度・彩度・サイズを大幅強化
- 星の明るさ・サイズを拡大
- パネル類の背景をより透過させ、磨りガラス越しの色がはっきり見えるように調整
- モバイルで星雲の中心がずれていた不具合を修正


## v1.10.3

ヒーロー内だけにあった流れ星のような光の線を、固定の宇宙背景レイヤーへ移し、画面全体を斜めに横切るように拡張しました。

- 紫・ティーン・ローズの3本の光の筋が、それぞれ異なる速さ・向きで画面を流れる
- カードの背後を通る部分は磨りガラス越しにぼんやり透け、隙間では鮮明に見える
- ヒーロー内に限定されていた旧バージョンの流れ星エフェクトは削除（全画面版に統合）


## v1.10.4

CSSで描画していた星雲・流れ星・瞬く星の宇宙背景を、金線の12星座早見盤イラスト1枚に置き換えました。

- 固定背景レイヤー（`.cosmic-field`）の背景をイラスト画像（WebP、`static/img/cosmic-zodiac-wheel.webp`）に変更
- 画像の上に暗めのグラデーションオーバーレイを重ね、磨りガラス調カードや文字の可読性を確保
- 星雲ドリフト・流れ星・瞬く星のCSSアニメーション／SVGを削除し、`body::before`／`::after` の点描・オーロラ演出も整理
- 静的な1枚絵のため `prefers-reduced-motion` 環境への配慮も自然に達成


## v1.10.5

ヘッダー・ヒーロー・フォームパネル・カード・入力欄・結果画面パネルなど各部品の背景を透過し、背後の12星座早見盤イラストがより見えるようにしました。

- ヘッダー（`.app-bar`）、フォームパネル（`.panel`）、券種カード（`.mode-card`／`.product-card`）、入力欄（`input`）、数字タイル（`.digit-tile`）、結果画面の星読みレポート（`.astrology-report`）や星座サマリー・生年月日カードなど、主要な部品の背景不透明度を全体的に引き下げ
- 透過度を上げた分、各部品には磨りガラス効果（`backdrop-filter: blur()`）を付与・強化し、文字の可読性を確保
- 読み込み中に全画面表示される演出用オーバーレイ（`.draw-loader`など）は、可読性・演出の観点からそのまま維持


## v1.10.6

各部品の背景をさらに透過し、12星座早見盤イラストがはっきり見えるようにしました。

- v1.10.5で設定した各部品の背景不透明度を、おおむね半分程度までさらに引き下げ
- 透過度を上げた分、磨りガラス効果（`backdrop-filter: blur()`）の強さを各部品でさらに増し、文字の可読性を確保


## v1.10.7

透過がまだ不十分だったため、大幅に強化しました。

- 背景画像の上に重ねていた暗いオーバーレイ（`.cosmic-field::before`）自体が濃かったのが主な原因だったため、これを大幅に薄く（端で最大.86だったものを.26程度まで）変更
- 各部品の背景も、うっすらとした色味だけが残る程度（アルファ0.05〜0.16程度）までさらに引き下げ
- `backdrop-filter`のぼかし量を全体的に増やし（16px〜34px）、薄い背景でも文字の可読性を維持


## v1.10.8

さらに透過を強め、ほぼ全部品を背景色なし・ぼかしのみの状態にしました。

- `.cosmic-field::before`の暗いオーバーレイをほぼ気配程度（アルファ最大.09）まで縮小
- 各部品の背景アルファを0.02〜0.07程度まで低減し、色味はほぼ枠線・シャドウのアクセントのみが残る状態に
- `backdrop-filter`のぼかしを20px〜38pxまでさらに強化し、可読性は主にぼかしのみで確保




## v1.12.0

同じ数字を呼び出す「合言葉」機能を削除し、数字生成中のローディングアニメーションを全面刷新しました。

- 合言葉（seed）欄をトップ画面のフォームから削除。結果画面の「同じ条件でもう一度」ボタンも常に「星を読み直して、新しい数字を導く」表示に統一
- 券種ごとに個別デザインだった生成中演出（月と蓮、六芒星、七惑星軌道、星読み盤、星の門）を廃止し、全券種共通の新しい演出「セレスチャル・コンパス」に一新
- 三重の回転リング（実線・破線・点線）、12個の目盛り、3つの軌道を回る光点、中央のコアに券種のシンボル（☾・✡・Ⅶ・☿・♀）を動的表示する脈動演出、二重のパルスリングで構成
- 進捗バー・フェーズ表示テキスト・スキップボタンなどの既存の演出ロジックはそのまま維持
- `prefers-reduced-motion`環境向けのアニメーション停止対応も新デザインに合わせて更新



## v1.14.0

- 最初に「西洋占星術 / カバラ数秘術 / タロット」から占いを選ぶStepを追加
- 画面の流れを「占い → くじ → 誕生日 → 口数 → 生成」に変更
- カバラ数秘術：生命数、誕生日数、態度数、誕生年数、パーソナルイヤー、パーソナルマンスから重みを生成
- タロット：大アルカナ22枚を使い、誕生カード・魂のカード・今日のカード・橋渡しカードから重みを生成
- 結果画面を占術共通化し、選んだ占術ごとの読み解き・中心数字を表示
- 生成中アニメーションの文言も選択した占術に連動

> 数秘術・タロットには複数の流派・計算法があります。本アプリは宝くじの数字選びを楽しむための独自の簡易変換方式です。

## v1.13.0

「ロトを選ぶ」ボタンを、横並びのスイッチ行からアイコン＋ラベルのタイル型ボタンへ一新しました。

- 5券種を3列（画面幅が広い場合は5列）のグリッドに並べ、アイコンを上・名称を下に配置したタイルボタンに変更
- 未選択タイルは枠線・アイコン・文字を控えめに、選択中のタイルは白い枠線とアクセントカラーのグロー（にじみ）で強調する、セグメントコントロール風の見た目に
- 右側にあったトグルスイッチ（丸いつまみ）は廃止し、タイル全体の枠線とグローだけで選択状態を示すように統一
