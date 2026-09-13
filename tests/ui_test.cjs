/* Offline DOM integration tests. No real browser or network connection.
   Modal drawing and layout require a separate real-device visual check. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { JSDOM, VirtualConsole } = require('jsdom');
const FakeTimers = require('@sinonjs/fake-timers');
const root = path.resolve(__dirname, '..');
const run = spawnSync(process.env.PYTHON || 'python', [path.join(__dirname, 'ui_fixtures.py')], { cwd: root, encoding: 'utf8', maxBuffer: 4 * 1024 * 1024 });
if (run.error) throw run.error;
assert.equal(run.status, 0, run.stderr);
const fixtures = JSON.parse(run.stdout);
const source = fs.readFileSync(path.join(root, 'static/js/app.js'), 'utf8');
let passed = 0;

function setup({ mode = 'ok', latency = 20, reduce = false, html = fixtures.home } = {}) {
  const consoleErrors = [];
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('jsdomError', (error) => consoleErrors.push(error.message));
  const dom = new JSDOM(html, { url: 'https://oracle.test/', runScripts: 'outside-only', virtualConsole });
  const { window } = dom;
  const clock = FakeTimers.withGlobal(window).install({ now: new Date('2026-09-12T00:00:00Z'), toFake: ['setTimeout', 'clearTimeout', 'Date'] });
  window.matchMedia = () => ({ matches: reduce });
  window.scrollTo = () => {};
  window.HTMLElement.prototype.scrollIntoView = () => {};
  window.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
  window.HTMLDialogElement.prototype.close = function () { this.open = false; };
  const calls = [];
  const state = { mode, latency };
  window.fetch = (url, options = {}) => {
    const record = { url: String(url), at: clock.now, method: options.method, data: Object.fromEntries(options.body || []) };
    calls.push(record);
    return new Promise((resolve, reject) => {
      const abort = () => { const error = new Error('aborted'); error.name = 'AbortError'; reject(error); };
      options.signal?.addEventListener('abort', abort, { once: true });
      if (options.signal?.aborted) { abort(); return; }
      window.setTimeout(() => {
        if (options.signal?.aborted) return;
        if (String(url).endsWith('/divination-preview')) {
          resolve({ ok: true, json: async () => ({ summary_items: [{ label: '生命数', value: '7' }] }) });
          return;
        }
        if (state.mode === 'network') { const err = new Error('offline'); err.name = 'TypeError'; reject(err); return; }
        if (state.mode === 'malformed') { resolve({ ok: true, json: async () => { throw new Error('bad JSON'); } }); return; }
        if (state.mode === 'error429') { resolve({ ok: false, json: async () => ({ error: '60秒ほど待ってからお試しください。' }) }); return; }
        if (state.mode === 'csrf') { resolve({ ok: false, json: async () => ({ error: 'フォームの有効期限が切れました。' }) }); return; }
        resolve({ ok: true, json: async () => fixtures.results[record.data.divination + '|' + record.data.product] });
      }, String(url).endsWith('/divination-preview') ? 10 : state.latency);
    });
  };
  window.eval(source);
  const doc = window.document;
  const select = (name, value) => {
    const field = doc.querySelector(`[name="${name}"]`);
    field.value = value;
    field.dispatchEvent(new window.Event('change', { bubbles: true }));
  };
  const radio = (name, value) => {
    const field = doc.querySelector(`input[name="${name}"][value="${value}"]`);
    field.checked = true;
    field.dispatchEvent(new window.Event('change', { bubbles: true }));
  };
  const birth = () => { select('birth_year', '2000'); select('birth_month', '2'); select('birth_day', '29'); };
  const submit = () => doc.querySelector('[data-oracle-form]').dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true }));
  return { window, doc, clock, calls, state, select, radio, birth, submit, consoleErrors, close() { clock.uninstall(); window.close(); } };
}

async function test(name, action) {
  await action();
  passed += 1;
  console.log('PASS', name);
}

(async () => {
  await test('generation starts immediately; result waits only for the minimum ritual; repeat reuses the flow', async () => {
    const t = setup(); t.birth(); t.select('count', '10');
    const start = t.clock.now; t.submit(); t.submit();
    assert.equal(t.calls.filter(c => c.url.endsWith('/generate')).length, 1);
    assert.equal(t.calls[0].at, start);
    assert.ok(t.doc.getElementById('ritual').open);
    await t.clock.tickAsync(4699);
    assert.equal(t.doc.querySelector('#best-pick'), null);
    await t.clock.tickAsync(2);
    assert.ok(t.doc.querySelector('#best-pick'));
    assert.equal(t.doc.querySelectorAll('.ticket').length, 9);
    const numbers = t.doc.querySelector('.best-numbers').textContent;
    t.submit();
    assert.ok(t.doc.getElementById('ritual').open);
    await t.clock.tickAsync(4701);
    assert.equal(t.doc.querySelector('.best-numbers').textContent, numbers);
    assert.equal(t.calls.filter(c => c.url.endsWith('/generate')).length, 2);
    assert.equal(t.window.location.href, 'https://oracle.test/');
    assert.equal(t.window.localStorage.length, 0);
    assert.equal(t.window.sessionStorage.length, 0);
    assert.deepEqual(t.consoleErrors, []); t.close();
  });

  await test('slow response and animation run in parallel', async () => {
    const t = setup({ latency: 8000 }); t.birth(); t.submit();
    await t.clock.tickAsync(4701);
    assert.ok(t.doc.getElementById('ritual').open);
    assert.equal(t.doc.querySelector('#best-pick'), null);
    await t.clock.tickAsync(3300);
    assert.ok(t.doc.querySelector('#best-pick')); t.close();
  });

  for (const mode of ['network', 'malformed', 'error429', 'csrf']) {
    await test(`${mode}: closes the ritual, preserves input and allows an explicit retry`, async () => {
      const t = setup({ mode }); t.birth(); t.submit();
      await t.clock.tickAsync(25);
      assert.equal(t.doc.getElementById('ritual').open, false);
      assert.equal(t.doc.querySelector('[name="birth_year"]').value, '2000');
      assert.equal(t.doc.querySelector('[data-submit-button]').disabled, false);
      assert.equal(t.doc.querySelector('.form-error').hidden, false);
      assert.equal(t.calls.filter(c => c.url.endsWith('/generate')).length, 1);
      t.state.mode = 'ok'; t.submit(); await t.clock.tickAsync(4701);
      assert.ok(t.doc.querySelector('#best-pick')); t.close();
    });
  }

  await test('timeout recovers controls after 60 seconds', async () => {
    const t = setup({ latency: 120000 }); t.birth(); t.submit();
    await t.clock.tickAsync(60001);
    assert.equal(t.doc.getElementById('ritual').open, false);
    assert.match(t.doc.querySelector('.form-error').textContent, /接続に時間/);
    assert.equal(t.doc.querySelector('[data-submit-button]').disabled, false); t.close();
  });

  await test('cancel discards the pending result and supports retry', async () => {
    const t = setup({ latency: 7000 }); t.birth(); t.submit();
    t.doc.querySelector('[data-cancel-ritual]').click();
    await t.clock.tickAsync(8000);
    assert.equal(t.doc.querySelector('#best-pick'), null);
    assert.equal(t.doc.querySelector('[data-submit-button]').disabled, false);
    t.state.latency = 10; t.submit(); await t.clock.tickAsync(4701);
    assert.ok(t.doc.querySelector('#best-pick')); t.close();
  });

  await test('reduced motion has no mandatory decorative delay', async () => {
    const t = setup({ reduce: true }); t.birth(); t.submit();
    await t.clock.tickAsync(21);
    assert.ok(t.doc.querySelector('#best-pick'));
    assert.equal(t.doc.querySelector('.is-revealing'), null); t.close();
  });

  await test('all 15 method/product combinations set the right theme and label', async () => {
    for (const method of ['astrology', 'kabbalah', 'tarot']) {
      for (const product of ['miniloto', 'loto6', 'loto7', 'numbers3', 'numbers4']) {
        const t = setup(); t.birth(); t.radio('divination', method); t.radio('product', product); t.select('count', '10');
        const chosen = t.doc.querySelector(`input[name="divination"][value="${method}"]`);
        assert.equal(t.doc.querySelector('[data-button-copy]').textContent, chosen.dataset.buttonLabel);
        t.submit();
        assert.equal(t.doc.querySelector('.ritual-card').dataset.theme, method);
        await t.clock.tickAsync(5500);
        assert.equal(t.doc.querySelector('main').dataset.theme, method);
        assert.equal(t.doc.querySelector('.number-reveal-group').dataset.revealProduct, product);
        t.close();
      }
    }
  });

  await test('preview uses POST, aborts stale requests and keeps birth data out of URL', async () => {
    const t = setup(); t.birth(); t.radio('divination', 'tarot'); t.radio('divination', 'kabbalah');
    await t.clock.tickAsync(370);
    const previewCalls = t.calls.filter(c => c.url.endsWith('/divination-preview'));
    assert.equal(previewCalls.length, 1);
    assert.equal(previewCalls[0].method, 'POST');
    assert.ok(!previewCalls[0].url.includes('?'));
    assert.equal(t.doc.querySelector('.reading-preview').hidden, false); t.close();
  });

  await test('calendar validation blocks impossible dates and missing birthday', async () => {
    const t = setup(); t.submit(); assert.equal(t.calls.length, 0);
    t.birth(); t.select('birth_year', '2001');
    assert.equal(t.doc.querySelector('[name="birth_day"]').value, '');
    t.submit(); assert.equal(t.calls.length, 0); t.close();
  });

  await test('BFCache restores exactly one preview listener', async () => {
    const t = setup(); t.birth();
    t.window.dispatchEvent(new t.window.PageTransitionEvent('pagehide', { persisted: true }));
    t.window.dispatchEvent(new t.window.PageTransitionEvent('pageshow', { persisted: true }));
    t.radio('divination', 'tarot'); await t.clock.tickAsync(370);
    assert.equal(t.calls.filter(c => c.url.endsWith('/divination-preview')).length, 1); t.close();
  });

  console.log(`${passed} offline UI integration tests passed.`);
})().catch(error => { console.error(error); process.exitCode = 1; });
