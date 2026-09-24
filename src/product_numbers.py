from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Mapping, MutableSet, Sequence

from settings import MAX_TICKET_COUNT
from oracle_mapping import correspondence

RandomSource = random.Random | random.SystemRandom

PRODUCTS: Dict[str, Dict[str, Any]] = {
    "miniloto": {
        "product_id": "miniloto",
        "name": "ミニロト",
        "english": "MINI LOTO",
        "kind": "loto",
        "max_number": 31,
        "pick_count": 5,
        "full_size": 5,
        "badge": "1〜31から5個",
        "ritual_duration": 3900,
    },
    "loto6": {
        "product_id": "loto6",
        "name": "ロト6",
        "english": "LOTO 6",
        "kind": "loto",
        "max_number": 43,
        "pick_count": 6,
        "full_size": 6,
        "badge": "1〜43から6個",
        "ritual_duration": 4700,
    },
    "loto7": {
        "product_id": "loto7",
        "name": "ロト7",
        "english": "LOTO 7",
        "kind": "loto",
        "max_number": 37,
        "pick_count": 7,
        "full_size": 7,
        "badge": "1〜37から7個",
        "ritual_duration": 5400,
    },
    "numbers3": {
        "product_id": "numbers3",
        "name": "ナンバーズ3",
        "english": "NUMBERS 3",
        "kind": "numbers",
        "digit_count": 3,
        "full_size": 3,
        "badge": "0〜9から3桁（順序あり）",
        "ritual_duration": 3800,
    },
    "numbers4": {
        "product_id": "numbers4",
        "name": "ナンバーズ4",
        "english": "NUMBERS 4",
        "kind": "numbers",
        "digit_count": 4,
        "full_size": 4,
        "badge": "0〜9から4桁（順序あり）",
        "ritual_duration": 4200,
    },
}

#: Largest `full_size` across every product, i.e. how many <option> rows the
#: "欲しい個数" selector needs to render (options beyond a product's own
#: full_size are disabled client-side; see static/js/app.js).
MAX_FULL_SIZE = max(item["full_size"] for item in PRODUCTS.values())

PRODUCT_ORDER = ["miniloto", "loto6", "loto7", "numbers3", "numbers4"]


def product_choices() -> List[Dict[str, Any]]:
    return [dict(PRODUCTS[product_id]) for product_id in PRODUCT_ORDER]


def get_product(product_id: str) -> Dict[str, Any]:
    try:
        return dict(PRODUCTS[product_id])
    except KeyError as exc:
        raise ValueError("ミニロト・ロト6・ロト7・ナンバーズ3・ナンバーズ4から選択してください。") from exc


def product_full_size(product: Mapping[str, Any]) -> int:
    """The product's own maximum: pick_count for loto, digit_count for numbers."""
    return int(product["full_size"])


def _weight_value(weights: Mapping[Any, Any], number: int) -> float:
    try:
        value = float(weights.get(number, weights.get(str(number), 0.0)) or 0.0)
        return max(0.0, value) if math.isfinite(value) else 0.0
    except (TypeError, ValueError):
        return 0.0


def _source_weights(profile: Mapping[str, Any]) -> List[float]:
    """Keep each method's character in the original 43 equal-width bins."""
    raw = profile.get("weights", {})
    weights = raw if isinstance(raw, Mapping) else {}
    source = [_weight_value(weights, n) for n in range(1, 44)]
    # Smooth on the source circle, before converting to a lottery's range.
    result = [source[i] + .1 * (source[(i - 1) % 43] + source[(i + 1) % 43]) for i in range(43)]
    for index, row in enumerate(profile.get("boost_rows", []) or []):
        if not isinstance(row, Mapping):
            continue
        resonance = _weight_value({1: row.get("resonance")}, 1)
        bonus = max(8.0, 22.0 + resonance * .12 - index)
        for key, factor in (("primary_candidate", 1.0), ("secondary_candidate", .55), ("tertiary_candidate", .38)):
            try:
                number = int(row.get(key, 0))
            except (TypeError, ValueError):
                continue
            if 1 <= number <= 43:
                result[number - 1] += bonus * factor
    return result


