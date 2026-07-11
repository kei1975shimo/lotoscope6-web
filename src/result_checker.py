from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from utils import now_stamp, resolve_path


def judge_rank(match_count: int, bonus_match: bool) -> str:
    if match_count == 6:
        return "1"
    if match_count == 5 and bonus_match:
        return "2"
    if match_count == 5:
        return "3"
    if match_count == 4:
        return "4"
    if match_count == 3:
        return "5"
    return ""


def rank_label(rank: str) -> str:
    return {
        "1": "1等",
        "2": "2等",
        "3": "3等",
        "4": "4等",
        "5": "5等",
        "": "等級なし",
    }.get(str(rank), "等級なし")


def check_ticket(ticket: Sequence[int], main_numbers: Sequence[int], bonus: int) -> dict:
    ticket_set = set(int(n) for n in ticket)
    main_set = set(int(n) for n in main_numbers)
    match_count = len(ticket_set & main_set)
    bonus_match = int(bonus) in ticket_set
    rank = judge_rank(match_count, bonus_match)
    return {
        "match_count": match_count,
        "bonus_match": 1 if bonus_match else 0,
        "prize_rank": rank,
        "prize_rank_label": rank_label(rank),
    }


def ticket_numbers_from_row(row: Dict[str, Any]) -> List[int]:
    nums: List[int] = []
    for i in range(1, 7):
        value = row.get(f"n{i}", "")
        try:
            nums.append(int(float(value)))
        except Exception:
            nums.append(0)
    return nums


def normalize_main_numbers(numbers: Sequence[int]) -> List[int]:
    cleaned: List[int] = []
    for n in numbers:
        try:
            i = int(n)
        except Exception:
            continue
        if 1 <= i <= 43 and i not in cleaned:
            cleaned.append(i)
    if len(cleaned) != 6:
        raise ValueError("本数字は1〜43の範囲で、重複なしの6個を入力してください。")
    return sorted(cleaned)


def normalize_bonus_number(value: int) -> int:
    try:
        n = int(value)
    except Exception as exc:
        raise ValueError("ボーナス数字を1〜43で入力してください。") from exc
    if not 1 <= n <= 43:
        raise ValueError("ボーナス数字を1〜43で入力してください。")
    return n


def validate_draw_numbers(main_numbers: Sequence[int], bonus: int) -> tuple[List[int], int]:
    main = normalize_main_numbers(main_numbers)
    bonus_n = normalize_bonus_number(bonus)
    if bonus_n in main:
        raise ValueError("ボーナス数字は本数字と異なる数字である必要があります。")
    return main, bonus_n


def read_csv_rows(path: str | Path, encoding: str = "utf-8-sig") -> List[Dict[str, Any]]:
    p = resolve_path(path)
    if not p.exists():
        raise FileNotFoundError(f"CSV file not found: {p}")
    with p.open("r", encoding=encoding, newline="") as f:
        return list(csv.DictReader(f))


def load_draw_by_no(draw_no: int, draws_path: str | Path = "data/raw/loto6_results.csv") -> Dict[str, Any]:
    rows = read_csv_rows(draws_path)
    target = str(int(draw_no))
    for row in rows:
        if str(row.get("draw_no", "")).strip() == target:
            return row
    raise ValueError(f"第{draw_no}回の抽せん結果は、同梱データ内に見つかりません。")


def load_latest_draw(draws_path: str | Path = "data/raw/loto6_results.csv") -> Dict[str, Any]:
    rows = read_csv_rows(draws_path)
    if not rows:
        raise ValueError("抽せん結果CSVが空です。")
    def _draw_no(row: Dict[str, Any]) -> int:
        try:
            return int(row.get("draw_no", 0))
        except Exception:
            return 0
    return max(rows, key=_draw_no)


def draw_numbers_from_row(row: Dict[str, Any]) -> Tuple[List[int], int]:
    main = [int(float(row.get(f"main_{i}", 0))) for i in range(1, 7)]
    bonus = int(float(row.get("bonus", 0)))
    return validate_draw_numbers(main, bonus)


def check_ticket_rows(
    ticket_rows: List[Dict[str, Any]],
    main_numbers: Sequence[int],
    bonus: int,
    draw_no: str = "",
    draw_date: str = "",
) -> List[Dict[str, Any]]:
    main, bonus_n = validate_draw_numbers(main_numbers, bonus)
    checked_at = now_stamp()
    checked_rows: List[Dict[str, Any]] = []
    for row in ticket_rows:
        ticket = ticket_numbers_from_row(row)
        result = check_ticket(ticket, main, bonus_n)
        new_row = dict(row)
        new_row.update({
            "checked_at": checked_at,
            "checked_draw_no": str(draw_no or ""),
            "checked_draw_date": str(draw_date or ""),
            "draw_main_numbers": ",".join(str(n) for n in main),
            "draw_bonus": str(bonus_n),
            "match_count": str(result["match_count"]),
            "bonus_match": "1" if result["bonus_match"] else "0",
            "prize_rank": result["prize_rank"],
            "prize_rank_label": result["prize_rank_label"],
        })
        checked_rows.append(new_row)
    return checked_rows


def write_checked_csv(rows: List[Dict[str, Any]], output_dir: str | Path = "output/checks") -> Path:
    out_dir = resolve_path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"lotoscope6_checked_{now_stamp()}.csv"
    if not rows:
        raise ValueError("No checked rows to save.")
    fieldnames: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return out_path


def check_ticket_csv(
    ticket_csv_path: str | Path,
    main_numbers: Sequence[int],
    bonus: int,
    draw_no: str = "",
    draw_date: str = "",
    output_dir: str | Path = "output/checks",
) -> Tuple[List[Dict[str, Any]], Path]:
    rows = read_csv_rows(ticket_csv_path)
    checked_rows = check_ticket_rows(rows, main_numbers, bonus, draw_no=draw_no, draw_date=draw_date)
    checked_path = write_checked_csv(checked_rows, output_dir=output_dir)
    return checked_rows, checked_path


if __name__ == "__main__":
    print("[INFO] result_checker.py is a helper module for Lotoscope6 result check workflows.")
