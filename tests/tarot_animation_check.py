"""Inspect actual card reveal and result correspondence in mobile Edge."""
import sys
from pathlib import Path
from threading import Thread
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app import create_app
app=create_app({'TESTING':True,'RATE_LIMIT_PER_MINUTE':0,'SESSION_COOKIE_SECURE':False})
server=make_server('127.0.0.1',0,app,threaded=True)
Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport={'width':390,'height':844},reduced_motion='no-preference')
        page.goto(f'http://127.0.0.1:{server.server_port}')
        for field,value in [('birth_year','2000'),('birth_month','2'),('birth_day','29')]:
            page.locator('#'+field).select_option(value)
        page.locator('input[value="tarot"]').check(force=True)
        page.locator('[data-submit-button]').click()
        page.locator('.draw-card.is-open img').first.wait_for(state='attached')
        page.locator('[data-tarot-draw] img').evaluate_all('(imgs)=>Promise.all(imgs.map(i=>i.decode()))')
        page.locator('.draw-card:not(.is-open)').wait_for(state='detached')
        sources=page.locator('[data-tarot-draw] img').evaluate_all('(imgs)=>imgs.map(i=>i.src)')
        page.locator('#ritual').screenshot(path=str(ROOT.parent/'lotoscope_preview/tarot-animation-mobile.png'),animations='disabled')
        page.locator('#best-pick').wait_for()
        assert sources==page.locator('.tarot-card img').evaluate_all('(imgs)=>imgs.map(i=>i.src)')
        assert len(sources)==len(set(sources))
        assert page.locator('#divination-reading .profile-grid, #divination-reading .profile-details').count()==0
        page.locator('#divination-reading').screenshot(path=str(ROOT.parent/'lotoscope_preview/tarot-reading-mobile.png'))
        browser.close()
finally:
    server.shutdown()
    server.server_close()
print('PASS actual animation images match unique result cards')
