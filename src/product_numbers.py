from __future__ import annotations

import math
import random
from datetime import datetime
from typing import Any, Dict, List, Mapping, MutableSet, Sequence

RandomSource = random.Random | random.SystemRandom

PRODUCTS: Dict[str, Dict[str, Any]] = {
    "miniloto": {
        "product_id": "miniloto",
        "name": "ミニロト",
        "english": "MINI LOTO",
        "kind": "loto",
        "min_number": 1,
        "max_number": 31,
        "pick_count": 5,
        "bonus_count": 1,
        "badge": "1〜31から5個",
        "result_title": "今回、星が導いた五つの数字",
        "button_label": "星読みの数字を生成する",
        "ritual_symbol": "☾",
        "ritual_name": "月輪の五光",
        "ritual_duration": 3900,
    },
    "loto6": {
        "product_id": "loto6",
        "name": "ロト6",
        "english": "LOTO 6",
        "kind": "loto",
        "min_number": 1,
        "max_number": 43,
        "pick_count": 6,
        "bonus_count": 1,
        "badge": "1〜43から6個",
        "result_title": "今回、星が導いた六つの数字",
        "button_label": "星読みの数字を生成する",
        "ritual_symbol": "✡",
        "ritual_name": "六星印の儀",
        "ritual_duration": 4700,
    },
    "loto7": {
        "product_id": "loto7",
        "name": "ロト7",
        "english": "LOTO 7",
        "kind": "loto",
        "min_number": 1,
        "max_number": 37,
        "pick_count": 7,
        "bonus_count": 2,
        "badge": "1〜37から7個",
        "result_title": "今回、星が導いた七つの数字",
        "button_label": "星読みの数字を生成する",
        "ritual_symbol": "Ⅶ",
        "ritual_name": "七惑星の大軌道",
        "ritual_duration": 5400,
    },
    "numbers3": {
        "product_id": "numbers3",
        "name": "ナンバーズ3",
        "english": "NUMBERS 3",
        "kind": "numbers",
        "digit_count": 3,
        "digit_min": 0,
        "digit_max": 9,
        "badge": "0〜9から3桁（順序あり）",
        "result_title": "今回、星が導いた三つの数字",
        "button_label": "星読みの数字を生成する",
        "ritual_symbol": "☿",
        "ritual_name": "三星印の共鳴",
        "ritual_duration": 3800,
    },
    "numbers4": {
        "product_id": "numbers4",
        "name": "ナンバーズ4",
        "english": "NUMBERS 4",
        "kind": "numbers",
        "digit_count": 4,
        "digit_min": 0,
        "digit_max": 9,
        "badge": "0〜9から4桁（順序あり）",
        "result_title": "今回、星が導いた四つの数字",
        "button_label": "星読みの数字を生成する",
        "ritual_symbol": "♀",
        "ritual_name": "四星印の共鳴",
        "ritual_duration": 4200,
    },
}

PRODUCT_ORDER = ["miniloto", "loto6", "loto7", "numbers3", "numbers4"]


def product_choices() -> List[Dict[str, Any]]:
    return [dict(PRODUCTS[product_id]) for product_id in PRODUCT_ORDER]


def get_product(product_id: str) -> Dict[str, Any]:
    try:
        return dict(PRODUCTS[product_id])
    except KeyError as exc:
        raise ValueError("ミニロト・ロト6・ロト7・ナンバーズ3・ナンバーズ4から選択してください。") from exc


def _fold_to_range(value: int, maximum: int) -> int:
    return ((int(value) - 1) % maximum) + 1


def _profile_weights(profile: Mapping[str, Any]) -> Mapping[Any, Any]:
    raw = profile.get("weights", {})
    return raw if isinstance(raw, Mapping) else {}


