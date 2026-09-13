"""Reproducible 120 birthdays × 3 methods × 5 lotteries, including prefixes."""
import sys
from datetime import date, timedelta
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import build_daily_oracle_seed
from divination_numbers import calculate_divination_profile, divination_choices
from product_numbers import generate_product_rows, product_choices


def main():
    start = perf_counter()
    cases = 0
    day = date(2026, 9, 13)
    for index in range(120):
        birth = date(1900, 1, 1) + timedelta(days=index * 367)
        for method in divination_choices():
            profile = calculate_divination_profile(method['divination_id'], birth, day)
            for product in product_choices():
                seed = build_daily_oracle_seed(birth, day, method['divination_id'], product['product_id'])
                full = generate_product_rows(product['product_id'], 10, profile, seed)
                assert len(full) == 10 and len({tuple(row['numbers']) for row in full}) == 10
                for count in (1, 3, 5):
                    assert generate_product_rows(product['product_id'], count, profile, seed) == full[:count]
                for row in full:
                    if product['kind'] == 'loto':
                        assert len(set(row['numbers'])) == product['pick_count']
                        assert all(1 <= n <= product['max_number'] for n in row['numbers'])
                    else:
                        assert len(row['numbers']) == product['digit_count']
                        assert all(0 <= n <= 9 for n in row['numbers'])
                cases += 1
    print(f'PASS: {cases} cases, {cases * 4} generation calls, prefixes 1/3/5/10; {perf_counter() - start:.3f}s')


if __name__ == '__main__':
    main()
