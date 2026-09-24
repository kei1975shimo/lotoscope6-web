from __future__ import annotations

from datetime import date, datetime
import hashlib
from oracle_mapping import finish_profile
from typing import Any, Dict, List, Mapping

from astrology_numbers import JST, calculate_astrology_profile

DIVINATIONS: Dict[str, Dict[str, Any]] = {
    "astrology": {
        "divination_id": "astrology",
        "name": "西洋占星術",
        "short_name": "占星術",
        "english": "ASTROLOGY",
        "symbol": "✦",
        "badge": "七天体と星座の響き",
        "description": "誕生日と生成日の七天体を重ね、星の配置から数字を導きます。",
        "button_label": "星の導きを受け取る",
    },
    "kabbalah": {
        "divination_id": "kabbalah",
        "name": "カバラ数秘術",
        "short_name": "数秘術",
        "english": "KABBALAH",
        "symbol": "✡",
        "badge": "誕生日を数へ還元",
        "description": "生年月日を基礎数へ還元し、複数の数秘サイクルから数字を導きます。",
        "button_label": "数秘の導きを受け取る",
    },
    "tarot": {
        "divination_id": "tarot",
        "name": "タロット",
        "short_name": "タロット",
        "english": "TAROT",
        "symbol": "☾",
        "badge": "大アルカナ22枚の導き",
        "description": "大アルカナを混ぜ、四枚のカードを開いて今日の数字を導きます。",
        "button_label": "カードの導きを受け取る",
    },
}

DIVINATION_ORDER = ["astrology", "kabbalah", "tarot"]

TAROT_MAJOR = [
    (1, "魔術師", "意志・始まり"),
    (2, "女教皇", "直感・静けさ"),
    (3, "女帝", "実り・創造"),
    (4, "皇帝", "秩序・安定"),
    (5, "教皇", "知恵・伝統"),
    (6, "恋人", "選択・調和"),
    (7, "戦車", "前進・勝負"),
    (8, "力", "勇気・持続"),
    (9, "隠者", "探求・内省"),
    (10, "運命の輪", "転機・循環"),
    (11, "正義", "均衡・判断"),
    (12, "吊るされた男", "視点・受容"),
    (13, "死神", "変化・再生"),
    (14, "節制", "調整・融合"),
    (15, "悪魔", "欲望・引力"),
    (16, "塔", "突破・刷新"),
    (17, "星", "希望・導き"),
    (18, "月", "感覚・揺らぎ"),
    (19, "太陽", "活力・成功"),
    (20, "審判", "目覚め・決断"),
    (21, "世界", "完成・統合"),
    (22, "愚者", "自由・可能性"),
]

# Display/artwork numbering only: the generator still uses 22 for the Fool.
TAROT_IMAGE_SLUGS = (
    "fool", "magician", "high-priestess", "empress", "emperor", "hierophant",
    "lovers", "chariot", "strength", "hermit", "wheel-of-fortune", "justice",
    "hanged-man", "death", "temperance", "devil", "tower", "star", "moon",
    "sun", "judgement", "world",
)
TAROT_IMAGE_FILES = tuple(f"img/tarot-{n:02d}-{slug}.webp" for n, slug in enumerate(TAROT_IMAGE_SLUGS))


def divination_choices() -> List[Dict[str, Any]]:
    return [dict(DIVINATIONS[item_id]) for item_id in DIVINATION_ORDER]


def get_divination(divination_id: str) -> Dict[str, Any]:
    try:
        return dict(DIVINATIONS[divination_id])
    except KeyError as exc:
        raise ValueError("西洋占星術・カバラ数秘術・タロットから占いを選んでください。") from exc


def _fold43(value: int) -> int:
    return ((int(value) - 1) % 43) + 1


def _digit_sum(value: int | str) -> int:
    return sum(int(ch) for ch in str(value) if ch.isdigit())


def _reduce_number(value: int, preserve_masters: bool = True) -> int:
    value = abs(int(value))
    if value == 0:
        return 0
    while value > 9:
        if preserve_masters and value in {11, 22, 33}:
            return value
        value = _digit_sum(value)
    return value


def _unique(values: List[int], wanted: int = 12) -> List[int]:
    result: List[int] = []
    seen: set[int] = set()
    for value in values:
        folded = _fold43(value)
        if folded in seen:
            continue
        seen.add(folded)
        result.append(folded)
        if len(result) >= wanted:
            break
    cursor = 1
    while len(result) < wanted:
        if cursor not in seen:
            seen.add(cursor)
            result.append(cursor)
        cursor += 1
    return result