def _weight_value(weights: Mapping[Any, Any], number: int) -> float:
    value = weights.get(number, weights.get(str(number), 0.0))
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def build_loto_weights(profile: Mapping[str, Any], maximum: int) -> Dict[int, float]:
    result = {number: 1.0 for number in range(1, maximum + 1)}
    source_weights = _profile_weights(profile)

    for source_number in range(1, 44):
        score = _weight_value(source_weights, source_number)
        if score <= 0:
            continue
        folded = _fold_to_range(source_number, maximum)
        result[folded] += score
        # 星の響きを一点に固定しすぎないよう、隣接数字へ弱い余韻を加える。
        result[_fold_to_range(folded - 1, maximum)] += score * 0.10
        result[_fold_to_range(folded + 1, maximum)] += score * 0.10

    for index, row in enumerate(profile.get("planet_rows", []) or []):
        if not isinstance(row, Mapping):
            continue
        resonance = float(row.get("resonance", 0.0) or 0.0)
        planet_bonus = max(8.0, 22.0 + resonance * 0.12 - index)
        for key, factor in (("primary_candidate", 1.0), ("secondary_candidate", 0.55), ("tertiary_candidate", 0.38)):
            if row.get(key) is None:
                continue
            number = _fold_to_range(int(row[key]), maximum)
            result[number] += planet_bonus * factor

    return result


def product_core_numbers(profile: Mapping[str, Any], product: Mapping[str, Any]) -> List[int]:
    maximum = int(product["max_number"])
    wanted = int(product["pick_count"])
    ordered_candidates: List[int] = []
    ordered_candidates.extend(int(value) for value in profile.get("core_numbers", []) or [])
    ordered_candidates.extend(int(value) for value in profile.get("pool_numbers", []) or [])
    seen: set[int] = set()
    result: List[int] = []

    for value in ordered_candidates:
        folded = _fold_to_range(value, maximum)
        if folded in seen:
            continue
        seen.add(folded)
        result.append(folded)
        if len(result) >= wanted:
            break

    cursor = 1
    while len(result) < wanted:
        if cursor not in seen:
            result.append(cursor)
            seen.add(cursor)
        cursor += 1
    return sorted(result)


def _weighted_sample_without_replacement(
    population: Sequence[int],
    weights: Mapping[int, float],
    count: int,
    rng: RandomSource,
) -> List[int]:
    available = list(population)
    chosen: List[int] = []
    for _ in range(min(count, len(available))):
        candidate_weights = [max(0.01, float(weights.get(number, 1.0))) for number in available]
        selected = rng.choices(available, weights=candidate_weights, k=1)[0]
        chosen.append(selected)
        available.remove(selected)
    return chosen


def _consecutive_pairs(numbers: Sequence[int]) -> int:
    ordered = sorted(numbers)
    return sum(1 for left, right in zip(ordered, ordered[1:]) if right - left == 1)


def _loto_metrics(numbers: Sequence[int], maximum: int) -> Dict[str, int]:
    ordered = sorted(int(number) for number in numbers)
    first_cut = math.ceil(maximum / 3)
    second_cut = math.ceil(maximum * 2 / 3)
    return {
        "set_sum": sum(ordered),
        "odd_count": sum(1 for number in ordered if number % 2),
        "even_count": sum(1 for number in ordered if number % 2 == 0),
        "low_count": sum(1 for number in ordered if number <= first_cut),
        "mid_count": sum(1 for number in ordered if first_cut < number <= second_cut),
        "high_count": sum(1 for number in ordered if number > second_cut),
        "consecutive_count": _consecutive_pairs(ordered),
        "spread": ordered[-1] - ordered[0] if ordered else 0,
    }


