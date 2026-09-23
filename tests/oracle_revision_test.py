import json
import re
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from app import create_app, build_daily_oracle_seed
from astrology_numbers import to_loto_number
from divination_numbers import (TAROT_IMAGE_FILES, _add_weight, _fold43, _tarot_card,
                                calculate_divination_profile)
from product_numbers import generate_product_rows, product_choices
from tests.generation_contract import BIRTHS, DAYS, samples, digest

ROOT = Path(__file__).resolve().parents[1]


class GenerationCompatibilityTests(unittest.TestCase):
    def test_v1172_snapshot_repetition_and_all_prefixes(self):
        baseline = json.loads((ROOT/'tests/fixtures/v1_17_2_generation.json').read_text())
        visited = set()
        for key, product, size, profile, seed in samples():
            with self.subTest(condition=key):
                rows = generate_product_rows(product, 10, profile, seed, pick_size=size)
                self.assertEqual(digest(rows), baseline[key])
                self.assertEqual(generate_product_rows(product, 10, profile, seed, pick_size=size), rows)
                for count in (1, 3, 5):
                    self.assertEqual(generate_product_rows(product, count, profile, seed, pick_size=size), rows[:count])
                visited.add(key)
        self.assertEqual(visited, set(baseline))
        self.assertEqual(len(visited), 900)

    def test_astrology_historical_mapping_is_not_silently_shifted(self):
        for value, expected in ((0,1),(1,2),(42,43),(43,1),(44,2),(-1,43)):
            self.assertEqual(to_loto_number(value),expected)

    def test_tarot_high_band_and_lottery_ranges(self):
        high_generated, high_pool = set(), set()
        for birth in BIRTHS:
            for day in DAYS:
                profile = calculate_divination_profile('tarot', birth, day)
                self.assertTrue(all(1 <= n <= 43 for n in profile['pool_numbers']))
                high_pool.update(n for n in profile['pool_numbers'] if n >= 23)
                for product in product_choices():
                    if product['kind'] != 'loto':
                        continue
                    seed=build_daily_oracle_seed(birth,day,'tarot',product['product_id'])
                    for size in range(1, product['full_size'] + 1):
                        rows=generate_product_rows(product['product_id'],10,profile,seed,pick_size=size)
                        for row in rows:
                            self.assertTrue(all(1 <= n <= product['max_number'] for n in row['numbers']))
                            if product['product_id']=='loto6':
                                high_generated.update(n for n in row['numbers'] if n>=23)
        self.assertEqual(high_generated,set(range(23,44)))
        # The profile pool is a ranked subset, not an enumeration of all 43.
        self.assertTrue(high_pool)

    def test_shadow_circulation_including_fool_is_retained(self):
        for number in range(1,23):
            weights={}
            _add_weight(weights,number+22,65)
            expected=number+22 if number<22 else 1
            self.assertEqual(weights,{expected:65.0})
        with patch('divination_numbers._add_weight',wraps=_add_weight) as add:
            profile=calculate_divination_profile('tarot',date(1900,1,29),DAYS[0])
        self.assertEqual(profile['tarot_cards'][0]['number'],22)
        self.assertTrue(any(c.args[1:]==(44,65) for c in add.call_args_list))
        self.assertGreaterEqual(profile['weights'][1],65)


class CardPresentationTests(unittest.TestCase):
    def setUp(self):
        self.app=create_app({'TESTING':True,'PREMIUM_PREVIEW_ENABLED':True,'SECRET_KEY':'test',
                             'RATE_LIMIT_PER_MINUTE':0,'SESSION_COOKIE_SECURE':False})
        self.client=self.app.test_client()
        token=re.search(r'name="csrf_token" value="([^"]+)"',self.client.get('/').text)[1]
        self.data=dict(csrf_token=token,birth_date='2000-02-29',divination='tarot',product='loto6',count='3',pick_size='full')

    def test_all_22_image_names_and_four_roles(self):
        cards=[_tarot_card(n) for n in range(1,23)]
        self.assertEqual(len({c['image_filename'] for c in cards}),22)
        self.assertEqual(cards[-1]['image_filename'],'img/tarot-00-fool.webp')
        self.assertEqual(cards[-1]['number'],22)
        self.assertEqual(cards[0]['image_filename'],'img/tarot-01-magician.webp')
        self.assertEqual(cards[20]['image_filename'],'img/tarot-21-world.webp')
        profile=calculate_divination_profile('tarot',date(2000,2,29),DAYS[0])
        self.assertEqual([c['role'] for c in profile['tarot_cards']],['誕生カード','魂のカード','今日のカード','橋渡しカード'])

    def test_missing_artwork_falls_back_without_broken_urls(self):
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as temp:
            previous=self.app.static_folder
            try:
                self.app.static_folder=temp
                r=self.client.post('/generate',data=self.data)
                self.assertEqual(r.status_code,200)
                self.assertEqual(r.text.count('<figure class="tarot-card">'), len({c['number'] for c in calculate_divination_profile('tarot',date(2000,2,29),DAYS[0])['tarot_cards']}))
                self.assertEqual(r.text.count('<small>共通イメージ</small>'), r.text.count('<figure class="tarot-card">'))
                self.assertNotRegex(r.text,r'src="[^"]*tarot-\d{2}-')
            finally:
                self.app.static_folder=previous

    def test_present_artwork_is_used_and_other_cards_still_fall_back(self):
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as temp:
            previous=self.app.static_folder
            try:
                self.app.static_folder=temp
                # Install just one real image at the birth-card filename.
                card=calculate_divination_profile('tarot',date(2000,2,29),DAYS[0])['tarot_cards'][0]
                target=Path(temp)/card['image_filename']
                target.parent.mkdir()
                shutil.copyfile(ROOT/'static/img/oracle-tarot.webp',target)
                r=self.client.post('/generate',data=self.data)
                self.assertEqual(r.status_code,200)
                self.assertIn(f'src="/static/{card["image_filename"]}"',r.text)
                self.assertIn('<small>共通イメージ</small>',r.text)
                image_response=self.client.get('/static/'+card['image_filename'])
                self.assertEqual(image_response.status_code,200)
                image_response.close()
            finally:
                self.app.static_folder=previous

    def test_correct_labels_score_formula_and_other_methods(self):
        for method in ('astrology','kabbalah','tarot'):
            r=self.client.post('/generate',data={**self.data,'divination':method})
            self.assertEqual(r.status_code,200)
            self.assertIn('数字の総合スコア',r.text)
            self.assertIn('78％＋数字構成22％',r.text)
            self.assertIn('当せん確率ではありません',r.text)
            self.assertIn('／ 数字構成',r.text)
            if method!='tarot':
                self.assertNotIn('class="tarot-card-grid"',r.text)
                self.assertIn(f'img/oracle-{method}.webp',r.text)
            if method=='astrology':
                self.assertNotIn('出生時 ',r.text)
                self.assertIn('生まれた日の正午（日本時間）',r.text)
                self.assertIn('出生時刻・出生地を使わない簡易星読み',r.text)
            if method=='tarot':
                self.assertIn('ロト6では23〜43も候補',r.text)


if __name__=='__main__':
    unittest.main()
