import re
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from app import create_app
from astrology_numbers import ZODIAC_SIGNS
from divination_numbers import calculate_divination_profile

class ZodiacArtworkTests(unittest.TestCase):
    def setUp(self):
        self.app=create_app({'TESTING':True,'RATE_LIMIT_PER_MINUTE':0,'SESSION_COOKIE_SECURE':False})

    def test_all_signs_resolve_and_unknown_input_cannot_be_a_path(self):
        with self.app.test_request_context('/'):
            context={};self.app.update_template_context(context)
            lookup=context['zodiac_image']
            images=[lookup(sign) for sign in ZODIAC_SIGNS]
            self.assertEqual(len(set(images)),12)
            self.assertNotIn(None,images)
            for filename in images:
                self.assertTrue((Path(self.app.static_folder)/filename).is_file())
            self.assertIsNone(lookup('../../app.py'))

    def test_missing_artwork_preserves_text_fallback(self):
        with self.app.test_request_context('/'):
            context={};self.app.update_template_context(context)
            with patch('app.Path.is_file',return_value=False):
                self.assertIsNone(context['zodiac_image']('牡羊座'))

    def test_actual_sun_moon_and_current_signs_get_correct_images(self):
        client=self.app.test_client()
        token=re.search(r'name="csrf_token" value="([^"]+)"',client.get('/').text)[1]
        from astrology_numbers import JST
        from datetime import datetime
        day=datetime.now(JST).date()
        with self.app.test_request_context('/'):
            context={};self.app.update_template_context(context)
            lookup=context['zodiac_image']
            for month in range(1,13):
                birthday=date(1990,month,15)
                profile=calculate_divination_profile('astrology',birthday,day)
                response=client.post('/generate',data={'csrf_token':token,'birth_date':birthday.isoformat(),'divination':'astrology','product':'loto6','count':'1','pick_size':'full'})
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.text.count('class="zodiac-image"'),3)
                for item in profile['summary_items']:
                    self.assertIn('/static/'+lookup(item['value']),response.text)

if __name__=='__main__': unittest.main()