def _composition_score(numbers: Sequence[int], maximum: int) -> int:
    metrics = _loto_metrics(numbers, maximum)
    count = len(numbers)
    odd_target = count / 2
    odd_score = max(0.0, 1.0 - abs(metrics["odd_count"] - odd_target) / max(1.0, odd_target))
    zone_coverage = sum(1 for key in ("low_count", "mid_count", "high_count") if metrics[key] > 0) / 3
    spread_score = min(1.0, metrics["spread"] / max(1.0, maximum * 0.55))
    consecutive_score = max(0.0, 1.0 - max(0, metrics["consecutive_count"] - 1) * 0.28)
    return round((odd_score * 0.30 + zone_coverage * 0.32 + spread_score * 0.23 + consecutive_score * 0.15) * 100)


def _astrology_score(numbers: Sequence[int], weights: Mapping[int, float]) -> int:
    max_weight = max(weights.values()) if weights else 1.0
    selected = [float(weights.get(number, 0.0)) for number in numbers]
    if not selected or max_weight <= 0:
        return 0
    average = sum(selected) / len(selected)
    peak = max(selected)
    normalized = (average / max_weight) * 0.72 + (peak / max_weight) * 0.28
    return max(0, min(100, round(normalized * 100)))


def _valid_loto_shape(numbers: Sequence[int], maximum: int) -> bool:
    metrics = _loto_metrics(numbers, maximum)
    count = len(numbers)
    # 全数字が一帯へ固まるなど、極端な偶然だけは避ける。
    if metrics["odd_count"] in {0, count}:
        return False
    if sum(1 for key in ("low_count", "mid_count", "high_count") if metrics[key] > 0) < 2:
        return False
    if metrics["consecutive_count"] >= max(3, count - 2):
        return False
    return True


def _loto_reason(numbers: Sequence[int], core_numbers: Sequence[int], product: Mapping[str, Any]) -> str:
    overlap = sorted(set(numbers) & set(core_numbers))
    if overlap:
        overlap_text = "・".join(f"{number:02d}" for number in overlap)
        return (
            f"誕生の日と今日の天体を{product['name']}の数字範囲へ重ね、"
            f"中心の響きと重なった{overlap_text}を軸に結びました。"
        )
    return (
        f"誕生の日と今日の七天体を{product['name']}の数字範囲へ映し、"
        "強く響く候補同士が一つの円環になるよう結びました。"
    )


def _generate_loto_rows(
    product: Mapping[str, Any],
    count: int,
    profile: Mapping[str, Any],
    rng: RandomSource,
    sub_count: int = 0,
) -> List[Dict[str, Any]]:
    maximum = int(product["max_number"])
    pick_count = int(product["pick_count"])
    weights = build_loto_weights(profile, maximum)
    core_numbers = product_core_numbers(profile, product)
    population = list(range(1, maximum + 1))
    seen: MutableSet[tuple[int, ...]] = set()
    rows: List[Dict[str, Any]] = []
    attempts = 0

    while len(rows) < count and attempts < 5000:
        attempts += 1
        numbers = sorted(_weighted_sample_without_replacement(population, weights, pick_count, rng))
        key = tuple(numbers)
        if key in seen or not _valid_loto_shape(numbers, maximum):
            continue
        seen.add(key)
        metrics = _loto_metrics(numbers, maximum)
        astro_score = _astrology_score(numbers, weights)
        composition_score = _composition_score(numbers, maximum)
        total_score = round(astro_score * 0.78 + composition_score * 0.22)
        overlap = sorted(set(numbers) & set(core_numbers))
        remaining_population = [number for number in population if number not in set(numbers)]
        sub_numbers = sorted(
            _weighted_sample_without_replacement(remaining_population, weights, sub_count, rng)
        )
        rows.append(
            {
                "product_id": product["product_id"],
                "product_name": product["name"],
                "product_kind": "loto",
                "numbers": numbers,
                "display_number": " ".join(f"{number:02d}" for number in numbers),
                "sub_numbers": sub_numbers,
                "display_sub_number": " ".join(f"{number:02d}" for number in sub_numbers),
                "astrology_numbers": core_numbers,
                "astrology_hit_count": len(overlap),
                "astrology_fit_score": astro_score,
                "composition_score": composition_score,
                "ticket_score": total_score,
                "reason": _loto_reason(numbers, core_numbers, product),
                **metrics,
            }
        )

    if len(rows) < count:
        raise RuntimeError(f"{product['name']}の数字を指定口数だけ導けませんでした。口数を減らして、もう一度お試しください。")
    return rows


