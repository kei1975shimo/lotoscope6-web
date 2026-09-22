"""Regressions for daily prefixes, unbiased resampling and request boundaries."""
from __future__ import annotations

import os
import re
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

from app import APP_VERSION, JST, RateLimiter, build_daily_oracle_seed, create_app, resolve_secret_key
from divination_numbers import calculate_divination_profile, divination_choices
from product_numbers import _resample_weights, build_digit_weights, build_loto_weights, generate_product_rows, get_product, product_choices, product_full_size

BIRTH = date(1975, 8, 16)
DAY = date(2026, 9, 13)
METHODS = [x['divination_id'] for x in divination_choices()]
PRODUCTS = [x['product_id'] for x in product_choices()]


class GenerationRegressionTests(unittest.TestCase):
    def test_every_count_is_a_ranked_prefix_for_all_methods_and_products(self):
        for method in METHODS:
            profile = calculate_divination_profile(method, BIRTH, DAY)
            for product in PRODUCTS:
                seed = build_daily_oracle_seed(BIRTH, DAY, method, product)
                full = generate_product_rows(product, 10, profile, seed)
                with self.subTest(method=method, product=product):
                    self.assertEqual(len({tuple(r['numbers']) for r in full}), 10)
                    self.assertEqual([r['ticket_score'] for r in full], sorted((r['ticket_score'] for r in full), reverse=True))
                    for count in range(1, 11):
                        self.assertEqual(generate_product_rows(product, count, profile, seed), full[:count])

    def test_score_ties_keep_generation_order(self):
        rows = [{'ticket_score': 50, 'numbers': [n]} for n in range(10)]
        with patch('product_numbers._generate_loto_rows', return_value=rows):
            self.assertEqual(generate_product_rows('loto6', 3, {}, 'seed'), rows[:3])

    def test_flat_profile_has_no_range_or_digit_bias(self):
        profile = {'weights': {n: 100 for n in range(1, 44)}}
        for maximum in (31, 37, 43):
            self.assertEqual(set(build_loto_weights(profile, maximum).values()), {121.0})
        self.assertEqual(set(build_digit_weights(profile).values()), {121.0})

    def test_resampling_preserves_mean_and_reflection(self):
        source = [float(n * n + 4) for n in range(43)]
        for size in (10, 31, 37, 43):
            projected = _resample_weights(source, size)
            self.assertAlmostEqual(sum(projected) / size, sum(source) / 43)
            self.assertEqual(projected, list(reversed(_resample_weights(list(reversed(source)), size))))

    def test_source_high_peak_stays_at_high_end_without_wrap(self):
        peak = [0.0] * 42 + [100.0]
        for size in (10, 31, 37):
            values = _resample_weights(peak, size)
            self.assertEqual(values.index(max(values)), size - 1)
            self.assertEqual(values[0], 0.0)
            self.assertGreater(values[-1], 0.0)

    def test_source_string_keys_and_invalid_weights(self):
        a = build_loto_weights({'weights': {1: 5, 43: 7}}, 31)
        b = build_loto_weights({'weights': {'1': 5, '43': 7, '20': float('nan'), '21': 'invalid'}}, 31)
        self.assertEqual(a, b)
        self.assertEqual(build_digit_weights({'weights': None}), {n: 1 for n in range(10)})

    def test_invalid_counts_fail_at_generator_boundary(self):
        for value in (0, 11, -1, True, 1.5, '1'):
            with self.subTest(count=value), self.assertRaises(ValueError):
                generate_product_rows('loto6', value, {}, 'test')

    def test_leap_day_oldest_date_and_high_counts(self):
        for birth in (date(1900, 1, 1), date(2000, 2, 29), DAY):
            for method in METHODS:
                profile = calculate_divination_profile(method, birth, DAY)
                for product in product_choices():
                    rows = generate_product_rows(product['product_id'], 10, profile, str(birth))
                    for row in rows:
                        if product['kind'] == 'loto':
                            self.assertEqual(len(set(row['numbers'])), product['pick_count'])
                            self.assertTrue(all(1 <= n <= product['max_number'] for n in row['numbers']))
                        else:
                            self.assertEqual(len(row['numbers']), product['digit_count'])
                            self.assertTrue(all(0 <= n <= 9 for n in row['numbers']))

    def test_removed_legacy_fields_are_not_returned(self):
        old = {'ticket_id', 'generated_at', 'astrology_numbers', 'astrology_hit_count', 'astrology_fit_score', 'reference_hit_count', 'product_kind', 'product_id', 'product_name', 'display_number', 'low_count', 'mid_count', 'high_count'}
        for product in PRODUCTS:
            row = generate_product_rows(product, 1, {}, 'test')[0]
            self.assertFalse(old & row.keys())


