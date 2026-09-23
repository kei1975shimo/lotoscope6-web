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
        page=browser.new_page(viewport={'width':1280,'height':900},reduced_motion='no-preference')
        page.goto((ROOT/'docs/numerology_gallery.html').as_uri())
        page.locator('img').evaluate_all('(imgs)=>Promise.all(imgs.map(i=>i.decode()))')
        assert page.locator('img').count()==13
        assert page.locator('img').evaluate_all('(imgs)=>imgs.every(i=>i.naturalWidth===640 && i.naturalHeight===640)')
        page.screenshot(path=str(ROOT.parent/'numerology_artwork/overview.png'),full_page=True)
        page.set_viewport_size({'width':390,'height':844})
        page.goto(f'http://127.0.0.1:{server.server_port}')
        for field,value in [('birth_year','1990'),('birth_month','3'),('birth_day','29')]:
            page.locator('#'+field).select_option(value)
        page.locator('input[value="kabbalah"]').check(force=True)
        page.locator('[data-submit-button]').click()
        page.locator('.ritual-card[data-phase="1"]').wait_for()
        page.locator('.kabbalah-tree').evaluate('(i)=>i.decode()')
        assert page.locator('.tree-sparks circle').count()==10
        assert page.locator('.tree-sparks circle').first.evaluate('(c)=>getComputedStyle(c).animationName')=='tree-spark'
        page.locator('#ritual').screenshot(path=str(ROOT.parent/'lotoscope_preview/numerology-animation-mobile.png'),animations='disabled')
        page.locator('#best-pick').wait_for()
        assert page.locator('.numerology-image').count()==3
        assert page.locator('.numerology-image').first.get_attribute('src').endswith('numerology-33.webp')
        for width in (320,390,768,1280):
            page.set_viewport_size({'width':width,'height':900})
            for img in page.locator('.numerology-image').all():
                img.scroll_into_view_if_needed();img.evaluate('(i)=>i.decode()')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            if width==390:
                page.locator('#divination-reading').screenshot(path=str(ROOT.parent/'lotoscope_preview/numerology-reading-mobile.png'))
        page.emulate_media(reduced_motion='reduce')
        page.locator('[data-submit-button]').click()
        page.locator('#ritual').wait_for(state='hidden')
        assert page.locator('.tree-sparks circle').first.evaluate('(c)=>getComputedStyle(c).animationName')=='none'
        browser.close()
finally:
    server.shutdown();server.server_close()
print('PASS 13 assets, master-number result, tree animation and 4 viewport widths')