def _fold_to_digit(value: int) -> int:
    return int(value) % 10


def build_digit_weights(profile: Mapping[str, Any]) -> Dict[int, float]:
    """星読みプロフィール（1〜43の重み）をナンバーズの桁（0〜9）へ畳み込む。"""
    result = {digit: 1.0 for digit in range(10)}
    source_weights = _profile_weights(profile)

    for source_number in range(1, 44):
        score = _weight_value(source_weights, source_number)
        if score <= 0:
            continue
        folded = _fold_to_digit(source_number)
        result[folded] += score
        # 星の響きを一点に固定しすぎないよう、隣接する桁へ弱い余韻を加える。
        result[_fold_to_digit(folded - 1)] += score * 0.10
        result[_fold_to_digit(folded + 1)] += score * 0.10

    for index, row in enumerate(profile.get("planet_rows", []) or []):
        if not isinstance(row, Mapping):
            continue
        resonance = float(row.get("resonance", 0.0) or 0.0)
        planet_bonus = max(8.0, 22.0 + resonance * 0.12 - index)
        for key, factor in (("primary_candidate", 1.0), ("secondary_candidate", 0.55), ("tertiary_candidate", 0.38)):
            if row.get(key) is None:
                continue
            digit = _fold_to_digit(int(row[key]))
            result[digit] += planet_bonus * factor

    return result


def numbers_core_digits(profile: Mapping[str, Any], product: Mapping[str, Any]) -> List[int]:
    wanted = int(product["digit_count"])
    ordered_candidates: List[int] = []
    ordered_candidates.extend(int(value) for value in profile.get("core_numbers", []) or [])
    ordered_candidates.extend(int(value) for value in profile.get("pool_numbers", []) or [])
    seen: set[int] = set()
    result: List[int] = []

    for value in ordered_candidates:
        folded = _fold_to_digit(value)
        if folded in seen:
            continue
        seen.add(folded)
        result.append(folded)
        if len(result) >= wanted:
            break

    cursor = 0
    while len(result) < wanted:
        if cursor not in seen:
            result.append(cursor)
            seen.add(cursor)
        cursor += 1
    return sorted(result)


def _digit_weighted_choice(weights: Mapping[int, float], rng: RandomSource) -> int:
    digits = list(range(10))
    candidate_weights = [max(0.01, float(weights.get(digit, 1.0))) for digit in digits]
    return rng.choices(digits, weights=candidate_weights, k=1)[0]


def _numbers_metrics(digits: Sequence[int]) -> Dict[str, int]:
    values = [int(d) for d in digits]
    return {
        "set_sum": sum(values),
        "odd_count": sum(1 for d in values if d % 2),
        "even_count": sum(1 for d in values if d % 2 == 0),
        "spread": (max(values) - min(values)) if values else 0,
        "consecutive_count": len(values) - len(set(values)),
    }


def _numbers_composition_score(digits: Sequence[int]) -> int:
    metrics = _numbers_metrics(digits)
    count = len(digits)
    odd_target = count / 2
    odd_score = max(0.0, 1.0 - abs(metrics["odd_count"] - odd_target) / max(1.0, odd_target))
    spread_score = min(1.0, metrics["spread"] / 9.0)
    repeat_score = max(0.0, 1.0 - metrics["consecutive_count"] * 0.35)
    return round((odd_score * 0.34 + spread_score * 0.36 + repeat_score * 0.30) * 100)


