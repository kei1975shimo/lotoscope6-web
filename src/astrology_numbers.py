from __future__ import annotations

import math
from datetime import date, datetime, time, timezone
from typing import Any, Dict, List, Sequence, Tuple
from zoneinfo import ZoneInfo

import ephem
from oracle_mapping import finish_profile

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
        raise ValueError("生年月日を西暦で入力してください。")
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
    moment = ephem.Date(utc_naive)
    body.compute(moment, epoch=moment)
    ecliptic = ephem.Ecliptic(body, epoch=moment)
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


def digit_sum(value: int | str) -> int:
    return sum(int(ch) for ch in str(value) if ch.isdigit())


def to_loto_number(value: int | float) -> int:
    # Preserve the historical zero-based residue mapping (1 -> 2, 43 -> 1).
    # Original intent is undocumented. Switching to one-based normalization
    # changes daily results; do not alter without an explicit migration decision.
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


# One published policy for this date-only chart; orb choices vary by school.
ASPECT_ORB = 6.0


def calculate_astrology_profile(birth_date: date, target_date: date | None = None) -> Dict[str, Any]:
    current_date = target_date or datetime.now(JST).date()
    rows = []
    evidence = []
    for planet_id, name, body_class, _legacy_priority in PLANETS:
        birth_lon = ecliptic_longitude(body_class, jst_noon_as_utc(birth_date))
        current_lon = ecliptic_longitude(body_class, jst_noon_as_utc(current_date))
        rows.append(dict(planet_id=planet_id, planet_name=name, symbol=PLANET_SYMBOLS[planet_id],
                         birth_longitude=birth_lon, current_longitude=current_lon,
                         birth_sign=zodiac_name(birth_lon), current_sign=zodiac_name(current_lon),
                         birth_sign_symbol=ZODIAC_SYMBOLS[int(birth_lon//30)],
                         current_sign_symbol=ZODIAC_SYMBOLS[int(current_lon//30)],
                         birth_degree=round(degree_in_sign(birth_lon),2),
                         current_degree=round(degree_in_sign(current_lon),2)))
        for label, lon in [('誕生日', birth_lon), ('生成日', current_lon)]:
            evidence.append(dict(kind='longitude', value=lon, strength=1.0, label=f'{label}の{name}'))
    aspects = []
    # All 7 transit bodies against all 7 natal bodies; not only same-body pairs.
    for transit in rows:
        for natal in rows:
            angle, name, orb = nearest_aspect(circular_distance(transit['current_longitude'], natal['birth_longitude']))
            if orb > ASPECT_ORB:
                continue
            label = f"生成日の{transit['planet_name']} × 誕生日の{natal['planet_name']}・{name}"
            aspects.append(dict(label=label, degree=angle, orb=round(orb,3)))
            # Closer aspects reinforce their actual endpoints equally. Hard
            # aspects are not treated as bad lottery outcomes.
            for lon in (transit['current_longitude'], natal['birth_longitude']):
                evidence.append(dict(kind='longitude', value=lon, strength=1-orb/ASPECT_ORB, label=label))
    sun, moon = rows[:2]
    return finish_profile(dict(
        calculation_time='12:00 JST', planet_rows=rows, aspect_rows=aspects,
        sun_sign=sun['birth_sign'], sun_sign_symbol=sun['birth_sign_symbol'],
        moon_sign=moon['birth_sign'], moon_sign_symbol=moon['birth_sign_symbol'],
        current_sun_sign=sun['current_sign'], current_sun_sign_symbol=sun['current_sign_symbol'],
        oracle_evidence=evidence,
        method_note='出生時刻・出生地を使わない簡易星読みです。両日の正午（日本時間）の七天体を、各日の春分点を基準とする黄経で計算します。出生図のハウス・上昇宮は扱いません。月や星座境界は出生時刻により変わり得ます。主要アスペクトは0・60・90・120・180度、許容差6度以内で判定します。黄道を券種の数字数で等分し、天体が入る区画とその近さを数字の重みにする部分は本アプリ独自の対応です。'
    ))
