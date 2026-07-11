from __future__ import annotations

import random
from typing import Any, Dict, List, Sequence

from pools import make_stats_lookup
from reason_builder import build_reason
from ticket_score import compute_ticket_score
from validate_ticket import validate_ticket


def weighted_pick(
    pool: Sequence[int],
    stats_lookup: Dict[int, Dict[str, Any]],
    score_key: str,
    selected: set[int],
) -> int | None:
    candidates = [int(n) for n in pool if int(n) not in selected]
    if not candidates:
        return None

    weights = []
    for n in candidates:
        value = float(stats_lookup[n].get(score_key, 0) or 0)
        weights.append(max(1.0, value + 1.0))

    return random.choices(candidates, weights=weights, k=1)[0]


def add_numbers(
    ticket: set[int],
    pool: Sequence[int],
    count: int,
    stats_lookup: Dict[int, Dict[str, Any]],
    score_key: str,
) -> None:
    for _ in range(max(0, count)):
        picked = weighted_pick(pool, stats_lookup, score_key, ticket)
        if picked is None:
            return
        ticket.add(picked)


def random_count(rule: Dict[str, Any], prefix: str) -> int:
    mn = int(rule.get(f"{prefix}_min", 0))
    mx = int(rule.get(f"{prefix}_max", mn))
    if mx < mn:
        mx = mn
    return random.randint(mn, mx)


def build_one_ticket(
    mode_id: str,
    mode_rule: Dict[str, Any],
    pools: Dict[str, List[int]],
    number_stats: List[Dict[str, Any]],
    balance_rules: Dict[str, Any],
    favorite_numbers: List[int],
) -> Dict[str, Any] | None:
    stats_lookup = make_stats_lookup(number_stats)
    ticket: set[int] = set()

    # Mode-based candidate composition.
    add_numbers(ticket, pools["personal_pool"], random_count(mode_rule, "personal"), stats_lookup, "base_data_score")
    add_numbers(ticket, pools["data_pool"], random_count(mode_rule, "data"), stats_lookup, "base_data_score")
    add_numbers(ticket, pools["cold_pool"], random_count(mode_rule, "cold"), stats_lookup, "absence_score")
    add_numbers(ticket, pools["over31_pool"], random_count(mode_rule, "over31"), stats_lookup, "base_data_score")

    # Fill up to 6 numbers.
    while len(ticket) < 6:
        picked = weighted_pick(pools["all_pool"], stats_lookup, "base_data_score", ticket)
        if picked is None:
            break
        ticket.add(picked)

    nums = sorted(ticket)
    ok, errors, metrics = validate_ticket(nums, balance_rules, favorite_numbers, mode_rule)
    if not ok:
        return None

    score_info = compute_ticket_score(nums, stats_lookup, favorite_numbers)
    reason = build_reason(nums, mode_rule, score_info, pools)

    return {
        "mode_id": mode_id,
        "mode_name": mode_rule.get("mode_name", mode_id),
        "mode_name_ja": mode_rule.get("mode_name_ja", ""),
        "numbers": nums,
        "reason": reason,
        **score_info,
    }


def generate_tickets(
    mode_id: str,
    ticket_count: int,
    pools: Dict[str, List[int]],
    number_stats: List[Dict[str, Any]],
    mode_rules: Dict[str, Any],
    balance_rules: Dict[str, Any],
    favorite_numbers: List[int],
) -> List[Dict[str, Any]]:
    if mode_id not in mode_rules:
        raise ValueError(f"Unknown mode_id: {mode_id}")

    mode_rule = mode_rules[mode_id]
    max_attempts = int(balance_rules.get("max_attempts", 3000))

    tickets: List[Dict[str, Any]] = []
    seen: set[tuple[int, ...]] = set()
    attempts = 0

    while len(tickets) < ticket_count and attempts < max_attempts:
        attempts += 1
        ticket = build_one_ticket(mode_id, mode_rule, pools, number_stats, balance_rules, favorite_numbers)
        if ticket is None:
            continue

        key = tuple(ticket["numbers"])
        if key in seen:
            continue

        seen.add(key)
        ticket["attempt_no"] = attempts
        tickets.append(ticket)

    return tickets