def _add_weight(weights: Dict[int, float], number: int, score: float) -> None:
    number = _fold43(number)
    weights[number] = max(float(score), float(weights.get(number, 0.0)))


def _base_profile(birth_date: date, target_date: date, method: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "method_id": method["divination_id"],
        "method_name": method["name"],
        "method_short_name": method["short_name"],
        "method_english": method["english"],
        "method_symbol": method["symbol"],
        "birth_date": birth_date.isoformat(),
        "birth_date_ja": f"{birth_date.year}年{birth_date.month}月{birth_date.day}日",
        "target_date": target_date.isoformat(),
        "target_date_ja": f"{target_date.year}年{target_date.month}月{target_date.day}日",
    }


def _astrology_profile(birth_date: date, target_date: date) -> Dict[str, Any]:
    raw = calculate_astrology_profile(birth_date, target_date)
    method = get_divination("astrology")
    raw.update(_base_profile(birth_date, target_date, method))
    raw["reading_title"] = "この数字へつながった星読み"
    raw["reading_kicker"] = "CELESTIAL READING"
    raw["reason_source"] = "誕生の日と今日の七天体"
    raw["boost_rows"] = []
    raw["summary_items"] = [
        {"symbol": raw["sun_sign_symbol"], "label": "太陽星座", "value": raw["sun_sign"], "detail": "生まれた日の太陽"},
        {"symbol": raw["moon_sign_symbol"], "label": "月星座", "value": raw["moon_sign"], "detail": "生まれた日の月"},
        {"symbol": raw["current_sun_sign_symbol"], "label": "生成日の太陽", "value": raw["current_sun_sign"], "detail": "今日の太陽星座"},
    ]
    raw["detail_rows"] = [
        {
            "symbol": row["symbol"],
            "title": row["planet_name"],
            "line1": f"生まれた日の正午（日本時間） {row['birth_sign_symbol']} {row['birth_sign']} {row['birth_degree']}°",
            "line2": f"生成日の正午（日本時間） {row['current_sign_symbol']} {row['current_sign']} {row['current_degree']}°",
            "line3": "正午の星位置です。成立したアスペクトは下に記載します。",
        }
        for row in raw.get("planet_rows", [])
    ]
    raw['detail_rows'].extend(
        dict(symbol='✦', title=a['label'], line1=f"角度 {a['degree']}° ／ 許容差内の誤差 {a['orb']}°",
             line2='生成日の天体と、誕生日の天体の関係', line3='許容差は6度。吉凶や当せん確率の評価ではありません。')
        for a in raw['aspect_rows'])
    return raw


def calculate_kabbalah_profile(birth_date: date, target_date: date) -> Dict[str, Any]:
    profile = _base_profile(birth_date, target_date, get_divination('kabbalah'))
    month, day, year = [_reduce_number(n) for n in (birth_date.month, birth_date.day, birth_date.year)]
    life = _reduce_number(month + day + year)
    birthday = day
    attitude = _reduce_number(birth_date.month + birth_date.day)
    py = _reduce_number(birth_date.month + birth_date.day + _digit_sum(target_date.year), False)
    pm = _reduce_number(py + target_date.month, False)
    pd = _reduce_number(pm + target_date.day, False)
    calculations = [
        ('生命数',life,f'月 {birth_date.month} → {month}、日 {birth_date.day} → {day}、年 {birth_date.year} → {year}。{month} + {day} + {year} → {life}'),
        ('誕生日数',birthday,f'{birth_date.day} → {birthday}'),
        ('態度数',attitude,f'{birth_date.month} + {birth_date.day} → {attitude}'),
        ('今年の数',py,f'{birth_date.month} + {birth_date.day} + {_digit_sum(target_date.year)}（今年の各桁の和） → {py}'),
        ('今月の数',pm,f'{py} + {target_date.month} → {pm}'),
        ('今日の数',pd,f'{pm} + {target_date.day} → {pd}')]
    profile.update(
        reading_title='この数字へつながった数秘の流れ', reading_kicker='NUMEROLOGY READING',
        reason_source='生命数・誕生日数と年・月・日の周期',
        numerology_values=dict(life_path=life,birthday=birthday,attitude=attitude,personal_year=py,personal_month=pm,personal_day=pd),
        oracle_evidence=[dict(kind='numerology',value=n,label=label) for label,n,_ in calculations],
        summary_items=[dict(symbol='✡',label=label,value=str(n),detail=detail) for label,n,detail in
                       [('生命数',life,'生年月日から導く中心数'),('誕生日数',birthday,'生まれた日に宿る数'),('今日の数',pd,'年・月・日を重ねた周期')]],
        detail_rows=[dict(symbol='✡',title=label,line1=f'導かれた数：{n}',line2=trace,
                          line3='生命数は年月日を別々に還元し11・22・33を保持。年・月・日の周期は1〜9に還元します。') for label,n,trace in calculations],
        method_note='カバラ数秘術という名称で親しまれる現代の生年月日数秘術を採用しています。ユダヤ教のカバラの伝統的解釈や姓名のゲマトリアではありません。生命数は年月日を個別に還元する方式、周期は暦年方式です。数字を各桁の和で1〜9へ還元して基礎数と照合し、同じ還元数を優先する部分は本アプリ独自のくじへの対応です。11・22・33との直接一致は重みを2倍にします。')
    return finish_profile(profile)


