from __future__ import annotations

from datetime import date, datetime
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
        "description": "生年月日と今日を大アルカナへ対応させ、カードの数字から候補を導きます。",
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
    raw["boost_rows"] = raw.get("planet_rows", [])
    raw["summary_items"] = [
        {"symbol": raw["sun_sign_symbol"], "label": "太陽星座", "value": raw["sun_sign"], "detail": "生まれた日の太陽"},
        {"symbol": raw["moon_sign_symbol"], "label": "月星座", "value": raw["moon_sign"], "detail": "生まれた日の月"},
        {"symbol": raw["current_sun_sign_symbol"], "label": "生成日の太陽", "value": raw["current_sun_sign"], "detail": "今日の太陽星座"},
    ]
    raw["detail_rows"] = [
        {
            "symbol": row["symbol"],
            "title": row["planet_name"],
            "line1": f"出生時 {row['birth_sign_symbol']} {row['birth_sign']} {row['birth_degree']}°",
            "line2": f"生成日 {row['current_sign_symbol']} {row['current_sign']} {row['current_degree']}°",
            "line3": f"{row['aspect_name']} {row['aspect_degree']}°への誤差 {row['orb']}°",
        }
        for row in raw.get("planet_rows", [])
    ]
    return raw


def calculate_kabbalah_profile(birth_date: date, target_date: date) -> Dict[str, Any]:
    method = get_divination("kabbalah")
    profile = _base_profile(birth_date, target_date, method)

    ymd_digits = birth_date.strftime("%Y%m%d")
    life_path = _reduce_number(_digit_sum(ymd_digits))
    birthday = _reduce_number(birth_date.day)
    attitude = _reduce_number(birth_date.month + birth_date.day)
    birth_year = _reduce_number(_digit_sum(birth_date.year))
    personal_year = _reduce_number(birth_date.month + birth_date.day + _digit_sum(target_date.year))
    personal_month = _reduce_number(personal_year + target_date.month)

    bases = [life_path, birthday, attitude, birth_year, personal_year, personal_month]
    labels = [
        ("生命数", life_path, "生年月日全体から導く中心数"),
        ("誕生日数", birthday, "生まれた日の性質"),
        ("態度数", attitude, "月と日を合わせた表現の数"),
        ("誕生年数", birth_year, "生まれた年の基礎振動"),
        ("パーソナルイヤー", personal_year, "今年の流れを示す数"),
        ("パーソナルマンス", personal_month, "今月の流れを示す数"),
    ]

    seed = int(birth_date.strftime("%Y%m%d"))
    today_seed = int(target_date.strftime("%Y%m%d"))
    candidate_values: List[int] = []
    weights: Dict[int, float] = {}
    boost_rows: List[Dict[str, Any]] = []

    for index, base in enumerate(bases, start=1):
        primary = _fold43(base)
        secondary = _fold43(base * (index + 2) + birth_date.month + birth_date.day)
        tertiary = _fold43(base * 7 + _digit_sum(seed) * index + _digit_sum(today_seed))
        resonance = max(45.0, 108.0 - index * 6.0 + (8.0 if base in {11, 22, 33} else 0.0))
        boost_rows.append(
            {
                "resonance": resonance,
                "primary_candidate": primary,
                "secondary_candidate": secondary,
                "tertiary_candidate": tertiary,
            }
        )
        candidate_values.extend([primary, secondary, tertiary])
        _add_weight(weights, primary, 120 - index * 5)
        _add_weight(weights, secondary, 92 - index * 4)
        _add_weight(weights, tertiary, 75 - index * 3)
        _add_weight(weights, primary - 1, 42)
        _add_weight(weights, primary + 1, 42)

    candidate_values.extend(
        [
            _fold43(seed),
            _fold43(_digit_sum(seed) * 11),
            _fold43(birth_date.month * 9 + birth_date.day * 4),
            _fold43(today_seed),
            _fold43(personal_year * 13 + target_date.day),
        ]
    )
    core_numbers = _unique(candidate_values, wanted=6)
    for rank, number in enumerate(core_numbers, start=1):
        _add_weight(weights, number, 118 - rank * 4)

    pool_numbers = [number for number, _ in sorted(weights.items(), key=lambda item: (-item[1], item[0]))]
    pool_numbers = _unique(pool_numbers + candidate_values, wanted=24)

    profile.update(
        {
            "core_numbers": sorted(core_numbers),
            "pool_numbers": pool_numbers,
            "weights": weights,
            "boost_rows": boost_rows,
            "reading_title": "この数字へつながったカバラ数秘術",
            "reading_kicker": "KABBALAH NUMEROLOGY",
            "reason_source": "生年月日から導いた数秘術の基礎数と今日の周期数",
            "summary_items": [
                {"symbol": "Ⅰ", "label": "生命数", "value": str(life_path), "detail": "人生の中心となる数"},
                {"symbol": "◇", "label": "誕生日数", "value": str(birthday), "detail": "生まれた日に宿る数"},
                {"symbol": "↻", "label": "今年の数", "value": str(personal_year), "detail": f"{target_date.year}年の周期"},
            ],
            "detail_rows": [
                {"symbol": "✡", "title": label, "line1": f"導かれた数：{value}", "line2": detail, "line3": "マスターナンバー11・22・33は途中で一桁化せず扱います。" if value in {11, 22, 33} else "1〜9の基礎数として数字候補へ展開します。"}
                for label, value, detail in labels
            ],
            "method_note": (
                "数秘術には複数の流派があります。本アプリでは、生年月日を使う簡易的なカバラ数秘術風の方式として、"
                "生命数・誕生日数・態度数・年周期などを1〜43の候補へ展開しています。"
            ),
        }
    )
    return profile


