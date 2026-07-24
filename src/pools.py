from __future__ import annotations

from typing import Any, Dict, List

from utils import clean_number_list


def make_stats_lookup(number_stats: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    return {int(r["number"]): r for r in number_stats}


def sort_numbers_by_score(number_stats: List[Dict[str, Any]], score_key: str, limit: int | None = None) -> List[int]:
    rows = sorted(number_stats, key=lambda r: float(r.get(score_key, 0) or 0), reverse=True)
    numbers = [int(r["number"]) for r in rows]
    return numbers if limit is None else numbers[:limit]


def build_pools(
    number_stats: List[Dict[str, Any]],
    astrology_numbers: List[int] | str | None = None,
    astrology_pool: List[int] | str | None = None,
) -> Dict[str, List[int]]:
    astrology_core = clean_number_list(astrology_numbers)
    astrology_candidates = clean_number_list(astrology_pool)

    return {
        "data_pool": sort_numbers_by_score(number_stats, "base_data_score", 18),
        "hot_pool": sort_numbers_by_score(number_stats, "recent_score", 12),
        "cold_pool": sort_numbers_by_score(number_stats, "absence_score", 12),
        "over31_pool": list(range(32, 44)),
        "astrology_core_pool": astrology_core,
        "astrology_pool": astrology_candidates,
        "all_pool": list(range(1, 44)),
    }