def _resample_weights(source: Sequence[float], size: int) -> List[float]:
    """Area-average equal intervals of [0, 1], without modulo fold-over.

    Use integer interval boundaries (source bins have width `size`, target
    bins have width len(source)). A flat source is exactly flat for ALL
    destination sizes; neither the low band nor digits 1/2/3 get extra mass.
    Source peaks are preserved as fractional overlap, without dropping bins.
    """
    width = len(source)
    return [
        sum(value * max(0, min((j + 1) * width, (i + 1) * size)
                        - max(j * width, i * size))
            for i, value in enumerate(source)) / width
        for j in range(size)
    ]


def build_loto_weights(profile: Mapping[str, Any], maximum: int) -> Dict[int, float]:
    if profile.get('oracle_evidence'):
        return correspondence(profile, maximum)[0]
    return {i + 1: 1.0 + value for i, value in enumerate(_resample_weights(_source_weights(profile), maximum))}


def build_digit_weights(profile: Mapping[str, Any]) -> Dict[int, float]:
    if profile.get('oracle_evidence'):
        return correspondence(profile, 10, 0)[0]
    return {i: 1.0 + value for i, value in enumerate(_resample_weights(_source_weights(profile), 10))}


def _core_numbers(profile: Mapping[str, Any], size: int, wanted: int, minimum: int) -> List[int]:
    if profile.get('oracle_evidence'):
        weights, _ = correspondence(profile, size, minimum)
        return sorted(sorted(weights, key=lambda n: (-weights[n], n))[:wanted])
    # Resample the core signal in the same coordinate system as the weights.
    cores = set(profile.get("core_numbers", []) or [])
    source = _source_weights(profile)
    signal = _resample_weights([1.0 if n in cores else 0.0 for n in range(1, 44)], size)
    strengths = _resample_weights(source, size)
    ranked = sorted(range(size), key=lambda i: (-signal[i], -strengths[i], i))
    return sorted(i + minimum for i in ranked[:wanted])


def product_core_numbers(profile: Mapping[str, Any], product: Mapping[str, Any]) -> List[int]:
    return _core_numbers(profile, int(product["max_number"]), int(product["pick_count"]), 1)


def numbers_core_digits(profile: Mapping[str, Any], product: Mapping[str, Any]) -> List[int]:
    return _core_numbers(profile, 10, int(product["digit_count"]), 0)


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


def _divination_score(numbers: Sequence[int], weights: Mapping[int, float]) -> int:
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


def _loto_reason(numbers: Sequence[int], core_numbers: Sequence[int], product: Mapping[str, Any], profile: Mapping[str, Any]) -> str:
    overlap = sorted(set(numbers) & set(core_numbers))
    source = str(profile.get("reason_source", "選んだ占いから導いた数"))
    method = str(profile.get("method_short_name", "占い"))
    if overlap:
        overlap_text = "・".join(f"{number:02d}" for number in overlap)
        return (
            f"{source}を{product['name']}の数字範囲へ重ね、"
            f"{method}の中心数字と重なった{overlap_text}を軸に結びました。"
        )
    return (
        f"{source}を{product['name']}の数字範囲へ映し、"
        f"{method}の対応する重みに沿って候補を結びました。"
    )


