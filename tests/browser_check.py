"""Local Edge integration check; server and browser are closed on completion."""
import sys
import logging
from pathlib import Path
from threading import Thread
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app import create_app

def main():
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    output=ROOT.parent/'lotoscope_preview'
    output.mkdir(exist_ok=True)
    app=create_app({'TESTING':True,'RATE_LIMIT_PER_MINUTE':0,'SESSION_COOKIE_SECURE':False})
    server=make_server('127.0.0.1',0,app,threaded=True)
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    origin=f'http://127.0.0.1:{server.server_port}'
    checks=0
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True)
            context=browser.new_context(viewport={'width':1280,'height':1000},reduced_motion='reduce')
            page=context.new_page()
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(origin)
            page.screenshot(path=str(output/'home-desktop.png'),full_page=True)
            page.locator('.oracle-hero').screenshot(path=str(output/'hero-desktop.png'))
            assert page.locator('.locked-oracle').count()==0
            assert page.locator('.oracle-hero').bounding_box()['height'] < 380
            for width in (320,390,768,1280):
                page.set_viewport_size({'width':width,'height':900})
                for route in ('/','/plans','/privacy','/terms','/support','/commerce'):
                    page.goto(origin+route)
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(width,route)
                    checks+=1
                    if width==390 and route in ('/','/plans'):
                        page.screenshot(path=str(output/('home-mobile.png' if route=='/' else 'plans-mobile.png')),full_page=True)
            page.goto(origin)
            page.set_viewport_size({'width':390,'height':844})
            page.locator('.oracle-section').screenshot(path=str(output/'readable-oracles-mobile.png'))
            page.screenshot(path=str(output/'readable-mobile-top.png'))
            assert page.locator('.oracle-hero').count() == 0 or page.locator('.oracle-hero').bounding_box()['height'] < 370
            for method in ('astrology','kabbalah','tarot'):
                for product,full in [('miniloto',5),('loto6',6),('loto7',7),('numbers3',3),('numbers4',4)]:
                    page.goto(origin)
                    page.locator('#birth_year').select_option('2000')
                    page.locator('#birth_month').select_option('2')
                    page.locator('#birth_day').select_option('29')
                    page.locator(f'input[value="{method}"]').check(force=True)
                    page.locator(f'input[value="{product}"]').check(force=True)
                    assert page.locator('#pick_size').input_value()=='full'
                    page.locator('[data-submit-button]').click()
                    page.locator('#best-pick').wait_for()
                    assert page.locator('.best-numbers .number').count()==full
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    before=page.locator('.best-numbers').inner_text()
                    with page.expect_response('**/generate'):
                        page.locator('[data-submit-button]').click()
                    page.locator('#ritual').wait_for(state='hidden')
                    assert page.locator('.best-numbers').inner_text()==before
                    checks+=1
            page.goto(origin)
            for selector,value in [('birth_year','2000'),('birth_month','2'),('birth_day','29'),('pick_size','1'),('count','10')]:
                page.locator('#'+selector).select_option(value)
            page.locator('[data-submit-button]').click()
            page.locator('#best-pick').wait_for()
            values=page.locator('.best-numbers .number, .ticket summary .number').all_text_contents()
            assert len(values)==len(set(values))==10
            assert page.locator('.partial-notice').count()==1
            page.screenshot(path=str(output/'result-mobile.png'),full_page=True)
            checks+=1
            for width in (320,390,430):
                page.set_viewport_size({'width':width,'height':844})
                page.goto(origin)
                for name,value in [('birth_year','2000'),('birth_month','2'),('birth_day','29'),('count','10')]:
                    page.locator('#'+name).select_option(value)
                page.locator('input[value="loto7"]').check(force=True)
                page.locator('[data-submit-button]').click()
                page.locator('#best-pick').wait_for()
                page.locator('details').evaluate_all('(nodes) => nodes.forEach(node => node.open = true)')
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),width
                if width==390:
                    page.screenshot(path=str(output/'readable-result-mobile.png'),full_page=True)
                checks+=1
            # Real native form, with scripts disabled: default adapts to each product.
            native=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844})
            n=native.new_page()
            for product,full in [('miniloto',5),('loto6',6),('loto7',7),('numbers3',3),('numbers4',4)]:
                n.goto(origin)
                for name,value in [('birth_year','2000'),('birth_month','2'),('birth_day','29')]:
                    n.locator('#'+name).select_option(value)
                n.locator(f'input[value="{product}"]').check(force=True)
                n.locator('[data-submit-button]').click()
                n.locator('#best-pick').wait_for()
                assert n.locator('.best-numbers .number').count()==full
                checks+=1
            assert not errors,errors
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    print(f'PASS: {checks} browser checks; screenshots: {output}')

if __name__=='__main__':
    main()