def _tarot_card(number: int) -> Dict[str, Any]:
    number = ((int(number) - 1) % 22) + 1
    card_number, name, keyword = TAROT_MAJOR[number - 1]
    display = "0" if card_number == 22 else str(card_number)
    return {"number": card_number, "display_number": display, "name": name, "keyword": keyword,
            "image_filename": TAROT_IMAGE_FILES[int(display)]}


def calculate_tarot_profile(birth_date: date, target_date: date) -> Dict[str, Any]:
    profile = _base_profile(birth_date, target_date, get_divination('tarot'))
    # Daily deterministic shuffle without replacement. Birth/date personalize
    # the shuffle; they are not arithmetic assignments of named cards.
    seed = f'tarot-spread-v1|{birth_date.isoformat()}|{target_date.isoformat()}'
    deck = sorted(range(1,23), key=lambda n:(hashlib.sha256(f'{seed}|{n}'.encode()).digest(),n))
    roles = [('現在','いまの状況を映すカード'),('課題','向き合うテーマ'),('助言','意識したい姿勢'),('向かう先','これからの可能性')]
    cards = [dict(_tarot_card(n),role=role,description=description) for n,(role,description) in zip(deck,roles)]
    evidence = []
    for card in cards:
        evidence.append(dict(kind='arcana',value=card['number'],label=f"{card['role']}・{card['name']}"))
        # Explicit app adaptation, including Fool 22 + 22 = 44 -> 1 for Loto6.
        evidence.append(dict(kind='arcana',value=card['number']+22,label=f"{card['name']}の影（+22）",strength=0.5))
    for i,card in enumerate(cards):
        for other in cards[i+1:]:
            evidence.append(dict(kind='arcana',value=card['number']+other['number'],
                                 label=f"{card['name']}＋{other['name']}",strength=0.5))
    profile.update(
        tarot_cards=cards,oracle_evidence=evidence,
        reading_title='四枚のカードが伝える導き',reading_kicker='FOUR CARD READING',
        reason_source='今回開いた四枚の大アルカナ',
        summary_items=[dict(symbol='☾',label=c['role'],value=c['name'],detail=c['keyword']) for c in cards[:3]],
        detail_rows=[dict(symbol='☾',title=c['role'],line1=c['name'],line2=c['keyword'],line3=c['description']) for c in cards],
        method_note='大アルカナ22枚を混ぜ、重複なく四枚を引きます。すべて正位置として読む方式です。「現在・課題・助言・向かう先」の配置は本アプリ独自の四枚展開です。同じ誕生日と日本時間の日付では同じ並びを再現します。カード番号（愚者は対応計算では22）、22を足す影の数字、二枚の番号の和を券種の範囲で循環させます。この数字への展開は独自ルールで、ロト6では23〜43も候補になります。')
    return finish_profile(profile)


def calculate_divination_profile(divination_id: str, birth_date: date, target_date: date | None = None) -> Dict[str, Any]:
    current_date = target_date or datetime.now(JST).date()
    get_divination(divination_id)
    if divination_id == "kabbalah":
        return calculate_kabbalah_profile(birth_date, current_date)
    if divination_id == "tarot":
        return calculate_tarot_profile(birth_date, current_date)
    return _astrology_profile(birth_date, current_date)