def _generate_loto_rows(
    product: Mapping[str, Any],
    count: int,
    profile: Mapping[str, Any],
    rng: RandomSource,
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
        if key in seen:
            continue
        seen.add(key)
        metrics = _loto_metrics(numbers, maximum)
        divination_score = _divination_score(numbers, weights)
        composition_score = _composition_score(numbers, maximum)
        total_score = divination_score
        rows.append(
            {
                "numbers": numbers,
                "reference_numbers": core_numbers,
                "divination_fit_score": divination_score,
                "composition_score": composition_score,
                "ticket_score": total_score,
                "reason": _loto_reason(numbers, core_numbers, product, profile),
                **{key: metrics[key] for key in ("set_sum", "odd_count", "even_count", "spread", "consecutive_count")},
            }
        )

    if len(rows) < count:
        raise RuntimeError(f"{product['name']}の数字を指定口数だけ導けませんでした。口数を減らして、もう一度お試しください。")
    return rows


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


def _numbers_reason(digits: Sequence[int], core_digits: Sequence[int], product: Mapping[str, Any], profile: Mapping[str, Any]) -> str:
    overlap = sorted(set(digits) & set(core_digits))
    source = str(profile.get("reason_source", "選んだ占いから導いた数"))
    method = str(profile.get("method_short_name", "占い"))
    if overlap:
        overlap_text = "・".join(str(number) for number in overlap)
        return (
            f"{source}を{product['name']}の各桁へ重ね、"
            f"{method}の中心数字と重なった{overlap_text}を軸に桁を並べました。"
        )
    return (
        f"{source}を{product['name']}の各桁へ映し、"
        f"{method}で強く響く数字が順序よく並ぶよう導きました。"
    )


def _rank_positions_by_weight(values: Sequence[int], weights: Mapping[int, float]) -> List[int]:
    """Position indices of `values`, most divination-weighted first.

    Ties (equal weight, including repeated digits) keep the leftmost/
    lowest-index position first, so a tie always resolves the same way.
    """
    return sorted(range(len(values)), key=lambda i: (-_weight_value(weights, values[i]), i))


def _reduce_unordered(values: Sequence[int], weights: Mapping[int, float], size: int) -> List[int]:
    """Keep the `size` most divination-weighted values, order-independent.

    Used for loto-type tickets, where only the set of numbers matters.
    Displayed ascending, as loto numbers conventionally are.
    """
    if size >= len(values):
        return sorted(values)
    keep = sorted(_rank_positions_by_weight(values, weights)[:size])
    return sorted(values[i] for i in keep)


def _reduce_ordered(values: Sequence[int], weights: Mapping[int, float], size: int) -> List[int]:
    """Keep the `size` most divination-weighted positions, left-to-right order kept.

    Used for Numbers-type tickets, where digit order is part of the ticket:
    dropping digits must not reorder the ones that remain.
    """
    if size >= len(values):
        return list(values)
    keep = sorted(_rank_positions_by_weight(values, weights)[:size])
    return [values[i] for i in keep]


def _reduce_loto_row(
    row: Dict[str, Any],
    weights: Mapping[int, float],
    maximum: int,
    core_numbers: Sequence[int],
    product: Mapping[str, Any],
    profile: Mapping[str, Any],
    size: int,
) -> Dict[str, Any]:
    numbers = _reduce_unordered(row["numbers"], weights, size)
    metrics = _loto_metrics(numbers, maximum)
    divination_score = _divination_score(numbers, weights)
    composition_score = _composition_score(numbers, maximum)
    row = dict(row)
    row.update(
        {
            "numbers": numbers,
            "divination_fit_score": divination_score,
            "composition_score": composition_score,
            "ticket_score": divination_score,
            "reason": _loto_reason(numbers, core_numbers, product, profile),
            **{key: metrics[key] for key in ("set_sum", "odd_count", "even_count", "spread", "consecutive_count")},
        }
    )
    return row


def _reduce_numbers_row(
    row: Dict[str, Any],
    weights: Mapping[int, float],
    core_digits: Sequence[int],
    product: Mapping[str, Any],
    profile: Mapping[str, Any],
    size: int,
) -> Dict[str, Any]:
    digits = _reduce_ordered(row["numbers"], weights, size)
    metrics = _numbers_metrics(digits)
    divination_score = _divination_score(digits, weights)
    composition_score = _numbers_composition_score(digits)
    row = dict(row)
    row.update(
        {
            "numbers": digits,
            "display_box_number": "-".join(str(number) for number in sorted(digits)),
            "divination_fit_score": divination_score,
            "composition_score": composition_score,
            "ticket_score": divination_score,
            "reason": _numbers_reason(digits, core_digits, product, profile),
            **{key: metrics[key] for key in ("set_sum", "odd_count", "even_count", "spread", "consecutive_count")},
        }
    )
    return row


def _generate_numbers_rows(
    product: Mapping[str, Any],
    count: int,
    profile: Mapping[str, Any],
    rng: RandomSource,
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
        divination_score = _divination_score(digits, weights)
        composition_score = _numbers_composition_score(digits)
        total_score = divination_score
        box_digits = sorted(digits)
        rows.append(
            {
                "numbers": digits,
                "display_box_number": "-".join(str(number) for number in box_digits),
                "reference_numbers": core_digits,
                "divination_fit_score": divination_score,
                "composition_score": composition_score,
                "ticket_score": total_score,
                "reason": _numbers_reason(digits, core_digits, product, profile),
                **{key: metrics[key] for key in ("set_sum", "odd_count", "even_count", "spread", "consecutive_count")},
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
    pick_size: int | None = None,
) -> List[Dict[str, Any]]:
    """Rank a unique daily pool for the requested size, then return its prefix.

    Version 1.18 uses method-specific evidence weights. Partial candidates are generated
    independently within the product's range and are not purchase-ready tickets.
    """
    product = get_product(product_id)
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= MAX_TICKET_COUNT:
        raise ValueError(f"受け取る口数は1〜{MAX_TICKET_COUNT}の範囲で選んでください。")
    full_size = product_full_size(product)
    if pick_size is None:
        pick_size = full_size
    if isinstance(pick_size, bool) or not isinstance(pick_size, int) or not 1 <= pick_size <= full_size:
        raise ValueError(f"欲しい個数は1〜{full_size}の範囲で選んでください。")
    rng: RandomSource = random.Random(seed) if seed else random.SystemRandom()
    if pick_size < full_size:
        # Size is part of the daily choice. Count never influences the pool.
        rng = random.Random(f"{seed}|size={pick_size}") if seed else random.SystemRandom()
        is_digits = product["kind"] == "numbers"
        weights = build_digit_weights(profile) if is_digits else build_loto_weights(profile, int(product["max_number"]))
        cores = numbers_core_digits(profile, product) if is_digits else product_core_numbers(profile, product)
        rows = []
        seen = set()
        for _ in range(5000):
            values = ([_digit_weighted_choice(weights, rng) for _ in range(pick_size)] if is_digits
                      else sorted(_weighted_sample_without_replacement(list(weights), weights, pick_size, rng)))
            key = tuple(values)
            if key in seen:
                continue
            seen.add(key)
            row = {"numbers": values, "reference_numbers": cores}
            rows.append(_reduce_numbers_row(row, weights, cores, product, profile, pick_size) if is_digits
                        else _reduce_loto_row(row, weights, int(product["max_number"]), cores, product, profile, pick_size))
            if len(rows) == MAX_TICKET_COUNT:
                break
        if len(rows) < MAX_TICKET_COUNT:
            raise RuntimeError("候補を作成できませんでした。もう一度お試しください。")
    elif product["kind"] == "numbers":
        rows = _generate_numbers_rows(product, MAX_TICKET_COUNT, profile, rng)
    else:
        rows = _generate_loto_rows(product, MAX_TICKET_COUNT, profile, rng)
    if profile.get('oracle_evidence'):
        _, origins = correspondence(profile, int(product['max_number']) if product['kind']=='loto' else 10,
                                    1 if product['kind']=='loto' else 0)
        for row in rows:
            row['number_origins'] = [origins[n] for n in row['numbers']]
    rows.sort(key=lambda row: row["ticket_score"], reverse=True)
    return rows[:count]
