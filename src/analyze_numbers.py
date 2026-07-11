from __future__ import annotations

from typing import Any, Dict, List

from import_results import clean_draws
from scoring import apply_scores
from utils import main_numbers_from_row, write_csv_dicts, zone_of_number


NUMBER_STATS_FIELDS = [
    "number",
    "total_count",
    "bonus_count",
    "recent_30_count",
    "recent_100_count",
    "last_seen_draw_no",
    "absence_count",
    "odd_even",
    "zone",
    "is_over31",
    "frequency_score",
    "recent_score",
    "midterm_score",
    "absence_score",
    "bonus_score",
    "base_data_score",
]


def build_number_stats(
    raw_results_path: str = "data/raw/loto6_results.csv",
    cleaned_output_path: str = "data/processed/cleaned_draws.csv",
    stats_output_path: str = "data/processed/number_stats.csv",
) -> List[Dict[str, Any]]:
    draws = clean_draws(raw_results_path, cleaned_output_path)
    if not draws:
        raise ValueError("No draw data.")

    draws.sort(key=lambda r: int(r["draw_no"]))
    latest_draw_no = int(draws[-1]["draw_no"])
    recent_30 = draws[-30:]
    recent_100 = draws[-100:]

    stats_rows: List[Dict[str, Any]] = []

    for n in range(1, 44):
        total_count = 0
        bonus_count = 0
        recent_30_count = 0
        recent_100_count = 0
        last_seen_draw_no = 0

        for row in draws:
            draw_no = int(row["draw_no"])
            nums = main_numbers_from_row(row)
            if n in nums:
                total_count += 1
                last_seen_draw_no = draw_no
            if int(row["bonus"]) == n:
                bonus_count += 1

        for row in recent_30:
            if n in main_numbers_from_row(row):
                recent_30_count += 1

        for row in recent_100:
            if n in main_numbers_from_row(row):
                recent_100_count += 1

        absence_count = latest_draw_no - last_seen_draw_no if last_seen_draw_no else latest_draw_no

        stats_rows.append(
            {
                "number": n,
                "total_count": total_count,
                "bonus_count": bonus_count,
                "recent_30_count": recent_30_count,
                "recent_100_count": recent_100_count,
                "last_seen_draw_no": last_seen_draw_no,
                "absence_count": absence_count,
                "odd_even": "odd" if n % 2 else "even",
                "zone": zone_of_number(n),
                "is_over31": 1 if n >= 32 else 0,
            }
        )

    scored_rows = apply_scores(stats_rows)
    write_csv_dicts(stats_output_path, scored_rows, NUMBER_STATS_FIELDS)
    return scored_rows


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze Loto6 numbers and create number_stats.csv.")
    parser.add_argument("--input", default="data/raw/loto6_results.csv")
    parser.add_argument("--cleaned-output", default="data/processed/cleaned_draws.csv")
    parser.add_argument("--stats-output", default="data/processed/number_stats.csv")
    args = parser.parse_args()

    rows = build_number_stats(args.input, args.cleaned_output, args.stats_output)
    print(f"[DONE] number stats rows: {len(rows)}")
    print(f"[DONE] saved: {args.stats_output}")
