"""Render real Flask templates for the offline JavaScript interaction tests."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app

app = create_app({'TESTING': True, 'TEST_PREMIUM_ACCESS': True, 'SECRET_KEY': 'ui-test', 'RATE_LIMIT_PER_MINUTE': 0, 'TRUSTED_PROXY_HOPS': 0, 'SESSION_COOKIE_SECURE': False})
client = app.test_client()
home = client.get('/').text
token = re.search(r'name="csrf_token" value="([^"]+)"', home)[1]
results = {}
for method in ('astrology', 'kabbalah', 'tarot'):
    for product in ('miniloto', 'loto6', 'loto7', 'numbers3', 'numbers4'):
        data = dict(csrf_token=token, divination=method, product=product, birth_date='2000-02-29', count='10')
        response = client.post('/generate', data=data, headers={'Accept': 'application/json'})
        assert response.status_code == 200
        results[method + '|' + product] = response.json
print(json.dumps({'home': home, 'results': results}, ensure_ascii=False))
