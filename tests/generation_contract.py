"""Fixed v1.17.2 samples: all methods, products and supported sizes."""
from datetime import date
import hashlib
import json

from app import build_daily_oracle_seed
from divination_numbers import calculate_divination_profile
from product_numbers import generate_product_rows, product_choices

BIRTHS = (date(1900, 1, 1), date(1975, 8, 16), date(2000, 2, 29), date(1992, 12, 31))
DAYS = (date(2026, 1, 1), date(2026, 9, 22), date(2026, 9, 23))
METHODS = ('astrology', 'kabbalah', 'tarot')

def samples(methods=METHODS):
    for birth in BIRTHS:
        for day in DAYS:
            for method in methods:
                profile = calculate_divination_profile(method, birth, day)
                for product in product_choices():
                    seed = build_daily_oracle_seed(birth, day, method, product['product_id'])
                    for size in range(1, product['full_size'] + 1):
                        key = '|'.join((birth.isoformat(), day.isoformat(), method, product['product_id'], str(size)))
                        yield key, product['product_id'], size, profile, seed

def digest(rows):
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def snapshot():
    return {key: digest(generate_product_rows(product, 10, profile, seed, pick_size=size))
            for key, product, size, profile, seed in samples()}
