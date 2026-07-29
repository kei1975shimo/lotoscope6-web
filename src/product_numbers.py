from __future__ import annotations

import math
import random
from collections import Counter
from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, MutableSet, Sequence

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
        "description": "小さな数字の円環から、異なる五つの数字を導きます。",
        "result_title": "今回、星が導いた五つの数字",
        "button_label": "五つの月光を受け取る",
        "ritual_symbol": "☾",
        "ritual_name": "月輪の五光",
        "ritual_description": "月の円環に五つの星を灯し、静かな光から数字を受け取ります。",
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
        "description": "これまでの星読みを受け継ぎ、異なる六つの数字を導きます。",
        "result_title": "今回、星が導いた六つの数字",
        "button_label": "六つの星印をひらく",
        "ritual_symbol": "✡",
        "ritual_name": "六星印の儀",
        "ritual_description": "二つの三角形が重なり、六つの天体印から数字が姿を現します。",
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
        "description": "七天体の響きを重ね、異なる七つの数字を導きます。",
        "result_title": "今回、星が導いた七つの数字",
        "button_label": "七つの軌道を重ねる",
        "ritual_symbol": "Ⅶ",
        "ritual_name": "七惑星の大軌道",
        "ritual_description": "七天体がそれぞれの軌道を巡り、ひとつの星図へ収束します。",
        "ritual_duration": 5400,
    },
    "numbers3": {
        "product_id": "numbers3",
        "name": "ナンバーズ3",
        "english": "NUMBERS 3",
        "kind": "numbers",
        "digit_count": 3,
        "badge": "0〜9の3桁",
        "description": "三つの桁を別々の天体から読み、並び順ごと導きます。",
        "result_title": "今回、星が導いた三桁の数字",
        "button_label": "三つの星盤をひらく",
        "ritual_symbol": "Ⅲ",
        "ritual_name": "三連星盤",
        "ritual_description": "三つの天体盤に星の光が巡り、左から順に三桁の星列を結びます。",
        "ritual_duration": 3600,
    },
    "numbers4": {
        "product_id": "numbers4",
        "name": "ナンバーズ4",
        "english": "NUMBERS 4",
        "kind": "numbers",
        "digit_count": 4,
        "badge": "0〜9の4桁",
        "description": "四つの桁を別々の天体から読み、先頭の0もそのまま届けます。",
        "result_title": "今回、星が導いた四桁の数字",
        "button_label": "四つの星門をひらく",
        "ritual_symbol": "Ⅳ",
        "ritual_name": "四星門の啓示",
        "ritual_description": "四つの星門を一枚ずつひらき、並びを崩さず数字を受け取ります。",
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
        raise ValueError("数字を受け取る宝くじを選択してください。") from exc


def _fold_to_range(value: int, maximum: int) -> int:
    return ((int(value) - 1) % maximum) + 1


def _fold_to_digit(value: int) -> int:
    return abs(int(value)) % 10


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
    if product["kind"] == "numbers":
        digits: List[int] = []
        for row in profile.get("planet_rows", []) or []:
            if not isinstance(row, Mapping):
                continue
            digits.append(_fold_to_digit(int(row.get("primary_candidate", 0))))
            if len(digits) >= int(product["digit_count"]):
                break
        while len(digits) < int(product["digit_count"]):
            digits.append((len(digits) * 3 + 7) % 10)
        return digits

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
    for _ in range(count):
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
    # 方式としての「バランス」は廃止するが、全数字が一帯へ固まる極端な偶然だけは避ける。
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
        rows.append(
            {
                "product_id": product["product_id"],
                "product_name": product["name"],
                "product_kind": "loto",
                "numbers": numbers,
                "display_number": " ".join(f"{number:02d}" for number in numbers),
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


def _digit_weight_sets(profile: Mapping[str, Any], digit_count: int) -> List[Dict[int, float]]:
    base = {digit: 2.0 for digit in range(10)}
    for number in range(1, 44):
        score = _weight_value(_profile_weights(profile), number)
        base[_fold_to_digit(number)] += score * 0.48

    birth_digits = [int(char) for char in str(profile.get("birth_date", "")) if char.isdigit()]
    current_digits = [int(char) for char in str(profile.get("target_date", "")) if char.isdigit()]
    planet_rows = [row for row in (profile.get("planet_rows", []) or []) if isinstance(row, Mapping)]
    results: List[Dict[int, float]] = []

    for position in range(digit_count):
        weights = dict(base)
        if planet_rows:
            row = planet_rows[position % len(planet_rows)]
            resonance = float(row.get("resonance", 0.0) or 0.0)
            weights[_fold_to_digit(int(row.get("primary_candidate", 0)))] += 58.0 + resonance * 0.18
            weights[_fold_to_digit(int(row.get("secondary_candidate", 0)))] += 31.0 + resonance * 0.08
            weights[_fold_to_digit(int(row.get("tertiary_candidate", 0)))] += 20.0
            degree_seed = round(float(row.get("birth_degree", 0.0) or 0.0) + float(row.get("current_degree", 0.0) or 0.0))
            weights[_fold_to_digit(degree_seed)] += 24.0
        if birth_digits:
            weights[birth_digits[position % len(birth_digits)]] += 22.0
        if current_digits:
            weights[current_digits[(position * 2 + 1) % len(current_digits)]] += 16.0
        results.append(weights)
    return results


def _numbers_reason(digits: Sequence[int], profile: Mapping[str, Any]) -> str:
    planet_rows = [row for row in (profile.get("planet_rows", []) or []) if isinstance(row, Mapping)]
    names = [str(row.get("planet_name", "天体")) for row in planet_rows[: len(digits)]]
    if names:
        return f"{('・'.join(names))}の響きを左の桁から順に読み、並びそのものを一つの数字として結びました。"
    return "誕生の日と今日の天体を各桁へ分けて読み、並びそのものを一つの数字として結びました。"


def _generate_numbers_rows(
    product: Mapping[str, Any],
    count: int,
    profile: Mapping[str, Any],
    rng: RandomSource,
) -> List[Dict[str, Any]]:
    digit_count = int(product["digit_count"])
    weight_sets = _digit_weight_sets(profile, digit_count)
    core_digits = product_core_numbers(profile, product)
    rows: List[Dict[str, Any]] = []
    seen: set[str] = set()
    attempts = 0

    while len(rows) < count and attempts < 3000:
        attempts += 1
        digits: List[int] = []
        position_scores: List[float] = []
        for weights in weight_sets:
            candidates = list(range(10))
            selected = rng.choices(candidates, weights=[max(0.01, weights[d]) for d in candidates], k=1)[0]
            digits.append(selected)
            position_scores.append(weights[selected] / max(weights.values()))
        number_string = "".join(str(digit) for digit in digits)
        if number_string in seen:
            continue
        seen.add(number_string)
        astro_score = round(sum(position_scores) / len(position_scores) * 100)
        repeated_pairs = sum(amount - 1 for amount in Counter(digits).values() if amount > 1)
        variety_score = round(max(0.0, 100.0 - repeated_pairs * 10.0))
        total_score = round(astro_score * 0.90 + variety_score * 0.10)
        rows.append(
            {
                "product_id": product["product_id"],
                "product_name": product["name"],
                "product_kind": "numbers",
                "numbers": digits,
                "display_number": number_string,
                "astrology_numbers": core_digits,
                "astrology_hit_count": sum(1 for left, right in zip(digits, core_digits) if left == right),
                "astrology_fit_score": astro_score,
                "composition_score": variety_score,
                "ticket_score": total_score,
                "reason": _numbers_reason(digits, profile),
                "set_sum": sum(digits),
                "odd_count": sum(1 for digit in digits if digit % 2),
                "even_count": sum(1 for digit in digits if digit % 2 == 0),
                "repeated_digit_count": repeated_pairs,
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
) -> List[Dict[str, Any]]:
    product = get_product(product_id)
    rng: RandomSource = random.Random(seed) if seed else random.SystemRandom()
    if product["kind"] == "loto":
        rows = _generate_loto_rows(product, count, profile, rng)
    else:
        rows = _generate_numbers_rows(product, count, profile, rng)

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    for index, row in enumerate(rows, start=1):
        row["ticket_id"] = f"web_{stamp}_{index:03d}"
        row["generated_at"] = generated_at
    return rows


def prize_label(product_id: str, match_count: int, bonus_hit_count: int) -> str:
    if product_id == "miniloto":
        if match_count == 5:
            return "1等条件"
        if match_count == 4 and bonus_hit_count >= 1:
            return "2等条件"
        if match_count == 4:
            return "3等条件"
        if match_count == 3:
            return "4等条件"
    elif product_id == "loto6":
        if match_count == 6:
            return "1等条件"
        if match_count == 5 and bonus_hit_count >= 1:
            return "2等条件"
        if match_count == 5:
            return "3等条件"
        if match_count == 4:
            return "4等条件"
        if match_count == 3:
            return "5等条件"
    elif product_id == "loto7":
        if match_count == 7:
            return "1等条件"
        if match_count == 6 and bonus_hit_count >= 1:
            return "2等条件"
        if match_count == 6:
            return "3等条件"
        if match_count == 5:
            return "4等条件"
        if match_count == 4:
            return "5等条件"
        if match_count == 3:
            return "6等条件"
    return "当せん条件外"


def check_loto_rows(
    rows: Iterable[Mapping[str, Any]],
    product_id: str,
    main_numbers: Sequence[int],
    bonus_numbers: Sequence[int],
    draw_label: str = "手入力",
) -> List[Dict[str, Any]]:
    main_set = set(int(number) for number in main_numbers)
    bonus_set = set(int(number) for number in bonus_numbers)
    checked: List[Dict[str, Any]] = []
    for raw in rows:
        row = dict(raw)
        ticket_numbers = [int(number) for number in row.get("numbers", [])]
        match_count = len(set(ticket_numbers) & main_set)
        bonus_hit_count = len(set(ticket_numbers) & bonus_set)
        row.update(
            {
                "match_count": match_count,
                "bonus_hit_count": bonus_hit_count,
                "prize_label": prize_label(product_id, match_count, bonus_hit_count),
                "draw_main_numbers": list(main_numbers),
                "draw_bonus_numbers": list(bonus_numbers),
                "draw_label": draw_label,
                "straight_match": False,
                "box_match": False,
                "position_match_count": 0,
            }
        )
        checked.append(row)
    return checked


def check_numbers_rows(
    rows: Iterable[Mapping[str, Any]],
    winning_number: str,
    draw_label: str = "手入力",
) -> List[Dict[str, Any]]:
    winning_digits = [int(char) for char in winning_number]
    winning_counter = Counter(winning_digits)
    checked: List[Dict[str, Any]] = []
    for raw in rows:
        row = dict(raw)
        ticket_digits = [int(number) for number in row.get("numbers", [])]
        straight = ticket_digits == winning_digits
        box = Counter(ticket_digits) == winning_counter
        position_matches = sum(1 for left, right in zip(ticket_digits, winning_digits) if left == right)
        if straight:
            label = "ストレート一致"
        elif box:
            label = "ボックス一致"
        elif row.get("product_id") == "numbers3" and ticket_digits[-2:] == winning_digits[-2:]:
            label = "ミニ一致"
        else:
            label = "一致なし"
        row.update(
            {
                "match_count": position_matches,
                "bonus_hit_count": 0,
                "prize_label": label,
                "draw_main_numbers": winning_digits,
                "draw_bonus_numbers": [],
                "draw_label": draw_label,
                "straight_match": straight,
                "box_match": box,
                "position_match_count": position_matches,
                "winning_number": winning_number,
            }
        )
        checked.append(row)
    return checked