def _tarot_card(number: int) -> Dict[str, Any]:
    number = ((int(number) - 1) % 22) + 1
    card_number, name, keyword = TAROT_MAJOR[number - 1]
    display = "0" if card_number == 22 else str(card_number)
    return {"number": card_number, "display_number": display, "name": name, "keyword": keyword}


def calculate_tarot_profile(birth_date: date, target_date: date) -> Dict[str, Any]:
    method = get_divination("tarot")
    profile = _base_profile(birth_date, target_date, method)

    birth_sum = _digit_sum(birth_date.strftime("%Y%m%d"))
    target_sum = _digit_sum(target_date.strftime("%Y%m%d"))
    birth_arcana = ((birth_sum - 1) % 22) + 1
    soul_arcana = ((_reduce_number(birth_sum, preserve_masters=False) + birth_date.month + birth_date.day - 1) % 22) + 1
    day_arcana = ((birth_arcana + target_sum + target_date.day - 1) % 22) + 1
    bridge_arcana = ((birth_arcana + day_arcana + birth_date.day - 1) % 22) + 1

    card_defs = [
        ("誕生カード", _tarot_card(birth_arcana), "生年月日全体から開くカード"),
        ("魂のカード", _tarot_card(soul_arcana), "誕生日の基礎数から開くカード"),
        ("今日のカード", _tarot_card(day_arcana), "誕生カードと生成日を重ねたカード"),
        ("橋渡しカード", _tarot_card(bridge_arcana), "誕生と今日を結ぶ補助カード"),
    ]

    weights: Dict[int, float] = {}
    candidate_values: List[int] = []
    boost_rows: List[Dict[str, Any]] = []
    birth_seed = int(birth_date.strftime("%Y%m%d"))
    target_seed = int(target_date.strftime("%Y%m%d"))

    for index, (_label, card, _detail) in enumerate(card_defs, start=1):
        arcana = int(card["number"])
        primary = _fold43(arcana)
        secondary = _fold43(arcana * 2 + birth_date.day + index * 3)
        tertiary = _fold43(arcana * 3 + target_date.day + birth_date.month * index)
        resonance = 112.0 - index * 7.0
        boost_rows.append(
            {
                "resonance": resonance,
                "primary_candidate": primary,
                "secondary_candidate": secondary,
                "tertiary_candidate": tertiary,
            }
        )
        candidate_values.extend([primary, secondary, tertiary])
        _add_weight(weights, primary, 126 - index * 6)
        _add_weight(weights, secondary, 96 - index * 5)
        _add_weight(weights, tertiary, 79 - index * 4)
        # 大アルカナの数字を1〜43へ二巡させ、同じカードの「影」の数字も候補にする。
        _add_weight(weights, arcana + 22, 68 - index * 3)

    candidate_values.extend(
        [
            _fold43(birth_seed),
            _fold43(target_seed),
            _fold43(birth_arcana * day_arcana),
            _fold43(soul_arcana * 5 + bridge_arcana * 7),
            _fold43(_digit_sum(birth_seed) * 9 + _digit_sum(target_seed)),
        ]
    )
    core_numbers = _unique(candidate_values, wanted=6)
    for rank, number in enumerate(core_numbers, start=1):
        _add_weight(weights, number, 120 - rank * 4)

    pool_numbers = [number for number, _ in sorted(weights.items(), key=lambda item: (-item[1], item[0]))]
    pool_numbers = _unique(pool_numbers + candidate_values, wanted=24)

    profile.update(
        {
            "core_numbers": sorted(core_numbers),
            "pool_numbers": pool_numbers,
            "weights": weights,
            "boost_rows": boost_rows,
            "reading_title": "この数字へつながったタロット",
            "reading_kicker": "MAJOR ARCANA READING",
            "reason_source": "生年月日と今日から開いた大アルカナ",
            "summary_items": [
                {"symbol": "Ⅰ", "label": "誕生カード", "value": card_defs[0][1]["name"], "detail": f"Arcana {card_defs[0][1]['display_number']}"},
                {"symbol": "☾", "label": "今日のカード", "value": card_defs[2][1]["name"], "detail": f"Arcana {card_defs[2][1]['display_number']}"},
                {"symbol": "∞", "label": "橋渡し", "value": card_defs[3][1]["name"], "detail": f"Arcana {card_defs[3][1]['display_number']}"},
            ],
            "detail_rows": [
                {
                    "symbol": "☾",
                    "title": label,
                    "line1": f"{card['display_number']} · {card['name']}",
                    "line2": card["keyword"],
                    "line3": detail,
                }
                for label, card, detail in card_defs
            ],
            "method_note": (
                "タロットの誕生カード計算法には複数の方式があります。本アプリでは大アルカナ22枚を使い、"
                "生年月日と生成日の数をカードへ対応させ、その番号と組み合わせを1〜43の候補へ展開しています。"
            ),
        }
    )
    return profile


def calculate_divination_profile(divination_id: str, birth_date: date, target_date: date | None = None) -> Dict[str, Any]:
    current_date = target_date or datetime.now(JST).date()
    get_divination(divination_id)
    if divination_id == "kabbalah":
        return calculate_kabbalah_profile(birth_date, current_date)
    if divination_id == "tarot":
        return calculate_tarot_profile(birth_date, current_date)
    return _astrology_profile(birth_date, current_date)
