# タロット個別画像の追加方法

画像は下記ファイル名で `static/img/` へ配置します。結果画面の誕生・魂・今日・橋渡しカードに自動で対応画像を表示します。計算は変わりません。

- WebP形式、縦横比2:3を推奨（例：400×600px）。containで表示し切り落としません。
- 未配置は `oracle-tarot.webp` にフォールバックし「共通イメージ」と明示。v1.17.4で22枚すべての個別画像を同梱しました。
- 愚者は画像名・表示が00、計算内部では22を維持。
- 同じカードが複数の役割に出た場合は、画像は1枚にまとめ、その下に役割を併記（v1.17.5）。
- 占星術・数秘術・演出の共通画像は変更しません。
- 配置後に再生成すると反映。外部通信やCSPの緩和は不要。

|カード|ファイル|
|---|---|
|01 魔術師|static/img/tarot-01-magician.webp|
|02 女教皇|static/img/tarot-02-high-priestess.webp|
|03 女帝|static/img/tarot-03-empress.webp|
|04 皇帝|static/img/tarot-04-emperor.webp|
|05 教皇|static/img/tarot-05-hierophant.webp|
|06 恋人|static/img/tarot-06-lovers.webp|
|07 戦車|static/img/tarot-07-chariot.webp|
|08 力|static/img/tarot-08-strength.webp|
|09 隠者|static/img/tarot-09-hermit.webp|
|10 運命の輪|static/img/tarot-10-wheel-of-fortune.webp|
|11 正義|static/img/tarot-11-justice.webp|
|12 吊るされた男|static/img/tarot-12-hanged-man.webp|
|13 死神|static/img/tarot-13-death.webp|
|14 節制|static/img/tarot-14-temperance.webp|
|15 悪魔|static/img/tarot-15-devil.webp|
|16 塔|static/img/tarot-16-tower.webp|
|17 星|static/img/tarot-17-star.webp|
|18 月|static/img/tarot-18-moon.webp|
|19 太陽|static/img/tarot-19-sun.webp|
|20 審判|static/img/tarot-20-judgement.webp|
|21 世界|static/img/tarot-21-world.webp|
|00 愚者|static/img/tarot-00-fool.webp|

## v1.17.4 同梱画像

内蔵image_genで制作。濃紺と金の共通画風で、正面・左・右・俯き・対面など視線を分散しました。スマホ配信用は768×1152pxのWebP、元PNGは作業フォルダーtarot_artwork/originalsに保存しています。左右反転や構図の切り抜きは行っていません。

全画像の一覧はtarot_gallery.html、各生成プロンプト・ファイルのSHA-256はtarot_image_prompts.jsonを参照してください。画像追加のみで数字生成の計算・順序・採点には変更ありません。
