from __future__ import annotations

import os
import re
import unittest

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")

from app import app  # noqa: E402
from astrology_numbers import calculate_astrology_profile  # noqa: E402
from product_numbers import generate_product_rows, product_choices  # noqa: E402


class LotoScopeSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
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

    def generate(self, product: str = "loto6", count: str = "2", sub_count: str = "1"):
        html, csrf = self.get_index()
        return self.client.post(
            "/generate",
            data={
                "csrf_token": csrf,
                "product": product,
                "count": count,
                "sub_count": sub_count,
                "birth_date": "1975-08-16",
            },
        )

    def test_index_lists_all_products(self) -> None:
        html, _ = self.get_index()
        for product in ["ミニロト", "ロト6", "ロト7", "ナンバーズ3", "ナンバーズ4"]:
            self.assertIn(product, html)
        for removed in ["星の儀式の流れ", "guide-panel", "FINAL CONFIRMATION"]:
            self.assertNotIn(removed, html)
        self.assertIn("ロト・スコープ", html)
        self.assertIn("compact-home-hero", html)
        self.assertRegex(html, r'name="product" value="loto6"[^>]*checked')

    def test_product_choices_include_loto_and_numbers(self) -> None:
        self.assertEqual(
            [item["product_id"] for item in product_choices()],
            ["miniloto", "loto6", "loto7", "numbers3", "numbers4"],
        )

    def test_all_loto_products_generate_correct_shapes(self) -> None:
        expected = {
            "miniloto": (5, 31),
            "loto6": (6, 43),
            "loto7": (7, 37),
        }
        profile = calculate_astrology_profile(__import__("datetime").date(1975, 8, 16))
        for product_id, (length, maximum) in expected.items():
            with self.subTest(product_id=product_id):
                rows = generate_product_rows(product_id, 3, profile, seed=f"seed-{product_id}")
                self.assertEqual(len(rows), 3)
                for row in rows:
                    self.assertEqual(len(row["numbers"]), length)
                    self.assertEqual(len(set(row["numbers"])), length)
                    self.assertTrue(all(1 <= number <= maximum for number in row["numbers"]))
                    self.assertEqual(row["product_kind"], "loto")

    def test_all_numbers_products_generate_correct_shapes(self) -> None:
        expected = {
            "numbers3": 3,
            "numbers4": 4,
        }
        profile = calculate_astrology_profile(__import__("datetime").date(1975, 8, 16))
        for product_id, digit_count in expected.items():
            with self.subTest(product_id=product_id):
                rows = generate_product_rows(product_id, 3, profile, seed=f"seed-{product_id}")
                self.assertEqual(len(rows), 3)
                for row in rows:
                    self.assertEqual(len(row["numbers"]), digit_count)
                    self.assertTrue(all(0 <= digit <= 9 for digit in row["numbers"]))
                    self.assertEqual(row["product_kind"], "numbers")
                    self.assertEqual(row["box_numbers"], sorted(row["numbers"]))
                    self.assertEqual(row["display_number"], "-".join(str(d) for d in row["numbers"]))
                    self.assertEqual(row["display_box_number"], "-".join(str(d) for d in row["box_numbers"]))

    def test_numbers_seed_is_reproducible(self) -> None:
        profile = calculate_astrology_profile(__import__("datetime").date(1990, 3, 3))
        first = generate_product_rows("numbers4", 2, profile, seed="repeat-me")
        second = generate_product_rows("numbers4", 2, profile, seed="repeat-me")
        self.assertEqual([row["numbers"] for row in first], [row["numbers"] for row in second])

    def test_result_renders_for_loto(self) -> None:
        response = self.generate("loto7", count="2")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("今回、星が導いた七つの数字", html)
        self.assertIn("七惑星の大軌道", html)
        self.assertIn('data-reveal-product="loto7"', html)

    def test_result_renders_for_numbers(self) -> None:
        response = self.generate("numbers4", count="2")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("今回、星が導いた四つの数字", html)
        self.assertIn("四星印の共鳴", html)
        self.assertIn('data-reveal-product="numbers4"', html)
        self.assertIn("ボックス目安", html)
        self.assertIn("digit-tile", html)

    def test_invalid_inputs_are_rejected(self) -> None:
        invalid_count = self.generate("loto6", count="11")
        self.assertEqual(invalid_count.status_code, 400)
        self.assertIn("1〜10", invalid_count.get_data(as_text=True))

        html, csrf = self.get_index()
        missing_birth = self.client.post(
            "/generate",
            data={"csrf_token": csrf, "product": "loto6", "count": "1", "birth_date": ""},
        )
        self.assertEqual(missing_birth.status_code, 400)
        self.assertIn("生年月日", missing_birth.get_data(as_text=True))

    def test_unknown_product_is_rejected(self) -> None:
        response = self.generate("numbers5", count="1")
        self.assertEqual(response.status_code, 400)
        self.assertIn("ナンバーズ4から選択してください", response.get_data(as_text=True))

    def test_zodiac_preview(self) -> None:
        response = self.client.get("/zodiac-preview?birth_date=1975-08-16")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["name"], "獅子座")

    def test_sub_numbers_generated_for_loto(self) -> None:
        profile = calculate_astrology_profile(__import__("datetime").date(1988, 5, 20))
        rows = generate_product_rows("loto6", 2, profile, seed="sub-test-loto", sub_count=3)
        for row in rows:
            self.assertEqual(len(row["sub_numbers"]), 3)
            self.assertTrue(set(row["sub_numbers"]).isdisjoint(set(row["numbers"])))
            self.assertTrue(all(1 <= number <= 43 for number in row["sub_numbers"]))

    def test_sub_numbers_generated_for_numbers(self) -> None:
        profile = calculate_astrology_profile(__import__("datetime").date(1988, 5, 20))
        rows = generate_product_rows("numbers3", 2, profile, seed="sub-test-numbers", sub_count=2)
        for row in rows:
            self.assertEqual(len(row["sub_numbers"]), 2)
            self.assertTrue(set(row["sub_numbers"]).isdisjoint(set(row["numbers"])))
            self.assertTrue(all(0 <= digit <= 9 for digit in row["sub_numbers"]))

    def test_sub_count_range_is_validated(self) -> None:
        response = self.generate("loto6", count="1", sub_count="4")
        self.assertEqual(response.status_code, 400)
        self.assertIn("1〜3", response.get_data(as_text=True))

    def test_result_page_shows_sub_numbers(self) -> None:
        response = self.generate("loto6", count="2", sub_count="2")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("サブ数字", html)
        self.assertIn("sub-numbers", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
