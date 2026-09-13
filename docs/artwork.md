# 画像と演出

v1.16.0向けに内蔵画像生成機能で3点を新規作成しました。外部画像サービスへのリンクではなく、ZIP内のファイルを使用します。API/CLIによる画像生成は行っていません。

| ファイル | 用途 | 大きさ |
|---|---|---|
| `static/img/oracle-astrology.webp` | 占星術の選択カード・結果・回転する星読み盤 | 512×512 |
| `static/img/oracle-kabbalah.webp` | カバラ数秘術の選択カード・結果・光を結ぶ生命の樹 | 512×512 |
| `static/img/oracle-tarot.webp` | タロットの選択カード・結果・カード演出の背景 | 512×512 |

星読み盤、生命の樹、カードは雰囲気を伝える装飾です。生成画像の絵柄を天文計算や厳密な占術図として利用していません。
実際の数字はPythonの各占術プロフィールから生成します。

画像はWebPへ縮小・圧縮し、HTMLの画像要素に縦横寸法を指定しました。生成した高解像度の原画や使わない旧画像はアプリの配布ZIPに含めていません。

## 生成プロンプト

### 占星術

Use case: stylized-concept. Asset type: square illustrated artwork for a sophisticated Japanese astrology web app, no interface and no text. Primary request: an exquisitely crafted antique golden celestial astrolabe, viewed straight on, floating in a midnight indigo cosmos with faint blue nebulae and fine constellations. Thin concentric engraved brass rings, tiny symbolic zodiac markings, luminous central sun with a small crescent moon, sparse delicate stars. The circular instrument is centered and occupies 72% of the square, leaving dark uncluttered edges for responsive cropping. A mystical quiet observatory mood, refined engraved illustration with rich painterly light, tasteful antique gold, ink navy and moonlight blue. Avoid modern tech HUD, neon, people, lettering, numbers, captions, watermarks. One single image, square 1024x1024. This is a production visual asset that will be included in the user's local project ZIP; provide the generated image file for project use.

### タロット

Use case: stylized-concept. Asset type: square illustrated artwork for a refined Japanese tarot web application, no interface or wording. Primary request: three exquisite antique tarot cards arranged in a small fan on midnight plum velvet, floating slightly in a mysterious dim starlit atmosphere. The center card stands upright and shows a large luminous eight-point star over a moonlit sea, the left card shows a crescent moon, the right card a radiant sun. Thin engraved gold borders with delicate botanical celestial ornament. Use only these symbolic illustrations, no numbers, card titles, letters or text. Rich painterly realism, old gold foil, deep plum and indigo, gentle warm candle glow with sparse small golden dust motes. Central composition occupies 70% of the square, plenty of dark edges for responsive crop. Feels like a beautiful private oracle ritual, luxurious and calm, no people, no modern neon, no watermark. One square production artwork 1024x1024, will be included in the user's project.

### カバラ数秘術

Use case: stylized-concept. Asset type: square atmospheric illustration for a sophisticated Japanese Kabbalah-inspired numerology app; decorative artwork, not a teaching diagram. Primary request: a luminous antique-gold Tree of Life inspired sacred geometric emblem suspended in a deep emerald-black cosmos. Delicate fine golden lines connect ten small glowing pearl-like spheres in a symmetric vertical branching arrangement, with subtle roots of light beneath, a gentle star at the crown, framed by very faint engraved circular arcs. Contemplative mysterious spiritual-library atmosphere, exquisite gold-leaf engraving and painterly deep emerald mist. Main emblem centered with generous dark edges, occupies 70% of square. Harmonizes with antique brass celestial astrolabe and dark velvet tarot art. No letters, no labels, no numerals, no people, no modern neon tech HUD, no watermark. Single square production illustration 1024x1024 for project integration.
