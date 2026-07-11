from __future__ import annotations

from typing import Dict, List, Any

from utils import normalize_values, round2


def apply_scores(stats_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_number: Dict[int, Dict[str, Any]] = {int(r["number"]): r for r in stats_rows}

    total_values = {n: float(r["total_count"]) for n, r in by_number.items()}
    recent30_values = {n: float(r["recent_30_count"]) for n, r in by_number.items()}
    recent100_values = {n: float(r["recent_100_count"]) for n, r in by_number.items()}
    absence_values = {n: float(r["absence_count"]) for n, r in by_number.items()}
    bonus_values = {n: float(r["bonus_count"]) for n, r in by_number.items()}

    frequency = normalize_values(total_values)
    recent = normalize_values(recent30_values)
    midterm = normalize_values(recent100_values)
    absence = normalize_values(absence_values)
    bonus = normalize_values(bonus_values)

    scored: List[Dict[str, Any]] = []
    for n in range(1, 44):
        row = dict(by_number[n])
        frequency_score = frequency[n]
        recent_score = recent[n]
        midterm_score = midterm[n]
        absence_score = absence[n]
        bonus_score = bonus[n]

        base_data_score = (
            frequency_score * 0.25
            + recent_score * 0.25
            + midterm_score * 0.20
            + absence_score * 0.20
            + bonus_score * 0.10
        )

        row.update(
            {
                "frequency_score": round2(frequency_score),
                "recent_score": round2(recent_score),
                "midterm_score": round2(midterm_score),
                "absence_score": round2(absence_score),
                "bonus_score": round2(bonus_score),
                "base_data_score": round2(base_data_score),
            }
        )
        scored.append(row)

    return scored
