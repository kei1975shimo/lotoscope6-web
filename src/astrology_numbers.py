from __future__ import annotations

import math
from datetime import date, datetime, time, timezone
from typing import Any, Dict, Iterable, List, Sequence, Tuple
from zoneinfo import ZoneInfo

import ephem

JST = ZoneInfo("Asia/Tokyo")
ZODIAC_SIGNS = [
    "牡羊座",
    "牡牛座",
    "双子座",
    "蟹座",
    "獅子座",
    "乙女座",
    "天秤座",
    "蠍座",
    "射手座",
    "山羊座",
    "水瓶座",
    "魚座",
]
ZODIAC_SYMBOLS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
ZODIAC_ENGLISH = [
    "ARIES",
    "TAURUS",
    "GEMINI",
    "CANCER",
    "LEO",
    "VIRGO",
    "LIBRA",
    "SCORPIO",
    "SAGITTARIUS",
    "CAPRICORN",
    "AQUARIUS",
    "PISCES",
]

PLANETS: Sequence[Tuple[str, str, type, int]] = (
    ("sun", "太陽", ephem.Sun, 16),
    ("moon", "月", ephem.Moon, 15),
    ("mercury", "水星", ephem.Mercury, 9),
    ("venus", "金星", ephem.Venus, 10),
    ("mars", "火星", ephem.Mars, 8),
    ("jupiter", "木星", ephem.Jupiter, 12),
    ("saturn", "土星", ephem.Saturn, 11),
)

PLANET_SYMBOLS = {
    "sun": "☉",
    "moon": "☾",
    "mercury": "☿",
    "venus": "♀",
    "mars": "♂",
    "jupiter": "♃",
    "saturn": "♄",
}

MAJOR_ASPECTS: Sequence[Tuple[int, str]] = (
    (0, "合"),
    (60, "六分"),
    (90, "矩"),
    (120, "三分"),
    (180, "衝"),
)


def parse_birth_date(value: str, today: date | None = None) -> date:
    text = str(value or "").strip()
    if not text:
        raise ValueError("星読みを使う場合は、生年月日を西暦で入力してください。")
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("生年月日は西暦の年月日で入力してください。") from exc

    current = today or datetime.now(JST).date()
    if parsed > current:
        raise ValueError("生年月日に未来の日付は指定できません。")
    if parsed < date(1900, 1, 1):
        raise ValueError("生年月日は1900年1月1日以降で入力してください。")
    return parsed


def jst_noon_as_utc(day: date) -> datetime:
    return datetime.combine(day, time(12, 0), tzinfo=JST).astimezone(timezone.utc)


def ecliptic_longitude(body_class: type, moment_utc: datetime) -> float:
    body = body_class()
    utc_naive = moment_utc.astimezone(timezone.utc).replace(tzinfo=None)
    body.compute(ephem.Date(utc_naive))
    ecliptic = ephem.Ecliptic(body)
    return math.degrees(float(ecliptic.lon)) % 360.0


def circular_distance(a: float, b: float) -> float:
    diff = abs(a - b) % 360.0
    return min(diff, 360.0 - diff)


def nearest_aspect(distance: float) -> Tuple[int, str, float]:
    degree, name = min(MAJOR_ASPECTS, key=lambda item: abs(distance - item[0]))
    return degree, name, abs(distance - degree)


