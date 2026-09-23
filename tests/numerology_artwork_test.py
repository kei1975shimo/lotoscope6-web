import re
import unittest
from pathlib import Path
from unittest.mock import patch
from app import create_app

class NumerologyArtworkTests(unittest.TestCase):
    def setUp(self):
        self.app=create_app({'TESTING':True,'RATE_LIMIT_PER_MINUTE':0,'SESSION_COOKIE_SECURE':False})

    def test_all_emblems_and_tree_resolve_with_strict_names(self):
        with self.app.test_request_context('/'):
            context={};self.app.update_template_context(context)
            lookup=context['numerology_image']
            names=[lookup(str(n)) for n in [1,2,3,4,5,6,7,8,9,11,22,33]]
            self.assertEqual(len(set(names)),12)
            self.assertNotIn(None,names)
            for filename in names+[context['kabbalah_tree_image']()]:
                self.assertTrue((Path(self.app.static_folder)/filename).is_file())
            for invalid in ['0','10','34','../app.py','11.0']:
                self.assertIsNone(lookup(invalid))

    def test_missing_artwork_falls_back(self):
        with self.app.test_request_context('/'):
            context={};self.app.update_template_context(context)
            with patch('app.Path.is_file',return_value=False):
                self.assertIsNone(context['numerology_image']('11'))
                self.assertEqual(context['kabbalah_tree_image'](),'img/oracle-kabbalah.webp')

    def test_master_numbers_keep_their_own_images(self):
        client=self.app.test_client()
        token=re.search(r'name="csrf_token" value="([^"]+)"',client.get('/').text)[1]
        for birth,number in [('1990-01-09',11),('1990-01-02',22),('1990-03-29',33)]:
            response=client.post('/generate',data={'csrf_token':token,'birth_date':birth,'divination':'kabbalah','product':'loto6','count':'1','pick_size':'full'})
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.text.count('class="numerology-image"'),3)
            self.assertIn(f'/static/img/numerology-{number}.webp',response.text)
            self.assertIn('/static/img/kabbalah-tree-of-life.webp',response.text)

if __name__=='__main__': unittest.main()