def _numbers_astrology_score(digits: Sequence[int], weights: Mapping[int, float]) -> int:
    max_weight = max(weights.values()) if weights else 1.0
    selected = [float(weights.get(d, 0.0)) for d in digits]
    if not selected or max_weight <= 0:
        return 0
    average = sum(selected) / len(selected)
    peak = max(selected)
    normalized = (average / max_weight) * 0.72 + (peak / max_weight) * 0.28
    return max(0, min(100, round(normalized * 100)))


def _numbers_reason(digits: Sequence[int], core_digits: Sequence[int], product: Mapping[str, Any]) -> str:
    overlap = sorted(set(digits) & set(core_digits))
    if overlap:
        overlap_text = "・".join(str(number) for number in overlap)
        return (
            f"誕生の日と今日の天体を{product['name']}の桁ごとの響きへ重ね、"
            f"中心の響きと重なった{overlap_text}を軸に桁を並べました。"
        )
    return (
        f"誕生の日と今日の七天体を{product['name']}の桁ごとの響きへ映し、"
        "強く響く数字が順序よく並ぶよう導きました。"
    )


def _generate_numbers_rows(
    product: Mapping[str, Any],
    count: int,
    profile: Mapping[str, Any],
    rng: RandomSource,
    sub_count: int = 0,
) -> List[Dict[str, Any]]:
    digit_count = int(product["digit_count"])
    weights = build_digit_weights(profile)
    core_digits = numbers_core_digits(profile, product)
    seen: MutableSet[tuple[int, ...]] = set()
    rows: List[Dict[str, Any]] = []
    attempts = 0

    while len(rows) < count and attempts < 5000:
        attempts += 1
        digits = [_digit_weighted_choice(weights, rng) for _ in range(digit_count)]
        key = tuple(digits)
        if key in seen:
            continue
        seen.add(key)
        metrics = _numbers_metrics(digits)
        astro_score = _numbers_astrology_score(digits, weights)
        composition_score = _numbers_composition_score(digits)
        total_score = round(astro_score * 0.78 + composition_score * 0.22)
        overlap = sorted(set(digits) & set(core_digits))
        box_digits = sorted(digits)
        remaining_digits = [digit for digit in range(10) if digit not in set(digits)]
        sub_digits = sorted(_weighted_sample_without_replacement(remaining_digits, weights, sub_count, rng))
        rows.append(
            {
                "product_id": product["product_id"],
                "product_name": product["name"],
                "product_kind": "numbers",
                "numbers": digits,
                "box_numbers": box_digits,
                "display_number": "-".join(str(number) for number in digits),
                "display_box_number": "-".join(str(number) for number in box_digits),
                "sub_numbers": sub_digits,
                "display_sub_number": "-".join(str(number) for number in sub_digits),
                "astrology_numbers": core_digits,
                "astrology_hit_count": len(overlap),
                "astrology_fit_score": astro_score,
                "composition_score": composition_score,
                "ticket_score": total_score,
                "reason": _numbers_reason(digits, core_digits, product),
                **metrics,
            }
        )

    if len(rows) < count:
        raise RuntimeError(f"{product['name']}の数字を指定口数だけ導けませんでした。口数を減らして、もう一度お試しください。")
    return rows


def generate_product_rows(
    product_id: str,
    count: int,
    profile: Mapping[str, Any],
    seed: str = "",
    sub_count: int = 1,
) -> List[Dict[str, Any]]:
    product = get_product(product_id)
    rng: RandomSource = random.Random(seed) if seed else random.SystemRandom()
    sub_count = max(0, int(sub_count))
    if product.get("kind") == "numbers":
        rows = _generate_numbers_rows(product, count, profile, rng, sub_count=sub_count)
    else:
        rows = _generate_loto_rows(product, count, profile, rng, sub_count=sub_count)

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    for index, row in enumerate(rows, start=1):
        row["ticket_id"] = f"web_{stamp}_{index:03d}"
        row["generated_at"] = generated_at
    return rows
