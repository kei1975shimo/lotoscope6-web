from __future__ import annotations

from typing import Any, Dict, List, Set

from utils import clean_number_list


def make_stats_lookup(number_stats: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    return {int(r["number"]): r for r in number_stats}


def sort_numbers_by_score(number_stats: List[Dict[str, Any]], score_key: str, limit: int | None = None) -> List[int]:
    rows = sorted(number_stats, key=lambda r: float(r.get(score_key, 0) or 0), reverse=True)
    numbers = [int(r["number"]) for r in rows]
    return numbers if limit is None else numbers[:limit]


def build_pools(
    number_stats: List[Dict[str, Any]],
    favorite_numbers: List[int] | str | None = None,
    avoided_numbers: List[int] | str | None = None,
) -> Dict[str, List[int]]:
    favorites = clean_number_list(favorite_numbers)
    avoided = set(clean_number_list(avoided_numbers))

    favorites = [n for n in favorites if n not in avoided]
    all_allowed = [n for n in range(1, 44) if n not in avoided]

    data_pool = [n for n in sort_numbers_by_score(number_stats, "base_data_score", 18) if n not in avoided]
    hot_pool = [n for n in sort_numbers_by_score(number_stats, "recent_score", 12) if n not in avoided]
    cold_pool = [n for n in sort_numbers_by_score(number_stats, "absence_score", 12) if n not in avoided]
    over31_pool = [n for n in range(32, 44) if n not in avoided]

    return {
        "personal_pool": favorites,
        "data_pool": data_pool,
        "hot_pool": hot_pool,
        "cold_pool": cold_pool,
        "over31_pool": over31_pool,
        "all_pool": all_allowed,
        "avoided_numbers": sorted(avoided),
    }
