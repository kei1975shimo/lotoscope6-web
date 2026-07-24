from __future__ import annotations

import os
import re
import unittest
from unittest.mock import patch
from datetime import date
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")

from app import app, load_generation_mode_rules, rows_from_token  # noqa: E402
from astrology_numbers import calculate_astrology_profile  # noqa: E402


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
        self.assertIn("数字の受け取り方", html)
        self.assertIn("birth_year", html)
        self.assertIn("星図に刻まれた誕生日", html)
        self.assertIn("CELESTIAL DIVINATION", html)

    def test_all_mode_generates_requested_total_without_duplicates(self) -> None:
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("生成数: 8口", html)
        rows = rows_from_token(self.ticket_token(html))
        self.assertEqual(len(rows), 8)
        combinations = {tuple(int(row[f"n{i}"]) for i in range(1, 7)) for row in rows}
        self.assertEqual(len(combinations), 8)

    def test_seed_reproduces_number_combinations(self) -> None:
        first = self.generate(seed="same-seed")
        first_rows = rows_from_token(self.ticket_token(first.get_data(as_text=True)))
        second = self.generate(seed="same-seed")
        second_rows = rows_from_token(self.ticket_token(second.get_data(as_text=True)))
        first_keys = [(row["mode_id"], tuple(row[f"n{i}"] for i in range(1, 7))) for row in first_rows]
        second_keys = [(row["mode_id"], tuple(row[f"n{i}"] for i in range(1, 7))) for row in second_rows]
        self.assertEqual(first_keys, second_keys)

    def test_generate_input_validation(self) -> None:
        invalid_count = self.generate(count="11")
        self.assertEqual(invalid_count.status_code, 400)
        self.assertIn("1〜10", invalid_count.get_data(as_text=True))

    def test_removed_number_fields_and_mode_are_not_displayed(self) -> None:
        html, _csrf = self.get_index()
        self.assertNotIn("好きな数字", html)
        self.assertNotIn("避けたい数字", html)
        self.assertNotIn('value="personal"', html)

    def test_astrology_is_enabled_by_default_in_the_ui(self) -> None:
        html, _csrf = self.get_index()
        self.assertRegex(html, r'id="use_astrology"[^>]*checked')
        self.assertIn("星からの導きを受け取る", html)
        self.assertIn("数字へ続く導き", html)

    def test_astrology_rule_is_repaired_when_deployed_config_is_stale(self) -> None:
        stale_rules = {
            "balance": {
                "mode_id": "balance",
                "mode_name_ja": "調和のバランス型",
            }
        }
        with patch("app.load_json", return_value=stale_rules):
            rules = load_generation_mode_rules()

        self.assertIn("astrology", rules)
        self.assertEqual(rules["astrology"]["mode_id"], "astrology")
        self.assertGreaterEqual(int(rules["astrology"]["astrology_core_min"]), 1)

    def test_astrology_opt_out_is_preserved_on_edit_url(self) -> None:
        response = self.generate(mode="all", count="1", astrology_setting_present="1", use_astrology="0")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("生成数: 4口", html)
        edit_match = re.search(r'<a class="ghost-button" href="([^"]+)">星読みをやり直す</a>', html)
        self.assertIsNotNone(edit_match)
        edit_response = self.client.get(edit_match.group(1).replace("&amp;", "&"))
        edit_html = edit_response.get_data(as_text=True)
        self.assertNotRegex(edit_html, r'id="use_astrology"[^>]*checked')

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
        self.assertIn("すべての答え合わせ", result_html)
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

    def test_astrology_profile_is_deterministic_and_in_range(self) -> None:
        profile = calculate_astrology_profile(date(1975, 8, 16), target_date=date(2026, 7, 22))
        repeated = calculate_astrology_profile(date(1975, 8, 16), target_date=date(2026, 7, 22))
        self.assertEqual(profile["core_numbers"], repeated["core_numbers"])
        self.assertEqual(len(profile["core_numbers"]), 6)
        self.assertEqual(len(set(profile["core_numbers"])), 6)
        self.assertTrue(all(1 <= number <= 43 for number in profile["core_numbers"]))
        self.assertEqual(len(profile["planet_rows"]), 7)
        self.assertEqual(profile["sun_sign"], "獅子座")

    def test_astrology_mode_generates_and_displays_profile(self) -> None:
        response = self.generate(
            mode="astrology",
            count="2",
            use_astrology="1",
            birth_date="1975-08-16",
            seed="astrology-smoke",
        )
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("今日、あなたの星に響いた数字", html)
        self.assertIn("太陽星座", html)
        rows = rows_from_token(self.ticket_token(html))
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["mode_id"] == "astrology" for row in rows))
        self.assertTrue(all(row["astrology_numbers"] for row in rows))
        self.assertTrue(all("birth_date" not in row for row in rows))

    def test_all_mode_adds_astrology_only_when_enabled(self) -> None:
        response = self.generate(
            mode="all",
            count="2",
            use_astrology="1",
            birth_date="1975-08-16",
            seed="all-with-astrology",
        )
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("生成数: 10口", html)
        rows = rows_from_token(self.ticket_token(html))
        self.assertEqual(len(rows), 10)
        self.assertIn("astrology", {row["mode_id"] for row in rows})

    def test_astrology_rejects_missing_or_future_birth_date(self) -> None:
        missing = self.generate(mode="astrology", count="1", birth_date="")
        self.assertEqual(missing.status_code, 400)
        self.assertIn("生年月日", missing.get_data(as_text=True))

        future = self.generate(mode="astrology", count="1", birth_date="2999-01-01")
        self.assertEqual(future.status_code, 400)
        self.assertIn("未来", future.get_data(as_text=True))

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


    def test_zodiac_preview_returns_sun_sign(self):
        response = self.client.get("/zodiac-preview?birth_date=1975-08-16")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["name"], "獅子座")
        self.assertEqual(payload["symbol"], "♌")
        self.assertEqual(payload["english"], "LEO")

    def test_zodiac_preview_rejects_invalid_date(self):
        response = self.client.get("/zodiac-preview?birth_date=2026-02-31")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

if __name__ == "__main__":
    unittest.main(verbosity=2)