def zodiac_name(longitude: float) -> str:
    return ZODIAC_SIGNS[int(longitude // 30) % 12]


def degree_in_sign(longitude: float) -> float:
    return longitude % 30.0


def calculate_birth_sun_sign(birth_date: date) -> Dict[str, Any]:
    """Return the tropical Sun sign at noon JST for an immediate form preview."""
    longitude = ecliptic_longitude(ephem.Sun, jst_noon_as_utc(birth_date))
    index = int(longitude // 30) % 12
    return {
        "name": ZODIAC_SIGNS[index],
        "symbol": ZODIAC_SYMBOLS[index],
        "english": ZODIAC_ENGLISH[index],
        "longitude": round(longitude, 2),
        "degree": round(degree_in_sign(longitude), 2),
    }


def digit_sum(value: int | str) -> int:
    return sum(int(ch) for ch in str(value) if ch.isdigit())


def to_loto_number(value: int | float) -> int:
    return int(round(value)) % 43 + 1


def add_weight(weights: Dict[int, float], number: int, score: float) -> None:
    if 1 <= number <= 43:
        weights[number] = max(float(score), weights.get(number, 0.0))


def unique_number(candidate: int, used: set[int], step: int) -> int:
    number = ((candidate - 1) % 43) + 1
    safe_step = step if math.gcd(step, 43) == 1 else step + 1
    while number in used:
        number = ((number - 1 + safe_step) % 43) + 1
    used.add(number)
    return number


def _build_planet_rows(birth_date: date, target_date: date) -> List[Dict[str, Any]]:
    birth_moment = jst_noon_as_utc(birth_date)
    target_moment = jst_noon_as_utc(target_date)
    birth_key = int(birth_date.strftime("%Y%m%d"))
    target_key = int(target_date.strftime("%Y%m%d"))
    rows: List[Dict[str, Any]] = []

    for index, (planet_id, planet_name, body_class, priority) in enumerate(PLANETS, start=1):
        birth_lon = ecliptic_longitude(body_class, birth_moment)
        current_lon = ecliptic_longitude(body_class, target_moment)
        distance = circular_distance(birth_lon, current_lon)
        aspect_degree, aspect_name, orb = nearest_aspect(distance)
        resonance = max(0.0, 100.0 - orb * 8.0) + priority

        birth_sign_index = int(birth_lon // 30) + 1
        current_sign_index = int(current_lon // 30) + 1
        primary_value = (
            round(birth_lon * 10) * 3
            + round(current_lon * 10) * 5
            + round(distance * 10) * 7
            + birth_sign_index * 11
            + current_sign_index * 13
            + digit_sum(birth_key) * 17
            + digit_sum(target_key) * 19
            + index * 23
        )
        secondary_value = (
            round(((birth_lon + current_lon) % 360.0) * 100)
            + round(orb * 100) * 3
            + birth_date.month * 29
            + birth_date.day * 31
            + target_date.month * 37
            + target_date.day * 41
            + index * 43
        )
        tertiary_value = (
            round(degree_in_sign(birth_lon) * 1000)
            + round(degree_in_sign(current_lon) * 1000) * 2
            + aspect_degree * 7
            + birth_date.year
            + target_date.year * 3
            + index * 47
        )

        rows.append(
            {
                "planet_id": planet_id,
                "planet_name": planet_name,
                "symbol": PLANET_SYMBOLS[planet_id],
                "birth_longitude": round(birth_lon, 2),
                "birth_sign": zodiac_name(birth_lon),
                "birth_degree": round(degree_in_sign(birth_lon), 2),
                "current_longitude": round(current_lon, 2),
                "current_sign": zodiac_name(current_lon),
                "current_degree": round(degree_in_sign(current_lon), 2),
                "distance": round(distance, 2),
                "aspect_degree": aspect_degree,
                "aspect_name": aspect_name,
                "orb": round(orb, 2),
                "resonance": round(resonance, 2),
                "primary_candidate": to_loto_number(primary_value),
                "secondary_candidate": to_loto_number(secondary_value),
                "tertiary_candidate": to_loto_number(tertiary_value),
                "priority": priority,
                "index": index,
            }
        )
    return rows


def calculate_astrology_profile(birth_date: date, target_date: date | None = None) -> Dict[str, Any]:
    current_date = target_date or datetime.now(JST).date()
    planet_rows = _build_planet_rows(birth_date, current_date)
    ranked = sorted(planet_rows, key=lambda row: (row["resonance"], row["priority"]), reverse=True)

    used_core: set[int] = set()
    core_numbers: List[int] = []
    for row in ranked:
        number = unique_number(int(row["primary_candidate"]), used_core, 5 + int(row["index"]) * 2)
        row["core_number"] = number
        if len(core_numbers) < 6:
            core_numbers.append(number)

    weights: Dict[int, float] = {}
    for rank, row in enumerate(ranked, start=1):
        base_score = max(45.0, 112.0 - rank * 5.0 + float(row["resonance"]) * 0.18)
        add_weight(weights, int(row["core_number"]), base_score)
        add_weight(weights, int(row["secondary_candidate"]), base_score - 17.0)
        add_weight(weights, int(row["tertiary_candidate"]), base_score - 25.0)

    birth_date_numbers = [
        to_loto_number(birth_date.year),
        to_loto_number(birth_date.month * 3 + birth_date.day),
        to_loto_number(digit_sum(birth_date.strftime("%Y%m%d")) * 7),
        to_loto_number((birth_date.year % 100) * 5 + birth_date.month * 11 + birth_date.day * 13),
    ]
    current_date_numbers = [
        to_loto_number(current_date.year + current_date.month * 13 + current_date.day * 17),
        to_loto_number(digit_sum(current_date.strftime("%Y%m%d")) * 11),
    ]
    for index, number in enumerate(birth_date_numbers, start=1):
        add_weight(weights, number, 74.0 - index * 3.0)
    for index, number in enumerate(current_date_numbers, start=1):
        add_weight(weights, number, 66.0 - index * 3.0)

    filler_seed = int(birth_date.strftime("%Y%m%d")) + int(current_date.strftime("%Y%m%d"))
    cursor = 1
    while len(weights) < 20:
        value = filler_seed * (cursor * 17 + 31) + cursor * cursor * 19
        add_weight(weights, to_loto_number(value), max(35.0, 58.0 - cursor))
        cursor += 1

    pool_numbers = [
        number
        for number, _score in sorted(weights.items(), key=lambda item: (-item[1], item[0]))
    ]
    sun_row = next(row for row in planet_rows if row["planet_id"] == "sun")
    moon_row = next(row for row in planet_rows if row["planet_id"] == "moon")

    return {
        "birth_date": birth_date.isoformat(),
        "birth_date_ja": f"{birth_date.year}年{birth_date.month}月{birth_date.day}日",
        "target_date": current_date.isoformat(),
        "target_date_ja": f"{current_date.year}年{current_date.month}月{current_date.day}日",
        "calculation_time": "12:00 JST",
        "sun_sign": sun_row["birth_sign"],
        "moon_sign": moon_row["birth_sign"],
        "current_sun_sign": sun_row["current_sign"],
        "core_numbers": sorted(core_numbers),
        "pool_numbers": pool_numbers,
        "weights": weights,
        "planet_rows": planet_rows,
        "method_note": (
            "出生時刻・出生地を使わない簡易星読みです。生年月日と生成日の正午（日本時間）における"
            "7天体の黄経、星座、主要アスペクトへの近さを1〜43へ変換しています。"
        ),
    }


def astrology_numbers_from_profile(profile: Dict[str, Any] | None) -> List[int]:
    if not profile:
        return []
    return [int(number) for number in profile.get("core_numbers", []) if 1 <= int(number) <= 43]


def astrology_pool_from_profile(profile: Dict[str, Any] | None) -> List[int]:
    if not profile:
        return []
    return [int(number) for number in profile.get("pool_numbers", []) if 1 <= int(number) <= 43]


def apply_astrology_scores(
    number_stats: Iterable[Dict[str, Any]],
    profile: Dict[str, Any] | None,
) -> List[Dict[str, Any]]:
    weights = profile.get("weights", {}) if profile else {}
    enriched: List[Dict[str, Any]] = []
    for raw_row in number_stats:
        row = dict(raw_row)
        number = int(row["number"])
        row["astrology_score"] = float(weights.get(number, 0.0))
        enriched.append(row)
    return enriched