class PickSizeRegressionTests(unittest.TestCase):
    """Partial candidates stay unique, ranked, in range and stable by count."""

    def test_omitted_pick_size_matches_explicit_full_size(self):
        for method in METHODS:
            profile = calculate_divination_profile(method, BIRTH, DAY)
            for product in PRODUCTS:
                seed = build_daily_oracle_seed(BIRTH, DAY, method, product)
                full = product_full_size(get_product(product))
                with self.subTest(method=method, product=product):
                    self.assertEqual(
                        generate_product_rows(product, 5, profile, seed),
                        generate_product_rows(product, 5, profile, seed, pick_size=full),
                    )

    def test_partial_pool_is_unique_ranked_and_count_independent(self):
        for method in METHODS:
            profile = calculate_divination_profile(method, BIRTH, DAY)
            for info in product_choices():
                product, full = info['product_id'], info['full_size']
                seed = build_daily_oracle_seed(BIRTH, DAY, method, product)
                for size in range(1, full + 1):
                    with self.subTest(method=method, product=product, size=size):
                        rows = generate_product_rows(product, 10, profile, seed, pick_size=size)
                        self.assertEqual(len({tuple(r['numbers']) for r in rows}), 10)
                        self.assertEqual([r['ticket_score'] for r in rows], sorted([r['ticket_score'] for r in rows], reverse=True))
                        for count in (1,3,5):
                            self.assertEqual(generate_product_rows(product,count,profile,seed,pick_size=size),rows[:count])
                        for row in rows:
                            self.assertEqual(len(row['numbers']),size)
                            if info['kind']=='loto':
                                self.assertEqual(len(set(row['numbers'])),size)
                                self.assertEqual(row['numbers'],sorted(row['numbers']))
                                self.assertTrue(all(1 <= n <= info['max_number'] for n in row['numbers']))
                            else:
                                self.assertTrue(all(0 <= n <= 9 for n in row['numbers']))

    def test_invalid_pick_size_fails_at_generator_boundary(self):
        for value in (0, 7, -1, True, 1.5, '1'):
            with self.subTest(pick_size=value), self.assertRaises(ValueError):
                generate_product_rows('loto6', 1, {}, 'test', pick_size=value)


class RequestRegressionTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True, 'TEST_PREMIUM_ACCESS': True, 'SECRET_KEY': 'test', 'RATE_LIMIT_PER_MINUTE': 0, 'TRUSTED_PROXY_HOPS': 0, 'SESSION_COOKIE_SECURE': False})
        self.client = self.app.test_client()
        self.token = self.csrf(self.client)

    @staticmethod
    def csrf(client):
        return re.search(r'name="csrf_token" value="([^"]+)"', client.get('/').text)[1]

    def data(self, **overrides):
        return dict(csrf_token=self.token, divination='astrology', product='loto6', count='1', birth_date=BIRTH.isoformat(), **overrides) if not overrides else {**self.data(), **overrides}

    def test_top_display_and_additional_rows_share_fixed_order(self):
        for method in METHODS:
            for product in PRODUCTS:
                tops = []
                for count in (1, 3, 10):
                    response = self.client.post('/generate', data=self.data(divination=method, product=product, count=str(count)))
                    self.assertEqual(response.status_code, 200)
                    block = response.text.split('class="best-numbers ', 1)[1].split('</div>', 1)[0]
                    tops.append(re.findall(r'aria-label="(\d+)(?:、占いの中心数字)?"', block))
                    self.assertEqual(response.text.count('<details class="ticket">'), count - 1)
                self.assertEqual(tops[0], tops[1])
                self.assertEqual(tops[0], tops[2])

    def test_pick_size_trims_numbers_and_is_preserved_on_reconfirm(self):
        response = self.client.post('/generate', data=self.data(product='loto6', count='3', pick_size='2'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text.count('<details class="ticket">'), 2)
        block = response.text.split('class="best-numbers ', 1)[1].split('</div>', 1)[0]
        numbers = re.findall(r'aria-label="(\d+)(?:、占いの中心数字)?"', block)
        self.assertEqual(len(numbers), 2)
        self.assertIn('name="pick_size" value="2"', response.text)

    def test_pick_size_out_of_range_or_non_numeric_is_rejected(self):
        headers = {'Accept': 'application/json'}
        response = self.client.post('/generate', data=self.data(product='numbers3', pick_size='4'), headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn('欲しい個数', response.json['error'])
        for value in ('0', 'abc'):
            response = self.client.post('/generate', data=self.data(pick_size=value), headers=headers)
            self.assertEqual(response.status_code, 400)
            self.assertIn('欲しい個数', response.json['error'])

    def test_native_selects_work_without_javascript(self):
        data = self.data(birth_year='2000', birth_month='2', birth_day='29')
        data.pop('birth_date')
        self.assertEqual(self.client.post('/generate', data=data).status_code, 200)
        data['birth_year'] = '2001'
        response = self.client.post('/generate', data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('年・月・日', response.text)

    def test_preview_uses_post_csrf_and_no_store(self):
        response = self.client.post('/divination-preview', data=self.data())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertNotIn('birth_date', response.json)
        self.assertEqual(self.client.get('/divination-preview').status_code, 405)
        self.assertEqual(self.client.get('/zodiac-preview').status_code, 404)
        self.assertEqual(self.client.post('/divination-preview', data={'birth_date': BIRTH.isoformat()}).status_code, 400)

    def test_json_contract_success_and_errors(self):
        headers = {'Accept': 'application/json'}
        response = self.client.post('/generate', data=self.data(), headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="best-pick"', response.json['html'])
        response = self.client.post('/generate', data=self.data(count='11'), headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn('1〜10', response.json['error'])

    def test_csrf_missing_forged_and_non_ascii_return_400(self):
        for token in ('', 'forged', '日本語'):
            response = self.client.post('/generate', data=self.data(csrf_token=token), headers={'Accept': 'application/json'})
            self.assertEqual(response.status_code, 400)
            self.assertIn('有効期限', response.json['error'])

    def test_security_headers_and_no_inline_css_or_script(self):
        response = self.client.post('/generate', data=self.data())
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertIn("style-src 'self';", response.headers['Content-Security-Policy'])
        self.assertNotIn('unsafe-inline', response.headers['Content-Security-Policy'])
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')
        self.assertEqual(response.headers['Referrer-Policy'], 'no-referrer')
        self.assertNotRegex(response.text, r'\sstyle=|<style[ >]|\son(?:click|submit|load)=')
        self.assertNotIn('https://', response.text)
        with self.client.session_transaction() as state:
            self.assertEqual(set(state.keys()), {'csrf_token'})

    def test_missing_secrets_fail_in_production(self):
        with patch.dict(os.environ, {'APP_ENV': 'production', 'SECRET_KEY': ''}):
            with self.assertRaises(RuntimeError):
                resolve_secret_key()

    def test_secure_cookie_in_production(self):
        with patch.dict(os.environ, {'APP_ENV': 'production', 'SECRET_KEY': 'test-production-key'}):
            response = create_app().test_client().get('/')
            cookie = response.headers['Set-Cookie']
            for attribute in ('Secure', 'HttpOnly', 'SameSite=Lax'):
                self.assertIn(attribute, cookie)

    def test_size_limit_json_error(self):
        response = self.client.post('/generate', data={'padding': 'x' * (257 * 1024)}, headers={'Accept': 'application/json'})
        self.assertEqual(response.status_code, 413)
        self.assertTrue(response.json['error'])

    def test_jst_date_is_consistent_through_request(self):
        fixed = datetime(2026, 9, 14, 0, 0, 1, tzinfo=JST)
        with patch('app.datetime') as clock:
            clock.now.return_value = fixed
            response = self.client.post('/generate', data=self.data())
        self.assertIn('2026年9月14日の導き', response.text)
        self.assertIn('datetime="2026-09-14"', response.text)

    def test_server_failure_returns_safe_json(self):
        with patch('app.generate_product_rows', side_effect=Exception('private internal detail')):
            with self.assertLogs(self.app.logger, level='ERROR'):
                response = self.client.post('/generate', data=self.data(), headers={'Accept': 'application/json'})
        self.assertEqual(response.status_code, 500)
        self.assertNotIn('private internal detail', response.text)

    def test_all_images_have_dimensions_and_exist(self):
        images = []
        class Parser(HTMLParser):
            def handle_starttag(self, tag, attrs):
                if tag == 'img':
                    images.append(dict(attrs))
        Parser().feed(self.client.get('/').text)
        root = Path(__file__).resolve().parents[1]
        for image in images:
            self.assertIn('width', image)
            self.assertIn('height', image)
            self.assertIn('alt', image)
            self.assertTrue((root / image['src'].lstrip('/')).is_file())


class RateLimitRegressionTests(unittest.TestCase):
    def check_spoofing(self, hops):
        app = create_app({'TESTING': True, 'TEST_PREMIUM_ACCESS': True, 'SECRET_KEY': 'rate-test', 'SESSION_COOKIE_SECURE': False, 'RATE_LIMIT_PER_MINUTE': 4, 'TRUSTED_PROXY_HOPS': hops})
        client = app.test_client()
        token = RequestRegressionTests.csrf(client)
        codes = []
        for i in range(12):
            forwarded = f'203.0.113.{i}' + (', 198.51.100.9' if hops else '')
            response = client.post('/generate', data={'csrf_token': token, 'birth_date': '1975-08-16', 'count': '1'}, headers={'X-Forwarded-For': forwarded, 'Accept': 'application/json'})
            codes.append(response.status_code)
            if response.status_code == 429:
                self.assertTrue(1 <= int(response.headers['Retry-After']) <= 60)
        self.assertEqual(codes, [200] * 4 + [429] * 8)
        return app, client, token

    def test_direct_connection_ignores_all_forwarded_headers(self):
        self.check_spoofing(0)

    def test_single_trusted_proxy_ignores_forged_leading_values(self):
        app, client, token = self.check_spoofing(1)
        self.assertIn('198.51.100.9', app.extensions['rate_limiter'].buckets)
        response = client.post('/generate', data={'csrf_token': token, 'birth_date': '1975-08-16', 'count': '1'}, headers={'X-Forwarded-For': '203.0.113.1, 198.51.100.10'})
        self.assertEqual(response.status_code, 200)

    def test_preview_and_generate_share_rate_budget(self):
        app = create_app({'TESTING': True, 'TEST_PREMIUM_ACCESS': True, 'SECRET_KEY': 'rate-test', 'SESSION_COOKIE_SECURE': False, 'RATE_LIMIT_PER_MINUTE': 1, 'TRUSTED_PROXY_HOPS': 0})
        client = app.test_client()
        data = {'csrf_token': RequestRegressionTests.csrf(client), 'birth_date': '1975-08-16', 'count': '1'}
        self.assertEqual(client.post('/divination-preview', data=data).status_code, 200)
        self.assertEqual(client.post('/generate', data=data).status_code, 429)

    def test_threads_cannot_race_past_limit(self):
        limiter = RateLimiter()
        with ThreadPoolExecutor(max_workers=16) as pool:
            replies = list(pool.map(lambda _: limiter.check('test', 4), range(100)))
        self.assertEqual(replies.count(0), 4)

    def test_window_expiry_and_app_isolation(self):
        limiter = RateLimiter()
        with patch('app.time.monotonic', return_value=100.0):
            self.assertEqual(limiter.check('test', 1), 0)
            self.assertEqual(limiter.check('test', 1), 60)
        with patch('app.time.monotonic', return_value=160.0):
            self.assertEqual(limiter.check('test', 1), 0)
        self.assertEqual(RateLimiter().check('test', 1), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
