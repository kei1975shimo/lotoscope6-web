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

    parts.append(f"{mode_name_ja}として、数字の偏りを抑えながら構成した買い目です。")

    if metrics.get("personal_hit_count", 0) >= 2:
        parts.append("好きな数字を複数取り入れています。")
    elif metrics.get("personal_hit_count", 0) == 1:
        parts.append("好きな数字を1個取り入れています。")

    if metrics.get("over31_count", 0) >= 2:
        parts.append("32以上の数字を複数含め、誕生日数字だけに寄りにくい形です。")
    elif metrics.get("over31_count", 0) == 1:
        parts.append("32以上の数字を1個含めています。")

    if metrics.get("odd_count") == 3:
        parts.append("奇数偶数は3:3で整っています。")
    elif metrics.get("odd_count") in (2, 4):
        parts.append("奇数偶数は極端になりすぎない範囲です。")

    if 110 <= int(metrics.get("set_sum", 0)) <= 160:
        parts.append("合計値も標準帯に収まっています。")
    else:
        parts.append("合計値は許容範囲内で、少し変化を持たせています。")

    if ticket_set & set(pools.get("cold_pool", [])):
        parts.append("未出現傾向のある数字も変化要素として取り入れています。")

    if ticket_set & set(pools.get("hot_pool", [])):
        parts.append("直近データで動きのある数字も含めています。")

    if int(metrics.get("consecutive_count", 0)) == 1:
        parts.append("連番を1組だけ含む変化型です。")

    return "".join(parts)
