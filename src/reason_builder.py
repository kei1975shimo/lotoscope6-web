from __future__ import annotations

from typing import Any, Dict, Sequence


def build_reason(
    ticket: Sequence[int],
    mode_rule: Dict[str, Any],
    metrics: Dict[str, Any],
    pools: Dict[str, list[int]],
) -> str:
    ticket_set = set(int(n) for n in ticket)
    parts: list[str] = []

    mode_name_ja = mode_rule.get("mode_name_ja", mode_rule.get("mode_name", ""))
    parts.append(f"{mode_name_ja}の条件で作成した買い目です。")

    personal_count = int(metrics.get("personal_hit_count", 0))
    if personal_count >= 2:
        parts.append(f"入力した好きな数字を{personal_count}個含みます。")
    elif personal_count == 1:
        parts.append("入力した好きな数字を1個含みます。")

    over31_count = int(metrics.get("over31_count", 0))
    if over31_count >= 2:
        parts.append(f"32〜43の数字を{over31_count}個含み、1〜31だけに偏らない構成です。")
    elif over31_count == 1:
        parts.append("32〜43の数字を1個含みます。")

    odd_count = int(metrics.get("odd_count", 0))
    even_count = int(metrics.get("even_count", 0))
    if odd_count == 3:
        parts.append("奇数と偶数は3対3です。")
    else:
        parts.append(f"奇数{odd_count}個、偶数{even_count}個です。")

    set_sum = int(metrics.get("set_sum", 0))
    if 110 <= set_sum <= 160:
        parts.append(f"合計値は{set_sum}で、このツールの中心範囲（110〜160）に入っています。")
    else:
        parts.append(f"合計値は{set_sum}で、このツールの設定範囲（80〜190）に入っています。")

    if ticket_set & set(pools.get("cold_pool", [])):
        parts.append("最近の出現間隔が比較的長い数字を含みます。")

    if ticket_set & set(pools.get("hot_pool", [])):
        parts.append("直近30回で比較的多く出ている数字を含みます。")

    if int(metrics.get("consecutive_count", 0)) == 1:
        parts.append("連続する数字を1組含みます。")

    return "".join(parts)
