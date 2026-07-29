from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")

from app import app  # noqa: E402
from astrology_numbers import calculate_astrology_profile
from product_numbers import generate_product_rows  # noqa: E402


class LotoNumbersScopeSmokeTests(unittest.TestCase):
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

    def generate(self, product: str = "loto6", count: str = "2", seed: str = "smoke-test"):
        html, csrf = self.get_index()
        return self.client.post(
            "/generate",
            data={
                "csrf_token": csrf,
                "product": product,
                "count": count,
                "seed": seed,
                "birth_date": "1975-08-16",
            },
        )

    def test_index_lists_all_five_products_and_removes_old_modes(self) -> None:
        html, _ = self.get_index()
        for product in ["ミニロト", "ロト6", "ロト7", "ナンバーズ3", "ナンバーズ4"]:
            self.assertIn(product, html)
        for removed in ["バランス", "過去データ", "眠っている数字", "高い数字を含める", "五つの導きをすべて試す"]:
            self.assertNotIn(removed, html)
        self.assertRegex(html, r'name="product" value="loto6"[^>]*checked')
        self.assertIn("ロトナンバーズ・スコープ", html)
        for ritual in ["月輪の五光", "六星印の儀", "七惑星の大軌道", "三連星盤", "四星門の啓示"]:
            self.assertIn(ritual, html)
        self.assertNotIn("答え合わせ", html)
        self.assertLess(html.index('id="product-panel"'), html.index('id="birth-panel"'))
        self.assertIn("まず、数字を尋ねるくじを選んでください", html)
        self.assertIn("次に、あなたの誕生日を教えてください", html)
        self.assertNotIn("data-oracle-digit", html)

    def test_all_products_generate_correct_shapes(self) -> None:
        expected = {
            "miniloto": (5, 31, "loto"),
            "loto6": (6, 43, "loto"),
            "loto7": (7, 37, "loto"),
            "numbers3": (3, 9, "numbers"),
            "numbers4": (4, 9, "numbers"),
        }
        profile = calculate_astrology_profile(__import__('datetime').date(1975, 8, 16))
        for product_id, (length, maximum, kind) in expected.items():
            with self.subTest(product_id=product_id):
                rows = generate_product_rows(product_id, 3, profile, seed=f"seed-{product_id}")
                self.assertEqual(len(rows), 3)
                for row in rows:
                    self.assertEqual(len(row["numbers"]), length)
                    if kind == "loto":
                        self.assertEqual(len(set(row["numbers"])), length)
                        self.assertTrue(all(1 <= number <= maximum for number in row["numbers"]))
                    else:
                        self.assertEqual(len(row["display_number"]), length)
                        self.assertTrue(row["display_number"].isdigit())

    def test_result_has_no_answer_check(self) -> None:
        response = self.generate("loto7", count="2")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("今回、星が導いた七つの数字", html)
        self.assertIn("この数字へつながった星読み", html)
        self.assertIn("七惑星の大軌道", html)
        self.assertIn('data-reveal-product="loto7"', html)
        self.assertNotIn("答え合わせ", html)
        self.assertNotIn('action="/check"', html)

    def test_answer_check_routes_are_not_published(self) -> None:
        self.assertEqual(self.client.get("/check").status_code, 404)
        self.assertEqual(self.client.post("/check", data={}).status_code, 404)
        self.assertEqual(self.client.post("/check-result", data={}).status_code, 404)

    def test_invalid_inputs_are_rejected(self) -> None:
        invalid_count = self.generate("loto6", count="11")
        self.assertEqual(invalid_count.status_code, 400)
        self.assertIn("1〜10", invalid_count.get_data(as_text=True))

        html, csrf = self.get_index()
        missing_birth = self.client.post(
            "/generate",
            data={"csrf_token": csrf, "product": "loto6", "count": "1", "seed": "", "birth_date": ""},
        )
        self.assertEqual(missing_birth.status_code, 400)
        self.assertIn("生年月日", missing_birth.get_data(as_text=True))

    def test_zodiac_preview(self) -> None:
        response = self.client.get("/zodiac-preview?birth_date=1975-08-16")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["name"], "獅子座")

    def test_public_code_contains_no_answer_check_copy(self) -> None:
        root = Path(__file__).resolve().parents[1]
        public_files = [root / "app.py", *(root / "templates").glob("*.html"), root / "static/js/app.js"]
        public_text = "\n".join(path.read_text(encoding="utf-8") for path in public_files)
        self.assertNotIn("答え合わせ", public_text)
        self.assertNotIn('@app.post("/check")', public_text)
        self.assertNotIn('@app.post("/check-result")', public_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
