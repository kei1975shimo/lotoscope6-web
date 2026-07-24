from __future__ import annotations

from typing import Any, Dict, Sequence


def build_reason(
    ticket: Sequence[int],
    mode_rule: Dict[str, Any],
    metrics: Dict[str, Any],
    pools: Dict[str, list[int]],
) -> str:
    """Build a warm, fortune-reader-style explanation without making predictions."""
    ticket_set = set(int(n) for n in ticket)
    parts: list[str] = []

    mode_name_ja = mode_rule.get("mode_name_ja", mode_rule.get("mode_name", ""))
    parts.append(f"この組み合わせは、『{mode_name_ja}』の流れから現れました。")

    astrology_count = int(metrics.get("astrology_hit_count", 0))
    if astrology_count >= 2:
        parts.append(f"あなたの誕生星と今日の天体に響いた数字が、{astrology_count}個静かに重なっています。")
    elif astrology_count == 1:
        parts.append("あなたの誕生星と今日の天体に響いた数字が、ひとつそっと含まれています。")

    over31_count = int(metrics.get("over31_count", 0))
    if over31_count >= 2:
        parts.append(f"32〜43の数字にも{over31_count}個の光が当たり、誕生日数字だけに寄りすぎない広がりがあります。")
    elif over31_count == 1:
        parts.append("32〜43からもひとつ数字が加わり、組み合わせに小さな広がりを与えています。")

    odd_count = int(metrics.get("odd_count", 0))
    even_count = int(metrics.get("even_count", 0))
    if odd_count == 3:
        parts.append("奇数と偶数は3対3。左右の天秤が穏やかに釣り合うような並びです。")
    else:
        parts.append(f"奇数{odd_count}個、偶数{even_count}個。少し個性を残したリズムになっています。")

    set_sum = int(metrics.get("set_sum", 0))
    if 110 <= set_sum <= 160:
        parts.append(f"六つの合計は{set_sum}。この星読みで中心とする穏やかな範囲に収まっています。")
    else:
        parts.append(f"六つの合計は{set_sum}。中心から少し離れた、印象に残る流れです。")

    if ticket_set & set(pools.get("cold_pool", [])):
        parts.append("しばらく姿を見せていない数字も含まれ、静かな変化の気配があります。")

    if ticket_set & set(pools.get("hot_pool", [])):
        parts.append("最近よく姿を見せている数字も加わり、今の流れを感じさせます。")

    if int(metrics.get("consecutive_count", 0)) == 1:
        parts.append("連続する二つの数字が寄り添い、ひとつの物語を作っています。")

    return "".join(parts)
