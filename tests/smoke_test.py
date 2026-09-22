from __future__ import annotations

import os
import re
import unittest
from datetime import date

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")

from app import app, build_daily_oracle_seed  # noqa: E402
from divination_numbers import calculate_divination_profile, divination_choices  # noqa: E402
from product_numbers import generate_product_rows, product_choices  # noqa: E402


class LotoScopeSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        app.config.update(TESTING=True, TEST_PREMIUM_ACCESS=True, SESSION_COOKIE_SECURE=False)
        self.client = app.test_client()

    @staticmethod
    def csrf(html: str) -> str:
        match = re.search(r'name="csrf_token" value="([^"]+)"', html)
        assert match
        return match.group(1)

    def get_index(self) -> tuple[str, str]:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        return html, self.csrf(html)

    def generate(self, product: str = "loto6", count: str = "2", divination: str = "astrology"):
        html, csrf = self.get_index()
        return self.client.post(
            "/generate",
            data={
                "csrf_token": csrf,
                "divination": divination,
                "product": product,
                "count": count,
                "birth_date": "1975-08-16",
            },
        )

    def test_index_lists_all_divinations_and_products(self) -> None:
        html, _ = self.get_index()
        for divination in ["西洋占星術", "カバラ数秘術", "タロット"]:
            self.assertIn(divination, html)
        for product in ["ミニロト", "ロト6", "ロト7", "ナンバーズ3", "ナンバーズ4"]:
            self.assertIn(product, html)
        self.assertRegex(html, r'name="divination" value="astrology"[^>]*checked')
        self.assertRegex(html, r'name="product" value="loto6"[^>]*checked')

    def test_choice_orders(self) -> None:
        self.assertEqual([item["divination_id"] for item in divination_choices()], ["astrology", "kabbalah", "tarot"])
        self.assertEqual([item["product_id"] for item in product_choices()], ["miniloto", "loto6", "loto7", "numbers3", "numbers4"])

    def test_each_divination_builds_profile(self) -> None:
        for method_id in ["astrology", "kabbalah", "tarot"]:
            with self.subTest(method_id=method_id):
                profile = calculate_divination_profile(method_id, date(1975, 8, 16), date(2026, 8, 26))
                self.assertEqual(profile["method_id"], method_id)
                self.assertGreaterEqual(len(profile["core_numbers"]), 6)
                self.assertTrue(profile["weights"])
                self.assertEqual(len(profile["summary_items"]), 3)
                self.assertTrue(profile["detail_rows"])

    def test_all_divinations_generate_different_weighted_results(self) -> None:
        results = {}
        for method_id in ["astrology", "kabbalah", "tarot"]:
            profile = calculate_divination_profile(method_id, date(1975, 8, 16), date(2026, 8, 26))
            rows = generate_product_rows("loto6", 2, profile, seed="same-seed")
            results[method_id] = [row["numbers"] for row in rows]
            self.assertTrue(all("reference_numbers" in row for row in rows))
            self.assertTrue(all("divination_fit_score" in row for row in rows))
        self.assertGreater(len({str(value) for value in results.values()}), 1)


    def test_daily_oracle_seed_is_stable_and_changes_next_day(self) -> None:
        birth = date(1975, 8, 16)
        today = date(2026, 8, 26)
        tomorrow = date(2026, 8, 27)
        seed_a = build_daily_oracle_seed(birth, today, "astrology", "loto6")
        seed_b = build_daily_oracle_seed(birth, today, "astrology", "loto6")
        seed_next = build_daily_oracle_seed(birth, tomorrow, "astrology", "loto6")
        self.assertEqual(seed_a, seed_b)
        self.assertNotEqual(seed_a, seed_next)

        profile = calculate_divination_profile("astrology", birth, today)
        rows_a = generate_product_rows("loto6", 3, profile, seed=seed_a)
        rows_b = generate_product_rows("loto6", 3, profile, seed=seed_b)
        self.assertEqual([row["numbers"] for row in rows_a], [row["numbers"] for row in rows_b])

    def test_daily_seed_changes_by_divination_and_product(self) -> None:
        birth = date(1975, 8, 16)
        today = date(2026, 8, 26)
        seeds = {
            build_daily_oracle_seed(birth, today, "astrology", "loto6"),
            build_daily_oracle_seed(birth, today, "kabbalah", "loto6"),
            build_daily_oracle_seed(birth, today, "astrology", "loto7"),
        }
        self.assertEqual(len(seeds), 3)

    def test_loto_shapes(self) -> None:
        expected = {"miniloto": (5, 31), "loto6": (6, 43), "loto7": (7, 37)}
        profile = calculate_divination_profile("kabbalah", date(1975, 8, 16), date(2026, 8, 26))
        for product_id, (length, maximum) in expected.items():
            rows = generate_product_rows(product_id, 3, profile, seed=f"seed-{product_id}")
            for row in rows:
                self.assertEqual(len(row["numbers"]), length)
                self.assertEqual(len(set(row["numbers"])), length)
                self.assertTrue(all(1 <= number <= maximum for number in row["numbers"]))

    def test_numbers_shapes(self) -> None:
        profile = calculate_divination_profile("tarot", date(1975, 8, 16), date(2026, 8, 26))
        for product_id, digit_count in {"numbers3": 3, "numbers4": 4}.items():
            rows = generate_product_rows(product_id, 3, profile, seed=f"seed-{product_id}")
            for row in rows:
                self.assertEqual(len(row["numbers"]), digit_count)
                self.assertTrue(all(0 <= digit <= 9 for digit in row["numbers"]))
                self.assertEqual(row["display_box_number"], "-".join(str(n) for n in sorted(row["numbers"])))

    def test_result_renders_for_each_divination(self) -> None:
        for method_id, label in [("astrology", "西洋占星術"), ("kabbalah", "カバラ数秘術"), ("tarot", "タロット")]:
            with self.subTest(method_id=method_id):
                response = self.generate("loto6", count="2", divination=method_id)
                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertIn(label, html)
                self.assertIn('data-reveal-product="loto6"', html)

    def test_divination_preview(self) -> None:
        for method_id in ["astrology", "kabbalah", "tarot"]:
            _, csrf = self.get_index()
            response = self.client.post("/divination-preview", data={"csrf_token": csrf, "divination": method_id, "birth_date": "1975-08-16"})
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data["method_id"], method_id)
            self.assertEqual(len(data["summary_items"]), 3)

    def test_invalid_divination_is_rejected(self) -> None:
        response = self.generate("loto6", count="1", divination="unknown")
        self.assertEqual(response.status_code, 400)
        self.assertIn("タロットから占いを選んでください", response.get_data(as_text=True))

    def test_invalid_inputs_are_rejected(self) -> None:
        invalid_count = self.generate("loto6", count="11")
        self.assertEqual(invalid_count.status_code, 400)
        self.assertIn("1〜10", invalid_count.get_data(as_text=True))

        html, csrf = self.get_index()
        missing_birth = self.client.post(
            "/generate",
            data={"csrf_token": csrf, "divination": "astrology", "product": "loto6", "count": "1", "birth_date": ""},
        )
        self.assertEqual(missing_birth.status_code, 400)
        self.assertIn("生年月日", missing_birth.get_data(as_text=True))



if __name__ == "__main__":
    unittest.main(verbosity=2)
