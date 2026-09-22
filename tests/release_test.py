import re
import unittest
from datetime import date
from unittest.mock import patch
from app import create_app
from product_numbers import generate_product_rows


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True, 'PREMIUM_PREVIEW_ENABLED': False, 'SECRET_KEY': 'test', 'RATE_LIMIT_PER_MINUTE': 0, 'SESSION_COOKIE_SECURE': False})
        self.client = self.app.test_client()
        self.token = re.search(r'name="csrf_token" value="([^"]+)"', self.client.get('/').text)[1]

    def data(self, **kw):
        return dict(dict(csrf_token=self.token, birth_date='2000-02-29', divination='astrology', product='loto6', count='10', pick_size='full'), **kw)

    def test_open_preview_allows_all_methods_without_test_entitlement(self):
        self.app.config.update(TESTING=False, PREMIUM_PREVIEW_ENABLED=True)
        home=self.client.get('/').text
        self.assertNotIn('class="oracle-option locked-oracle"',home)
        self.assertIn('無料開放中',home)
        for method in ('astrology','kabbalah','tarot'):
            for route in ('/generate','/divination-preview'):
                self.assertEqual(self.client.post(route,data=self.data(divination=method)).status_code,200)
        self.assertIn('自動課金もありません',self.client.get('/plans').text)

    def test_invalid_product_html_returns_400(self):
        self.assertEqual(self.client.post('/generate', data=self.data(product='invalid')).status_code, 400)

    def test_native_default_full_size_all_products(self):
        for product, size in [('miniloto',5),('loto6',6),('loto7',7),('numbers3',3),('numbers4',4)]:
            response=self.client.post('/generate',data=self.data(product=product))
            self.assertEqual(response.status_code,200)
            self.assertIn(f'data-number-count="{size}"',response.text)
        home=self.client.get('/').text
        self.assertIn('value="full" selected',home)
        self.assertNotIn('value="7" disabled',home)

    def test_free_cannot_bypass_paid_method_gate(self):
        for method in ('kabbalah','tarot'):
            for route in ('/generate','/divination-preview'):
                response=self.client.post(route,data=self.data(divination=method,premium='true'),headers={'Accept':'application/json','X-Premium':'true'})
                self.assertEqual(response.status_code,403)
        with self.client.session_transaction() as s:
            s['premium']=True
        self.assertEqual(self.client.post('/generate',data=self.data(divination='tarot')).status_code,403)

    def test_premium_fixture_never_unlocks_production(self):
        self.app.config.update(TESTING=False,TEST_PREMIUM_ACCESS=True)
        self.assertEqual(self.client.post('/generate',data=self.data(divination='tarot')).status_code,403)

    def test_public_pages_and_identity(self):
        for path in ('/plans','/privacy','/terms','/support','/commerce'):
            r=self.client.get(path)
            self.assertEqual(r.status_code,200)
            self.assertIn('no-store',r.headers['Cache-Control'])
        self.assertIn('下地 恵雄',self.client.get('/privacy').text)
        self.assertIn('keiyuu1975@yahoo.co.jp',self.client.get('/support').text)
        self.assertIn('500円',self.client.get('/plans').text)

    def test_partial_result_labels_and_reconfirmation(self):
        r=self.client.post('/generate',data=self.data(product='numbers3',pick_size='1'))
        self.assertEqual(r.status_code,200)
        self.assertIn('ラッキーナンバー',r.text)
        self.assertIn('このまま購入する組み合わせではありません',r.text)
        self.assertNotIn('ボックス参考',r.text)
        self.assertIn('name="pick_size" value="1"',r.text)

    def test_numbers_preserve_leading_zero_and_digit_repeats(self):
        rows=generate_product_rows('numbers3',10,{},seed='zero-check',pick_size=1)
        self.assertEqual({r['numbers'][0] for r in rows},set(range(10)))
        rows=generate_product_rows('numbers3',10,{},seed='repeats')
        self.assertTrue(any(len(set(r['numbers']))<3 for r in rows))

if __name__ == '__main__':
    unittest.main()
