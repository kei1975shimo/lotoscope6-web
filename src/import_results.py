from __future__ import annotations

from typing import Any, Dict, List

from utils import (
    count_consecutive_pairs,
    count_odd_even,
    count_over31,
    count_zones,
    main_numbers_from_row,
    read_csv_dicts,
    write_csv_dicts,
)


CLEANED_FIELDS = [
    "draw_no",
    "draw_date",
    "weekday",
    "main_1",
    "main_2",
    "main_3",
    "main_4",
    "main_5",
    "main_6",
    "bonus",
    "set_sum",
    "odd_count",
    "even_count",
    "low_count",
    "mid_count",
    "high_count",
    "over31_count",
    "consecutive_count",
    "source_url",
    "fetched_at",
]


def clean_draws(input_path: str, output_path: str | None = None) -> List[Dict[str, Any]]:
    raw_rows = read_csv_dicts(input_path)
    cleaned: List[Dict[str, Any]] = []

    seen_draws = set()

    for idx, row in enumerate(raw_rows, start=1):
        draw_no = int(row["draw_no"])
        if draw_no in seen_draws:
            raise ValueError(f"Duplicate draw_no: {draw_no}")
        seen_draws.add(draw_no)

        numbers = main_numbers_from_row(row)
        bonus = int(row["bonus"])

        if len(numbers) != 6:
            raise ValueError(f"Invalid main number count at row {idx}")
        if len(set(numbers)) != 6:
            raise ValueError(f"Duplicate main numbers at draw {draw_no}: {numbers}")
        if any(n < 1 or n > 43 for n in numbers + [bonus]):
            raise ValueError(f"Number out of range at draw {draw_no}: {numbers}, bonus={bonus}")

        numbers = sorted(numbers)
        odd_count, even_count = count_odd_even(numbers)
        low_count, mid_count, high_count = count_zones(numbers)

        clean_row: Dict[str, Any] = {
            "draw_no": draw_no,
            "draw_date": row.get("draw_date", ""),
            "weekday": row.get("weekday", ""),
            "main_1": numbers[0],
            "main_2": numbers[1],
            "main_3": numbers[2],
            "main_4": numbers[3],
            "main_5": numbers[4],
            "main_6": numbers[5],
            "bonus": bonus,
            "set_sum": sum(numbers),
            "odd_count": odd_count,
            "even_count": even_count,
            "low_count": low_count,
            "mid_count": mid_count,
            "high_count": high_count,
            "over31_count": count_over31(numbers),
            "consecutive_count": count_consecutive_pairs(numbers),
            "source_url": row.get("source_url", ""),
            "fetched_at": row.get("fetched_at", ""),
        }
        cleaned.append(clean_row)

    cleaned.sort(key=lambda r: int(r["draw_no"]))

    if output_path:
        write_csv_dicts(output_path, cleaned, CLEANED_FIELDS)

    return cleaned


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Clean Loto6 draw CSV.")
    parser.add_argument("--input", default="data/raw/loto6_results.csv")
    parser.add_argument("--output", default="data/processed/cleaned_draws.csv")
    args = parser.parse_args()

    rows = clean_draws(args.input, args.output)
    print(f"[DONE] cleaned rows: {len(rows)}")
    print(f"[DONE] saved: {args.output}")
