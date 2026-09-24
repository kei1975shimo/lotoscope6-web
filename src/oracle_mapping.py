"""Lottery adaptation, explicitly separate from the divination traditions.

Every weight is the sum of evidence contributions. No birthday hash, uniform
filler or lottery-composition filter contributes to these weights.
"""
from math import floor


def root9(value):
    return (abs(int(value)) - 1) % 9 + 1


def fold(value, size):
    return (int(value) - 1) % size + 1


def circle_distance(a, b, size):
    distance = abs(a - b) % size
    return min(distance, size - distance)


def correspondence(profile, size=43, minimum=1):
    """Return weights and the strongest, auditable contribution per number.

    Circular inverse-square proximity is OUR interpolation rule, not a
    historical claim. It leaves the whole legal range available, including 0
    for Numbers and 23..43 for Loto6. Strengths only express symbolic affinity.
    """
    weights, origins = {}, {}
    for index in range(1, size + 1):
        number = index + minimum - 1
        parts = []
        for item in profile['oracle_evidence']:
            kind, value = item['kind'], item['value']
            strength = item.get('strength', 1.0)
            if kind == 'longitude':
                anchor = floor((value % 360) * size / 360) + 1
                distance = circle_distance(index, anchor, size)
                detail = f"黄経 {value:.2f}° → {size}区分の {anchor + minimum - 1}、距離 {distance}"
                affinity = strength / (1 + distance) ** 2
            elif kind == 'arcana':
                anchor = fold(value, size)
                distance = circle_distance(index, anchor, size)
                detail = f"対応値 {value} → {anchor + minimum - 1}、循環距離 {distance}"
                affinity = strength / (1 + distance) ** 2
            else:
                # Numerology acts on the actual lottery integer, not a
                # rescaled 43-bin index. Zero is explicitly represented by 10.
                numeric = number if number else 10
                reduced = root9(numeric)
                distance = circle_distance(reduced, root9(value), 9)
                affinity = strength / (1 + distance) ** 2
                if number == value and value in (11, 22, 33):
                    affinity *= 2
                detail = f"{'0を10として扱い、' if number == 0 else ''}還元数 {reduced} ／ 基礎数 {value}（還元 {root9(value)}）、循環距離 {distance}"
            parts.append((affinity, item['label'], detail))
        weights[number] = sum(p[0] for p in parts)
        strongest = max(parts, key=lambda p: p[0])
        origins[number] = {'number': number, 'source': strongest[1], 'detail': strongest[2]}
    return weights, origins


def finish_profile(profile):
    weights, _ = correspondence(profile)
    ranked = sorted(weights, key=lambda n: (-weights[n], n))
    profile.update(weights=weights, core_numbers=sorted(ranked[:6]), pool_numbers=ranked,
                   boost_rows=[], engine_version='1.18.0')
    return profile
