import sys, logging
from pathlib import Path
from threading import Thread
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app import create_app
logging.getLogger('werkzeug').setLevel(logging.ERROR)
app=create_app({'TESTING':True,'RATE_LIMIT_PER_MINUTE':0,'SESSION_COOKIE_SECURE':False})
server=make_server('127.0.0.1',0,app,threaded=True)
Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport={'width':1280,'height':900},reduced_motion='reduce')
        page.goto((ROOT/'docs/zodiac_gallery.html').as_uri())
        page.locator('img').evaluate_all('(imgs)=>Promise.all(imgs.map(i=>i.decode()))')
        assert page.locator('img').count()==12
        assert page.locator('img').evaluate_all('(imgs)=>imgs.every(i=>i.naturalWidth===640 && i.naturalHeight===640)')
        page.screenshot(path=str(ROOT.parent/'zodiac_artwork/overview.png'),full_page=True)
        page.goto(f'http://127.0.0.1:{server.server_port}')
        for field,value in [('birth_year','2000'),('birth_month','2'),('birth_day','29')]:
            page.locator('#'+field).select_option(value)
        page.locator('[data-submit-button]').click()
        page.locator('#best-pick').wait_for()
        assert page.locator('.zodiac-image').count()==3
        for width in (320,390,768,1280):
            page.set_viewport_size({'width':width,'height':900})
            for img in page.locator('.zodiac-image').all():
                img.scroll_into_view_if_needed();img.evaluate('(i)=>i.decode()')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            if width==390:
                page.locator('#divination-reading').screenshot(path=str(ROOT.parent/'lotoscope_preview/zodiac-reading-mobile.png'))
        browser.close()
finally:
    server.shutdown();server.server_close()
print('PASS 12 zodiac assets and result images at 4 viewport widths')
