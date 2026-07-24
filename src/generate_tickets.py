from __future__ import annotations

import random
from typing import Any, Dict, List, MutableSet, Sequence

from pools import make_stats_lookup
from reason_builder import build_reason
from ticket_score import compute_ticket_score
from validate_ticket import validate_ticket

RandomSource = random.Random | random.SystemRandom


def weighted_pick(
    pool: Sequence[int],
    stats_lookup: Dict[int, Dict[str, Any]],
    score_key: str,
    selected: set[int],
    rng: RandomSource,
) -> int | None:
    candidates = [int(n) for n in pool if int(n) not in selected]
    if not candidates:
        return None

    weights = []
    for n in candidates:
        value = float(stats_lookup[n].get(score_key, 0) or 0)
        weights.append(max(1.0, value + 1.0))

    return rng.choices(candidates, weights=weights, k=1)[0]


def add_numbers(
    ticket: set[int],
    pool: Sequence[int],
    count: int,
    stats_lookup: Dict[int, Dict[str, Any]],
    score_key: str,
    rng: RandomSource,
) -> None:
    for _ in range(max(0, count)):
        picked = weighted_pick(pool, stats_lookup, score_key, ticket, rng)
        if picked is None:
            return
        ticket.add(picked)


def random_count(rule: Dict[str, Any], prefix: str, rng: RandomSource) -> int:
    mn = int(rule.get(f"{prefix}_min", 0))
    mx = int(rule.get(f"{prefix}_max", mn))
    if mx < mn:
        mx = mn
    return rng.randint(mn, mx)


def build_one_ticket(
    mode_id: str,
    mode_rule: Dict[str, Any],
    pools: Dict[str, List[int]],
    number_stats: List[Dict[str, Any]],
    balance_rules: Dict[str, Any],
    astrology_numbers: List[int],
    rng: RandomSource,
) -> Dict[str, Any] | None:
    stats_lookup = make_stats_lookup(number_stats)
    ticket: set[int] = set()

    add_numbers(ticket, pools.get("astrology_core_pool", []), random_count(mode_rule, "astrology_core", rng), stats_lookup, "astrology_score", rng)
    add_numbers(ticket, pools.get("astrology_pool", []), random_count(mode_rule, "astrology", rng), stats_lookup, "astrology_score", rng)
    add_numbers(ticket, pools["data_pool"], random_count(mode_rule, "data", rng), stats_lookup, "base_data_score", rng)
    add_numbers(ticket, pools["cold_pool"], random_count(mode_rule, "cold", rng), stats_lookup, "absence_score", rng)
    add_numbers(ticket, pools["over31_pool"], random_count(mode_rule, "over31", rng), stats_lookup, "base_data_score", rng)

    while len(ticket) < 6:
        picked = weighted_pick(pools["all_pool"], stats_lookup, "base_data_score", ticket, rng)
        if picked is None:
            break
        ticket.add(picked)

    nums = sorted(ticket)
    ok, _errors, _metrics = validate_ticket(nums, balance_rules)
    if not ok:
        return None

    score_info = compute_ticket_score(nums, stats_lookup, astrology_numbers)
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
    astrology_numbers: List[int] | None = None,
    rng: RandomSource | None = None,
    seen: MutableSet[tuple[int, ...]] | None = None,
) -> List[Dict[str, Any]]:
    if mode_id not in mode_rules:
        raise ValueError(f"Unknown mode_id: {mode_id}")

    mode_rule = mode_rules[mode_id]
    max_attempts = int(balance_rules.get("max_attempts", 3000))
    random_source = rng or random.SystemRandom()
    shared_seen = seen if seen is not None else set()

    tickets: List[Dict[str, Any]] = []
    attempts = 0

    while len(tickets) < ticket_count and attempts < max_attempts:
        attempts += 1
        ticket = build_one_ticket(
            mode_id,
            mode_rule,
            pools,
            number_stats,
            balance_rules,
            list(astrology_numbers or []),
            random_source,
        )
        if ticket is None:
            continue

        key = tuple(ticket["numbers"])
        if key in shared_seen:
            continue

        shared_seen.add(key)
        ticket["attempt_no"] = attempts
        tickets.append(ticket)

    return tickets
