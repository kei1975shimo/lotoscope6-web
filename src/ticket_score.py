from __future__ import annotations

from typing import Any, Dict, Sequence

from utils import round2
from validate_ticket import ticket_metrics


def data_score_average(ticket: Sequence[int], stats_lookup: Dict[int, Dict[str, Any]]) -> float:
    scores = [float(stats_lookup[int(n)].get("base_data_score", 0) or 0) for n in ticket]
    return sum(scores) / len(scores) if scores else 0.0


def balance_fit_score(metrics: Dict[str, Any]) -> float:
    score = 100.0

    if metrics["odd_count"] == 3:
        pass
    elif metrics["odd_count"] in (2, 4):
        score -= 5
    else:
        score -= 25

    if 110 <= metrics["set_sum"] <= 160:
        pass
    elif 80 <= metrics["set_sum"] <= 190:
        score -= 10
    else:
        score -= 30

    if metrics["consecutive_count"] == 1:
        score -= 3
    elif metrics["consecutive_count"] > 1:
        score -= 20

    if metrics["low_count"] == 0 or metrics["mid_count"] == 0 or metrics["high_count"] == 0:
        score -= 20

    if metrics["over31_count"] == 0:
        score -= 20

    if metrics.get("same_tens_max", 0) > 3:
        score -= 10

    return max(0.0, min(100.0, score))


def personal_fit_score(personal_hit_count: int) -> float:
    if personal_hit_count <= 0:
        return 40.0
    if personal_hit_count == 1:
        return 70.0
    if personal_hit_count == 2:
        return 100.0
    if personal_hit_count == 3:
        return 90.0
    return 60.0


def uniqueness_score(over31_count: int) -> float:
    if over31_count <= 0:
        return 30.0
    if over31_count == 1:
        return 70.0
    if over31_count == 2:
        return 100.0
    return 90.0


def compute_ticket_score(
    ticket: Sequence[int],
    stats_lookup: Dict[int, Dict[str, Any]],
    favorite_numbers: Sequence[int] | None = None,
) -> Dict[str, Any]:
    metrics = ticket_metrics(ticket, favorite_numbers)
    d_avg = data_score_average(ticket, stats_lookup)
    b_score = balance_fit_score(metrics)
    p_score = personal_fit_score(metrics["personal_hit_count"])
    u_score = uniqueness_score(metrics["over31_count"])

    ticket_score = d_avg * 0.40 + b_score * 0.30 + p_score * 0.15 + u_score * 0.15

    return {
        "data_score_avg": round2(d_avg),
        "balance_fit_score": round2(b_score),
        "personal_fit_score": round2(p_score),
        "uniqueness_score": round2(u_score),
        "ticket_score": round2(ticket_score),
        **metrics,
    }
