/* Same-day oracle UI. No localStorage, birthday cookies or external requests. */
(() => {
  'use strict';
  const dialog = document.getElementById('ritual');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let activeDraw = null;
  let disposeHome = () => {};

  const rituals = {
    astrology: [
      ['星の扉を開いています', '誕生日と今日の空を重ねて。'],
      ['七つの天体が、響きあう', '太陽、月、惑星のつながりを辿ります。'],
      ['星の光が、数字へ', '今日の空に浮かぶ、小さな導き。'],
      ['あなたの星が結ばれました', 'まもなく、今日の数字が届きます。'],
    ],
    kabbalah: [
      ['数の扉を開いています', '誕生日に秘められた数を辿って。'],
      ['光が、ひとつずつ結ばれる', '生命数と今日の周期を重ねます。'],
      ['数の響きが、ひとつに', 'あなたと今日をつなぐ、数の流れ。'],
      ['数秘の導きが整いました', 'まもなく、今日の数字が届きます。'],
    ],
    tarot: [
      ['カードの扉を開いています', '誕生日に結ばれたアルカナを。'],
      ['今日のカードを開くとき', 'カードの象徴と、今日の流れを重ねて。'],
      ['アルカナが、姿をあらわす', 'カードに宿る数を、そっと読み解きます。'],
      ['カードの導きが届きました', 'まもなく、今日の数字が届きます。'],
    ],
  };

  function showError(form, message) {
    const node = form.querySelector('.form-error');
    node.textContent = message;
    node.hidden = false;
    node.focus({ preventScroll: true });
    node.scrollIntoView({ behavior: reducedMotion.matches ? 'instant' : 'smooth', block: 'center' });
  }

  function birthValue(form) {
    const year = form.elements.birth_year;
    const month = form.elements.birth_month;
    const day = form.elements.birth_day;
    if (!year || !month || !day) return form.elements.birth_date?.value || '';
    [year, month, day].forEach((field) => field.setCustomValidity(''));
    if (!year.value || !month.value || !day.value) return '';
    const y = Number(year.value), m = Number(month.value), d = Number(day.value);
    const value = `${String(y).padStart(4, '0')}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    const date = new Date(Date.UTC(y, m - 1, d));
    if (date.getUTCFullYear() !== y || date.getUTCMonth() !== m - 1 || date.getUTCDate() !== d) {
      day.setCustomValidity('存在する日付を選択してください。');
      return '';
    }
    if (value > form.dataset.today) {
      year.setCustomValidity('未来の生年月日は選択できません。');
      return '';
    }
    return value;
  }

  function setupHome(form) {
    let previewTimer;
    let previewController;
    let previewKey = '';
    let disposed = false;
    const listeners = new AbortController();
    const preview = form.querySelector('.reading-preview');
    const selected = (name) => form.querySelector(`input[name="${name}"]:checked`);

    function stopPreview() {
      clearTimeout(previewTimer);
      previewController?.abort();
      previewController = null;
    }

    function queuePreview() {
      const birth = birthValue(form);
      const method = selected('divination');
      // Include JST date so a changed selection after midnight gets a fresh reading.
      const today = new Date(Date.now() + 9 * 3600000).toISOString().slice(0, 10);
      const key = birth && method ? `${today}|${method.value}|${birth}` : '';
      if (key && key === previewKey) return;
      stopPreview();
      previewKey = key;
      preview.hidden = true;
      preview.replaceChildren();
      if (!key) return;
      previewTimer = setTimeout(async () => {
        const controller = new AbortController();
        previewController = controller;
        const timeout = setTimeout(() => controller.abort(), 15000);
        try {
          const response = await fetch(form.dataset.previewUrl, {
            method: 'POST', body: new FormData(form), credentials: 'same-origin', cache: 'no-store',
            headers: { Accept: 'application/json' }, signal: controller.signal,
          });
          const data = await response.json();
          if (!response.ok) throw new Error(data.error || '');
          if (disposed || controller.signal.aborted || previewKey !== key) return;
          const children = (data.summary_items || []).slice(0, 3).map((item) => {
            const node = document.createElement('div');
            const label = document.createElement('small');
            const value = document.createElement('strong');
            label.textContent = item.label;
            value.textContent = item.value;
            node.append(label, value);
            return node;
          });
          preview.replaceChildren(...children);
          preview.hidden = !children.length;
        } catch (error) {
          if (!disposed && previewKey === key && !controller.signal.aborted) {
            preview.hidden = true;
            previewKey = ''; // A later selection can retry; generation remains usable.
          }
        } finally {
          clearTimeout(timeout);
        }
      }, 350);
    }

    function updateDays() {
      const y = Number(form.elements.birth_year.value) || 2000;
      const m = Number(form.elements.birth_month.value);
      const maximum = m ? new Date(Date.UTC(y, m, 0)).getUTCDate() : 31;
      Array.from(form.elements.birth_day.options).forEach((option) => {
        option.disabled = Boolean(option.value && Number(option.value) > maximum);
      });
      if (Number(form.elements.birth_day.value) > maximum) form.elements.birth_day.value = '';
    }

    function updateSelection() {
      const method = selected('divination');
      const product = selected('product');
      if (!method || !product) return;
      document.getElementById('main-content').dataset.theme = method.value;
      form.querySelector('[data-selection-description]').textContent = method.dataset.description;
      form.querySelector('[data-summary-method]').textContent = method.dataset.name;
      form.querySelector('[data-summary-product]').textContent = product.dataset.name;
      form.querySelector('[data-summary-count]').textContent = `${form.elements.count.value}口`;
      form.querySelector('[data-button-copy]').textContent = method.dataset.buttonLabel;
    }

    // Recover a selection when displaying an invalid native form submission.
    for (const name of ['divination', 'product']) {
      if (!selected(name)) form.querySelector(`input[name="${name}"]`).checked = true;
    }
    form.addEventListener('change', (event) => {
      if (event.target.name.startsWith('birth_')) updateDays();
      updateSelection();
      if (event.target.name !== 'product' && event.target.name !== 'count') queuePreview();
    }, { signal: listeners.signal });
    updateDays();
    updateSelection();
    queuePreview();
    return () => { disposed = true; listeners.abort(); stopPreview(); };
  }

  function selectionFor(form) {
    const method = form.querySelector('input[name="divination"]:checked');
    const product = form.querySelector('input[name="product"]:checked');
    return {
      method: form.elements.divination.value,
      methodName: method?.dataset.name || form.dataset.methodName,
      english: method?.dataset.english || form.dataset.methodEnglish,
      productName: product?.dataset.name || form.dataset.productName,
      duration: Number(product?.dataset.duration || form.dataset.duration) || 4400,
    };
  }

  function startRitual(selection) {
    const card = dialog.querySelector('.ritual-card');
    const progress = dialog.querySelector('progress');
    const title = dialog.querySelector('#ritual-title');
    const text = dialog.querySelector('#ritual-text');
    const phases = rituals[selection.method] || rituals.astrology;
    card.dataset.theme = selection.method;
    dialog.querySelector('[data-ritual-kicker]').textContent = selection.english;
    dialog.querySelector('[data-ritual-product]').textContent = `${selection.methodName} × ${selection.productName}`;
    const duration = reducedMotion.matches ? 0 : selection.duration;
    const timers = [];
    let resolveDone;
    const done = new Promise((resolve) => { resolveDone = resolve; });
    const phase = (index) => {
      card.dataset.phase = String(index);
      progress.value = index;
      [title.textContent, text.textContent] = phases[Math.min(index, 3)];
    };
    phase(0);
    document.body.classList.add('is-drawing');
    dialog.showModal();
    // Focus the cancel control without announcing every decorative object.
    dialog.querySelector('[data-cancel-ritual]').focus({ preventScroll: true });
    for (let index = 1; index < 4; index += 1) {
      timers.push(setTimeout(() => phase(index), duration * index / 4));
    }
    timers.push(setTimeout(() => {
      phase(4);
      title.textContent = '導きを受け取っています';
      text.textContent = '接続状況により、少し時間がかかることがあります。';
      resolveDone();
    }, duration));
    return {
      done,
      close() {
        timers.forEach(clearTimeout);
        resolveDone();
        if (dialog.open) dialog.close();
        document.body.classList.remove('is-drawing');
      },
    };
  }

  function replacePage(html) {
    const parsed = new DOMParser().parseFromString(html, 'text/html');
    const main = parsed.getElementById('main-content');
    if (!main || !main.querySelector('#best-pick')) throw new Error('結果を表示できませんでした。もう一度お試しください。');
    disposeHome();
    document.getElementById('main-content').replaceWith(document.importNode(main, true));
    document.title = parsed.title;
    // Keep the birthday and result out of URL, browser storage and history state.
    initPage();
    window.scrollTo({ top: 0, behavior: 'instant' });
    document.querySelector('main h1')?.focus({ preventScroll: true });
  }

  function cancelDraw() {
    if (!activeDraw) return;
    const draw = activeDraw;
    activeDraw = null;
    draw.controller.abort();
    draw.ritual.close();
    clearTimeout(draw.timeout);
    draw.button.disabled = false;
    draw.form.removeAttribute('aria-busy');
    draw.button.focus({ preventScroll: true });
  }

  async function submitOracle(event) {
    const form = event.currentTarget;
    if (form.hasAttribute('data-home-form')) birthValue(form);
    if (!form.reportValidity()) { event.preventDefault(); return; }
    // The real form remains a fully functional fallback without modern APIs.
    if (!window.fetch || !window.DOMParser || !dialog?.showModal) return;
    event.preventDefault();
    if (activeDraw) return;
    const button = form.querySelector('[data-submit-button]');
    const data = new FormData(form);
    const selection = selectionFor(form);
    const controller = new AbortController();
    const errorNode = form.querySelector('.form-error');
    errorNode.hidden = true;
    button.disabled = true;
    form.setAttribute('aria-busy', 'true');
    let timedOut = false;
    // Start the request immediately, before running the decorative animation.
    const responsePromise = fetch(form.action, {
      method: 'POST', body: data, credentials: 'same-origin', cache: 'no-store',
      headers: { Accept: 'application/json' }, signal: controller.signal,
    }).then(async (response) => {
      let payload;
      try { payload = await response.json(); }
      catch { throw new Error('応答を読み取れませんでした。少し時間をおいてお試しください。'); }
      if (!response.ok) throw new Error(payload.error || '数字を受け取れませんでした。');
      if (typeof payload.html !== 'string') throw new Error('結果を読み取れませんでした。');
      return payload;
    });
    const ritual = startRitual(selection);
    const timeout = setTimeout(() => { timedOut = true; controller.abort(); }, 60000);
    const draw = { controller, ritual, timeout, button, form };
    activeDraw = draw;
    try {
      const [payload] = await Promise.all([responsePromise, ritual.done]);
      if (activeDraw !== draw) return;
      ritual.close();
      replacePage(payload.html);
    } catch (error) {
      if (activeDraw !== draw) return;
      ritual.close();
      const message = timedOut ? '接続に時間がかかっています。入力内容は残っていますので、少し待ってからお試しください。'
        : error.name === 'TypeError' ? '通信が途切れました。接続を確認して、もう一度お試しください。' : error.message;
      showError(form, message);
    } finally {
      clearTimeout(timeout);
      if (activeDraw === draw) {
        activeDraw = null;
        button.disabled = false;
        form.removeAttribute('aria-busy');
      }
    }
  }

  function initPage() {
    const form = document.querySelector('[data-home-form]');
    disposeHome = form ? setupHome(form) : () => {};
    document.querySelectorAll('[data-oracle-form]').forEach((node) => node.addEventListener('submit', submitOracle));
    if (!reducedMotion.matches) {
      document.querySelectorAll('.number-reveal-group').forEach((group) => group.classList.add('is-revealing'));
    }
  }

  dialog?.querySelector('[data-cancel-ritual]').addEventListener('click', cancelDraw);
  dialog?.addEventListener('cancel', (event) => { event.preventDefault(); cancelDraw(); });
  window.addEventListener('pagehide', () => { cancelDraw(); disposeHome(); });
  window.addEventListener('pageshow', (event) => {
    if (event.persisted) {
      // BFCache restores DOM with listeners intact. Only reconnect the preview.
      const form = document.querySelector('[data-home-form]');
      if (form) disposeHome = setupHome(form);
    }
  });
  initPage();
})();
