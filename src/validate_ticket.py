from __future__ import annotations

from typing import Any, Dict, List, Sequence

from utils import (
    count_consecutive_pairs,
    count_odd_even,
    count_over31,
    count_same_tens_max,
    count_zones,
)


def ticket_metrics(
    ticket: Sequence[int],
    astrology_numbers: Sequence[int] | None = None,
) -> Dict[str, Any]:
    nums = sorted(int(n) for n in ticket)
    astrology_set = set(astrology_numbers or [])

    odd_count, even_count = count_odd_even(nums)
    low_count, mid_count, high_count = count_zones(nums)

    return {
        "n1": nums[0] if len(nums) > 0 else "",
        "n2": nums[1] if len(nums) > 1 else "",
        "n3": nums[2] if len(nums) > 2 else "",
        "n4": nums[3] if len(nums) > 3 else "",
        "n5": nums[4] if len(nums) > 4 else "",
        "n6": nums[5] if len(nums) > 5 else "",
        "set_sum": sum(nums),
        "odd_count": odd_count,
        "even_count": even_count,
        "low_count": low_count,
        "mid_count": mid_count,
        "high_count": high_count,
        "over31_count": count_over31(nums),
        "consecutive_count": count_consecutive_pairs(nums),
        "same_tens_max": count_same_tens_max(nums),
        "astrology_hit_count": sum(1 for n in nums if n in astrology_set),
    }


def validate_ticket(
    ticket: Sequence[int],
    balance_rules: Dict[str, Any],
) -> tuple[bool, List[str], Dict[str, Any]]:
    errors: List[str] = []
    nums = sorted(int(n) for n in ticket)

    if len(nums) != 6:
        errors.append("number_count")
    if len(set(nums)) != len(nums):
        errors.append("duplicate")
    if any(n < 1 or n > 43 for n in nums):
        errors.append("range")

    if errors:
        return False, errors, {}

    metrics = ticket_metrics(nums)

    if metrics["set_sum"] < int(balance_rules.get("min_sum", 80)):
        errors.append("sum_low")
    if metrics["set_sum"] > int(balance_rules.get("max_sum", 190)):
        errors.append("sum_high")
    if metrics["odd_count"] not in set(balance_rules.get("allowed_odd_counts", [2, 3, 4])):
        errors.append("odd_even")
    if metrics["low_count"] < int(balance_rules.get("min_low_count", 1)):
        errors.append("low_missing")
    if metrics["mid_count"] < int(balance_rules.get("min_mid_count", 1)):
        errors.append("mid_missing")
    if metrics["high_count"] < int(balance_rules.get("min_high_count", 1)):
        errors.append("high_missing")
    if metrics["over31_count"] < int(balance_rules.get("min_over31_count", 1)):
        errors.append("over31_missing")
    if metrics["consecutive_count"] > int(balance_rules.get("max_consecutive_pairs", 1)):
        errors.append("too_many_consecutive")
    if metrics["same_tens_max"] > int(balance_rules.get("max_same_tens_count", 3)):
        errors.append("same_tens_bias")

    return len(errors) == 0, errors, metrics
