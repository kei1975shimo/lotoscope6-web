from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")

from app import app, rows_from_token  # noqa: E402


class LotoscopeSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
        self.client = app.test_client()

    @staticmethod
    def csrf(html: str) -> str:
        match = re.search(r'name="csrf_token" value="([^"]+)"', html)
        assert match
        return match.group(1)

    @staticmethod
    def ticket_token(html: str) -> str:
        match = re.search(r'name="ticket_token" value="([^"]+)"', html)
        assert match
        return match.group(1)

    def get_index(self) -> tuple[str, str]:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        return html, self.csrf(html)

    def generate(self, **overrides: str):
        html, csrf = self.get_index()
        data = {
            "csrf_token": csrf,
            "mode": "all",
            "count": "2",
            "favorite_1": "7",
            "favorite_2": "24",
            "avoid_1": "13",
            "seed": "smoke-test",
        }
        data.update(overrides)
        return self.client.post("/generate", data=data)

    def test_index_and_security_headers(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Content-Security-Policy", response.headers)
        self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(response.headers.get("Cache-Control"), "no-store")
        html = response.get_data(as_text=True)
        self.assertIn("合計予定口数", html)
        self.assertIn("総合スコア", html)

    def test_all_mode_generates_requested_total_without_duplicates(self) -> None:
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("生成数: 10口", html)
        rows = rows_from_token(self.ticket_token(html))
        self.assertEqual(len(rows), 10)
        combinations = {tuple(int(row[f"n{i}"]) for i in range(1, 7)) for row in rows}
        self.assertEqual(len(combinations), 10)

    def test_seed_reproduces_number_combinations(self) -> None:
        first = self.generate(seed="same-seed")
        first_rows = rows_from_token(self.ticket_token(first.get_data(as_text=True)))
        second = self.generate(seed="same-seed")
        second_rows = rows_from_token(self.ticket_token(second.get_data(as_text=True)))
        first_keys = [(row["mode_id"], tuple(row[f"n{i}"] for i in range(1, 7))) for row in first_rows]
        second_keys = [(row["mode_id"], tuple(row[f"n{i}"] for i in range(1, 7))) for row in second_rows]
        self.assertEqual(first_keys, second_keys)

    def test_generate_input_validation(self) -> None:
        duplicate = self.generate(favorite_1="7", favorite_2="7")
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("重複", duplicate.get_data(as_text=True))

        overlap = self.generate(favorite_1="7", favorite_2="", avoid_1="7")
        self.assertEqual(overlap.status_code, 400)
        self.assertIn("両方", overlap.get_data(as_text=True))

        invalid_count = self.generate(count="11")
        self.assertEqual(invalid_count.status_code, 400)
        self.assertIn("1〜10", invalid_count.get_data(as_text=True))

    def test_manual_check_and_recheck_flow(self) -> None:
        generated = self.generate(mode="balance", count="2")
        generated_html = generated.get_data(as_text=True)
        token = self.ticket_token(generated_html)
        check_response = self.client.post(
            "/check",
            data={"csrf_token": self.csrf(generated_html), "ticket_token": token},
        )
        self.assertEqual(check_response.status_code, 200)
        check_html = check_response.get_data(as_text=True)

        result = self.client.post(
            "/check-result",
            data={
                "csrf_token": self.csrf(check_html),
                "ticket_token": token,
                "check_method": "manual",
                "main_1": "1",
                "main_2": "2",
                "main_3": "3",
                "main_4": "4",
                "main_5": "5",
                "main_6": "6",
                "bonus": "7",
            },
        )
        self.assertEqual(result.status_code, 200)
        result_html = result.get_data(as_text=True)
        self.assertIn("全照合結果", result_html)
        self.assertIn("照合条件を変更", result_html)
        self.assertIn('name="check_method" value="manual"', result_html)

    def test_manual_draw_rejects_duplicate_and_bonus_overlap(self) -> None:
        generated = self.generate(mode="balance", count="1")
        generated_html = generated.get_data(as_text=True)
        token = self.ticket_token(generated_html)
        check_response = self.client.post(
            "/check",
            data={"csrf_token": self.csrf(generated_html), "ticket_token": token},
        )
        check_html = check_response.get_data(as_text=True)
        csrf = self.csrf(check_html)

        duplicate = self.client.post(
            "/check-result",
            data={
                "csrf_token": csrf,
                "ticket_token": token,
                "check_method": "manual",
                "main_1": "1",
                "main_2": "1",
                "main_3": "3",
                "main_4": "4",
                "main_5": "5",
                "main_6": "6",
                "bonus": "7",
            },
        )
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("重複", duplicate.get_data(as_text=True))

        # Refresh the form to obtain a fresh CSRF token in case the session changed.
        check_response = self.client.post(
            "/check",
            data={"csrf_token": self.csrf(duplicate.get_data(as_text=True)), "ticket_token": token},
        )
        check_html = check_response.get_data(as_text=True)
        overlap = self.client.post(
            "/check-result",
            data={
                "csrf_token": self.csrf(check_html),
                "ticket_token": token,
                "check_method": "manual",
                "main_1": "1",
                "main_2": "2",
                "main_3": "3",
                "main_4": "4",
                "main_5": "5",
                "main_6": "6",
                "bonus": "6",
            },
        )
        self.assertEqual(overlap.status_code, 400)
        self.assertIn("異なる数字", overlap.get_data(as_text=True))

    def test_draw_number_check(self) -> None:
        generated = self.generate(mode="balance", count="1")
        generated_html = generated.get_data(as_text=True)
        token = self.ticket_token(generated_html)
        check_response = self.client.post(
            "/check",
            data={"csrf_token": self.csrf(generated_html), "ticket_token": token},
        )
        check_html = check_response.get_data(as_text=True)
        result = self.client.post(
            "/check-result",
            data={
                "csrf_token": self.csrf(check_html),
                "ticket_token": token,
                "check_method": "draw",
                "draw_no": "2100",
            },
        )
        self.assertEqual(result.status_code, 200)
        self.assertIn("第2100回", result.get_data(as_text=True))

    def test_public_templates_do_not_contain_deprecated_copy(self) -> None:
        root = Path(__file__).resolve().parents[1]
        public_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [root / "app.py", *(root / "templates").glob("*.html")]
        )
        deprecated = [
            "iPhoneライクUI",
            "iPhone UI",
            "高配当意識型",
            "未出現数字重視型",
            "今回の見やすいおすすめ",
            "運命の数字を生成する",
            "買い目バランス",
        ]
        for phrase in deprecated:
            self.assertNotIn(phrase, public_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
