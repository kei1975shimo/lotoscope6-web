from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(path_text: str | Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return project_root() / path


def load_json(path_text: str | Path) -> Dict[str, Any]:
    path = resolve_path(path_text)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_csv_dicts(path_text: str | Path, encoding: str = "utf-8-sig") -> List[Dict[str, str]]:
    path = resolve_path(path_text)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    with path.open("r", encoding=encoding, newline="") as f:
        return list(csv.DictReader(f))


def write_csv_dicts(
    path_text: str | Path,
    rows: List[Dict[str, Any]],
    fieldnames: Sequence[str] | None = None,
    encoding: str = "utf-8-sig",
) -> Path:
    path = resolve_path(path_text)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    return path


def append_csv_dicts(
    path_text: str | Path,
    rows: List[Dict[str, Any]],
    fieldnames: Sequence[str],
    encoding: str = "utf-8-sig",
) -> Path:
    path = resolve_path(path_text)
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames))
        if not exists:
            writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    return path


def clean_number_list(text_or_numbers: str | Iterable[int] | None) -> List[int]:
    if text_or_numbers is None:
        return []
    if isinstance(text_or_numbers, str):
        normalized = (
            text_or_numbers.replace("，", ",")
            .replace("、", ",")
            .replace(" ", ",")
            .replace("\n", ",")
            .replace("\t", ",")
        )
        items = [x for x in normalized.split(",") if x.strip()]
    else:
        items = list(text_or_numbers)

    numbers: List[int] = []
    for item in items:
        try:
            n = int(str(item).strip())
        except ValueError:
            continue
        if 1 <= n <= 43 and n not in numbers:
            numbers.append(n)
    return sorted(numbers)


def main_numbers_from_row(row: Dict[str, Any]) -> List[int]:
    return [int(row[f"main_{i}"]) for i in range(1, 7)]


def count_odd_even(numbers: Sequence[int]) -> Tuple[int, int]:
    odd = sum(1 for n in numbers if n % 2 == 1)
    return odd, len(numbers) - odd


def zone_of_number(n: int) -> str:
    if 1 <= n <= 14:
        return "low"
    if 15 <= n <= 29:
        return "mid"
    return "high"


def count_zones(numbers: Sequence[int]) -> Tuple[int, int, int]:
    low = sum(1 for n in numbers if 1 <= n <= 14)
    mid = sum(1 for n in numbers if 15 <= n <= 29)
    high = sum(1 for n in numbers if 30 <= n <= 43)
    return low, mid, high


def count_over31(numbers: Sequence[int]) -> int:
    return sum(1 for n in numbers if n >= 32)


def count_consecutive_pairs(numbers: Sequence[int]) -> int:
    nums = sorted(numbers)
    return sum(1 for a, b in zip(nums, nums[1:]) if b == a + 1)


def count_same_tens_max(numbers: Sequence[int]) -> int:
    buckets: Dict[int, int] = {}
    for n in numbers:
        bucket = n // 10
        buckets[bucket] = buckets.get(bucket, 0) + 1
    return max(buckets.values()) if buckets else 0


def normalize_values(values_by_number: Dict[int, float]) -> Dict[int, float]:
    values = list(values_by_number.values())
    if not values:
        return {}
    mn = min(values)
    mx = max(values)
    if mx == mn:
        return {n: 50.0 for n in values_by_number}
    return {n: ((v - mn) / (mx - mn)) * 100.0 for n, v in values_by_number.items()}


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def round2(value: float) -> float:
    return round(float(value), 2)
