document.addEventListener('touchstart', function () {}, { passive: true });

function getBirthDateControls(form) {
  return {
    hidden: form.querySelector('#birth_date'),
    year: form.querySelector('#birth_year'),
    month: form.querySelector('#birth_month'),
    day: form.querySelector('#birth_day'),
  };
}

function syncBirthDate(form, { report = false } = {}) {
  const { hidden, year, month, day } = getBirthDateControls(form);
  if (!hidden || !year || !month || !day) return { complete: false, valid: false, value: '' };
  [year, month, day].forEach((select) => select.setCustomValidity(''));
  const y = Number(year.value);
  const m = Number(month.value);
  const d = Number(day.value);
  const complete = Boolean(y && m && d);
  let valid = complete;

  if (complete) {
    const candidate = new Date(y, m - 1, d);
    valid = candidate.getFullYear() === y && candidate.getMonth() === m - 1 && candidate.getDate() === d;
    const todayText = form.dataset.today || '';
    if (valid && todayText && candidate > new Date(`${todayText}T23:59:59`)) {
      valid = false;
      year.setCustomValidity('未来の生年月日は選択できません。');
    }
  }
  hidden.value = complete && valid
    ? `${String(y).padStart(4, '0')}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    : '';

  if (report && !complete) {
    const firstEmpty = [year, month, day].find((select) => !select.value) || year;
    firstEmpty.setCustomValidity('生年月日を年・月・日すべて選択してください。');
    firstEmpty.reportValidity();
  } else if (report && !valid) {
    const target = [year, month, day].find((select) => select.validationMessage) || day;
    if (!target.validationMessage) target.setCustomValidity('あなたが生まれた年月日を、もう一度確かめてください。');
    target.reportValidity();
  }
  return { complete, valid, value: hidden.value };
}

const zodiacPreviewState = new WeakMap();

function resetZodiacPreview(form) {
  const node = form.querySelector('[data-birth-zodiac]');
  if (!node) return;
  node.hidden = true;
  node.classList.remove('is-ready', 'is-reading');
  zodiacPreviewState.delete(form);
}

async function requestZodiacPreview(form, birthDate) {
  const node = form.querySelector('[data-birth-zodiac]');
  const symbol = form.querySelector('[data-zodiac-symbol]');
  const name = form.querySelector('[data-zodiac-name]');
  const english = form.querySelector('[data-zodiac-english]');
  if (!node || !symbol || !name || !english) return;
  const oldState = zodiacPreviewState.get(form);
  if (oldState?.birthDate === birthDate && oldState?.ready) return;
  oldState?.controller?.abort();
  const controller = new AbortController();
  zodiacPreviewState.set(form, { birthDate, controller, ready: false });
  node.hidden = false;
  node.classList.add('is-reading');
  node.classList.remove('is-ready');
  symbol.textContent = '✦';
  name.textContent = 'あなたの星を確かめています';
  english.textContent = 'READING THE SUN';
  try {
    const response = await fetch(`/zodiac-preview?birth_date=${encodeURIComponent(birthDate)}`, {
      headers: { Accept: 'application/json' }, signal: controller.signal,
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || '星座を読み取れませんでした。');
    if (form.querySelector('#birth_date')?.value !== birthDate) return;
    symbol.textContent = data.symbol || '✦';
    name.textContent = data.name || '太陽星座';
    english.textContent = data.english || 'SUN SIGN';
    node.classList.remove('is-reading');
    node.classList.add('is-ready');
    zodiacPreviewState.set(form, { birthDate, controller: null, ready: true });
  } catch (error) {
    if (error.name === 'AbortError') return;
    node.classList.remove('is-reading', 'is-ready');
    symbol.textContent = '☉';
    name.textContent = '星の位置を確かめられませんでした';
    english.textContent = 'TRY AGAIN';
  }
}

function updateBirthDatePreview(form) {
  const preview = form.querySelector('[data-birth-preview]');
  const dateNode = form.querySelector('[data-birth-preview-date]');
  const statusNode = form.querySelector('[data-birth-preview-status]');
  if (!preview || !dateNode || !statusNode) return;
  const result = syncBirthDate(form);
  if (result.complete && result.valid) {
    const [year, month, day] = result.value.split('-').map(Number);
    dateNode.textContent = `${year}年${month}月${day}日`;
    statusNode.textContent = 'SEALED';
    preview.classList.add('is-complete');
    requestZodiacPreview(form, result.value);
  } else {
    dateNode.textContent = '生年月日を選ぶと、ここに刻まれます';
    statusNode.textContent = 'WAITING';
    preview.classList.remove('is-complete');
    resetZodiacPreview(form);
  }
}

function selectedProduct(form) {
  return form.querySelector('input[name="product"]:checked');
}

const RITUAL_THEMES = {
  miniloto: {
    className: 'ritual-miniloto',
    kicker: 'MINI LOTO · LUNAR FIVE-LIGHT RITUAL',
    phases: [
      ['月輪の目覚め', '静かな月の円環をひらいています', '誕生の日に宿った月の光を、今夜の空へ呼び戻しています'],
      ['五つの灯', '五つの小さな星を灯しています', '一つずつ目覚める星が、あなたに近い数字を探しています'],
      ['月光の転写', '月の光をミニロトの数字へ映しています', '1から31の円環へ、五つの光を重ねています'],
      ['五光の結晶', '五つの数字が月光の中で結ばれます', 'もうすぐ、あなたのための五つの数字が姿を現します'],
    ],
  },
  loto6: {
    className: 'ritual-loto6',
    kicker: 'LOTO 6 · SIX CELESTIAL SEALS',
    phases: [
      ['星図の封印', 'あなたの誕生星図をひらいています', '二つの三角形へ、誕生の日の光を静かに刻んでいます'],
      ['六天体の交差', '六つの天体印を呼び寄せています', '星の軌道が交わる場所を、一つずつ確かめています'],
      ['六星印の共鳴', '六つの星印をロト6の数字へ映しています', '1から43の星図で、強く響く数字を結んでいます'],
      ['数字の顕現', '六つの星印が数字へ姿を変えます', '封印がほどけるまで、あとほんの少しです'],
    ],
  },
  loto7: {
    className: 'ritual-loto7',
    kicker: 'LOTO 7 · SEVEN PLANETARY ORBITS',
    phases: [
      ['七天体の起動', '七つの惑星を目覚めさせています', '太陽から土星まで、七天体の声を一つずつ呼び集めています'],
      ['大軌道の重なり', '七つの軌道を一枚の星図へ重ねています', '異なる速さで巡る星々が、今だけの配置を描いています'],
      ['七光の収束', '七つの光をロト7の数字へ収束させています', '1から37の世界で、七天体の響きが重なる地点を探しています'],
      ['大軌道の啓示', '七つの数字が星図の中心へ集まります', '最も壮大な星の儀式が、まもなく結ばれます'],
    ],
  },
  numbers3: {
    className: 'ritual-numbers3',
    kicker: 'NUMBERS 3 · THREE ASTRAL DIALS',
    phases: [
      ['星盤の起動', '三つの天体盤を目覚めさせています', '左・中央・右、それぞれの桁へ別の星の声を呼び込みます'],
      ['三光の巡行', '三つの天体印を異なる軌道で巡らせています', 'まだ数字の形を持たない光から、左・中央・右の響きを読み分けています'],
      ['星序の封印', '三つの光を正しい順序へ結んでいます', '並び順を崩さず、三桁の星列として静かに封じています'],
      ['三桁の啓示', '三つの星盤がひとつの星列へ重なります', '実際に導かれた数字は、儀式が結ばれた次の画面で初めて姿を現します'],
    ],
  },
  numbers4: {
    className: 'ritual-numbers4',
    kicker: 'NUMBERS 4 · FOUR CELESTIAL GATES',
    phases: [
      ['星門の起動', '四つの星門へ光を注いでいます', '誕生の星から今日の空へ、四本の光の道をひらいています'],
      ['四門の開扉', '四つの門を一枚ずつひらいています', '門の奥を巡る光から、四つの位置それぞれの響きを読み取っています'],
      ['星列の連結', '四つの光を順番どおりに結んでいます', '先頭の0も失わないよう、まだ形のない星列として封じています'],
      ['四桁の啓示', '四つの星門がひとつの星列へ重なります', '実際に導かれた数字は、儀式が結ばれた次の画面で初めて姿を現します'],
    ],
  },
};

const RITUAL_CLASS_NAMES = Object.values(RITUAL_THEMES).map((theme) => theme.className);

function applyRitualTheme(productId) {
  const theme = RITUAL_THEMES[productId] || RITUAL_THEMES.loto6;
  document.body.classList.remove(...RITUAL_CLASS_NAMES.map((name) => name.replace('ritual-', 'ritual-theme-')));
  document.body.classList.add(theme.className.replace('ritual-', 'ritual-theme-'));
  return theme;
}

function updateProductSummary() {
  const form = document.querySelector('form[data-generate-form]');
  if (!form) return;
  const selected = selectedProduct(form);
  const countInput = form.querySelector('#count');
  if (!selected || !countInput) return;
  const count = Math.max(1, Number(countInput.value) || 1);
  const productId = selected.value || 'loto6';
  applyRitualTheme(productId);

  const nameNode = document.getElementById('selected-product-name');
  const ruleNode = document.getElementById('selected-product-rule');
  const ritualNameNode = document.getElementById('selected-ritual-name');
  const ritualSymbolNode = document.getElementById('selected-ritual-symbol');
  const ritualDescriptionNode = document.getElementById('selected-ritual-description');
  const totalNode = document.getElementById('planned-total');
  const detailNode = document.getElementById('planned-total-detail');
  const button = form.querySelector('[data-generate-button]');

  if (nameNode) nameNode.textContent = selected.dataset.productName || '宝くじ';
  if (ruleNode) ruleNode.textContent = selected.dataset.productRule || '';
  if (ritualNameNode) ritualNameNode.textContent = selected.dataset.ritualName || '星の儀式';
  if (ritualSymbolNode) ritualSymbolNode.textContent = selected.dataset.ritualSymbol || '✦';
  if (ritualDescriptionNode) ritualDescriptionNode.textContent = selected.dataset.ritualDescription || '';
  if (totalNode) totalNode.textContent = `${count}口`;
  if (detailNode) detailNode.textContent = `${selected.dataset.ritualName || '星の儀式'}で${count}口を導く`;
  if (button) button.innerHTML = `<span aria-hidden="true">${selected.dataset.ritualSymbol || '✦'}</span> ${selected.dataset.buttonLabel || '星から数字を受け取る'}`;
}

function setupGenerateForm() {
  const form = document.querySelector('form[data-generate-form]');
  if (!form) return;
  const controls = getBirthDateControls(form);
  const selects = [controls.year, controls.month, controls.day].filter(Boolean);
  const updateDays = () => {
    const year = Number(controls.year?.value) || 2000;
    const month = Number(controls.month?.value);
    const maxDay = month ? new Date(year, month, 0).getDate() : 31;
    Array.from(controls.day?.options || []).forEach((option) => {
      if (option.value) option.disabled = Number(option.value) > maxDay;
    });
    if (Number(controls.day?.value) > maxDay) controls.day.value = '';
  };
  selects.forEach((select) => {
    select.required = true;
    select.addEventListener('change', () => {
      updateDays();
      syncBirthDate(form);
      updateBirthDatePreview(form);
    });
  });
  form.querySelectorAll('input[name="product"], #count').forEach((input) => {
    input.addEventListener('input', updateProductSummary);
    input.addEventListener('change', updateProductSummary);
  });
  form.addEventListener('submit', (event) => {
    const result = syncBirthDate(form, { report: true });
    if (!result.complete || !result.valid) event.preventDefault();
  });
  updateDays();
  syncBirthDate(form);
  updateBirthDatePreview(form);
  updateProductSummary();
}

function setupScrollTop() {
  document.querySelectorAll('[data-scroll-top]').forEach((button) => button.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' })));
}

function getContent(details) { return details.querySelector(':scope > .smooth-content'); }
function updateToggleLabel(details) {
  const label = details.querySelector(':scope > summary [data-toggle-label]');
  if (label) label.textContent = details.open ? label.dataset.openLabel : label.dataset.closedLabel;
}
function wrapDetailsContent(details) {
  const summary = details.querySelector(':scope > summary');
  if (!summary || getContent(details)) return;
  const wrapper = document.createElement('div');
  wrapper.className = 'smooth-content';
  const nodes = [];
  let node = summary.nextSibling;
  while (node) { nodes.push(node); node = node.nextSibling; }
  nodes.forEach((child) => wrapper.appendChild(child));
  details.appendChild(wrapper);
  if (details.open) { wrapper.style.height = 'auto'; wrapper.style.opacity = '1'; wrapper.style.transform = 'translateY(0)'; }
  else { wrapper.style.height = '0px'; wrapper.style.opacity = '0'; wrapper.style.transform = 'translateY(-4px)'; }
  updateToggleLabel(details);
}
function openDetails(details) {
  const content = getContent(details);
  if (!content || details.dataset.animating === '1' || details.open) return;
  if (details.classList.contains('accordion') && details.parentElement?.classList.contains('accordion-group')) {
    details.parentElement.querySelectorAll(':scope > details.accordion[open]').forEach((other) => { if (other !== details) closeDetails(other); });
  }
  details.dataset.animating = '1'; details.open = true; updateToggleLabel(details);
  content.style.height = '0px'; content.style.opacity = '0'; content.style.transform = 'translateY(-4px)';
  requestAnimationFrame(() => { void content.offsetHeight; content.style.height = `${content.scrollHeight}px`; content.style.opacity = '1'; content.style.transform = 'translateY(0)'; });
  const finish = () => { content.style.height = 'auto'; details.dataset.animating = '0'; content.removeEventListener('transitionend', finish); };
  content.addEventListener('transitionend', finish); window.setTimeout(finish, 560);
}
function closeDetails(details) {
  const content = getContent(details);
  if (!content || details.dataset.animating === '1' || !details.open) return;
  details.dataset.animating = '1'; content.style.height = `${content.scrollHeight}px`; content.style.opacity = '1'; content.style.transform = 'translateY(0)';
  requestAnimationFrame(() => { content.style.height = '0px'; content.style.opacity = '0'; content.style.transform = 'translateY(-4px)'; });
  const finish = () => { details.open = false; details.dataset.animating = '0'; updateToggleLabel(details); content.removeEventListener('transitionend', finish); };
  content.addEventListener('transitionend', finish); window.setTimeout(finish, 380);
}
function setupSmoothAccordions() {
  document.querySelectorAll('details.accordion, details.compact-ticket, details.advanced').forEach((details) => {
    wrapDetailsContent(details);
    const summary = details.querySelector(':scope > summary');
    if (!summary) return;
    summary.addEventListener('click', (event) => { event.preventDefault(); if (details.open) closeDetails(details); else openDetails(details); });
  });
}

function setupDrawAnimation() {
  const form = document.querySelector('form[data-generate-form]');
  const loader = document.getElementById('draw-loader');
  if (!form || !loader) return;

  const resetLoader = () => {
    form.dataset.submitted = '0';
    document.body.classList.remove('is-drawing');
    loader.classList.remove('is-active', 'is-final-phase');
    loader.classList.remove(...RITUAL_CLASS_NAMES);
    loader.classList.add('ritual-loto6');
    loader.setAttribute('aria-hidden', 'true');
    loader.querySelectorAll('.ritual-step-dots i').forEach((dot) => dot.classList.remove('is-active', 'is-complete'));
    const progress = loader.querySelector('[data-loader-progress]');
    if (progress) { progress.style.transitionDuration = '0ms'; progress.style.width = '0%'; }
    const button = form.querySelector('button[type="submit"]');
    if (button) button.disabled = false;
    updateProductSummary();
  };

  form.addEventListener('submit', (event) => {
    if (event.defaultPrevented || !form.checkValidity()) return;
    if (form.dataset.submitted === '1') { event.preventDefault(); return; }
    event.preventDefault();
    form.dataset.submitted = '1';

    const selected = selectedProduct(form);
    const productId = selected?.value || 'loto6';
    const productName = selected?.dataset.productName || '数字';
    const ritualName = selected?.dataset.ritualName || '星の儀式';
    const ritualSymbol = selected?.dataset.ritualSymbol || '✦';
    const theme = RITUAL_THEMES[productId] || RITUAL_THEMES.loto6;
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const configuredDuration = Number(selected?.dataset.ritualDuration) || 4400;
    const duration = reduceMotion ? 760 : configuredDuration;

    document.body.classList.add('is-drawing');
    loader.classList.remove(...RITUAL_CLASS_NAMES, 'is-final-phase');
    loader.classList.add('is-active', theme.className);
    loader.setAttribute('aria-hidden', 'false');

    const button = form.querySelector('button[type="submit"]');
    if (button) { button.disabled = true; button.innerHTML = `<span aria-hidden="true">${ritualSymbol}</span> ${ritualName}を執り行っています`; }

    const kicker = loader.querySelector('[data-loader-kicker]');
    const product = loader.querySelector('[data-loader-product]');
    const title = loader.querySelector('[data-loader-title]');
    const text = loader.querySelector('[data-loader-text]');
    const stage = loader.querySelector('[data-loader-stage]');
    const progress = loader.querySelector('[data-loader-progress]');
    const dots = Array.from(loader.querySelectorAll('.ritual-step-dots i'));
    if (kicker) kicker.textContent = theme.kicker;
    if (product) product.textContent = `${productName} · ${ritualName}`;

    const phases = theme.phases;
    const span = duration / phases.length;
    phases.forEach((phase, index) => window.setTimeout(() => {
      if (stage) stage.textContent = phase[0];
      if (title) title.textContent = phase[1];
      if (text) text.textContent = phase[2];
      dots.forEach((dot, dotIndex) => {
        dot.classList.toggle('is-active', dotIndex === index);
        dot.classList.toggle('is-complete', dotIndex < index);
      });
      loader.classList.toggle('is-final-phase', index === phases.length - 1);
    }, Math.round(index * span)));

    if (progress) {
      progress.style.transitionDuration = `${duration}ms`;
      requestAnimationFrame(() => { progress.style.width = '100%'; });
    }
    window.setTimeout(() => {
      form.submit();
    }, duration);
  });

  window.addEventListener('pageshow', resetLoader);
}


function setupResultRepeatForm() {
  const form = document.querySelector('form[data-result-repeat-form]');
  const loader = document.getElementById('draw-loader');
  if (!form || !loader) return;

  const reset = () => {
    form.dataset.submitted = '0';
    document.body.classList.remove('is-drawing');
    loader.classList.remove('is-active', 'is-final-phase', ...RITUAL_CLASS_NAMES);
    loader.classList.add('ritual-loto6');
    loader.setAttribute('aria-hidden', 'true');
    loader.querySelectorAll('.ritual-step-dots i').forEach((dot) => dot.classList.remove('is-active', 'is-complete'));
    const progress = loader.querySelector('[data-loader-progress]');
    if (progress) { progress.style.transitionDuration = '0ms'; progress.style.width = '0%'; }
    const button = form.querySelector('button[type="submit"]');
    if (button) button.disabled = false;
  };

  form.addEventListener('submit', (event) => {
    if (form.dataset.submitted === '1') { event.preventDefault(); return; }
    event.preventDefault();
    form.dataset.submitted = '1';

    const productId = form.dataset.productId || 'loto6';
    const productName = form.dataset.productName || '数字';
    const ritualName = form.dataset.ritualName || '星の儀式';
    const ritualSymbol = form.dataset.ritualSymbol || '✦';
    const theme = RITUAL_THEMES[productId] || RITUAL_THEMES.loto6;
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const configuredDuration = Number(form.dataset.ritualDuration) || 4400;
    const duration = reduceMotion ? 760 : configuredDuration;

    document.body.classList.add('is-drawing');
    loader.classList.remove(...RITUAL_CLASS_NAMES, 'is-final-phase');
    loader.classList.add('is-active', theme.className);
    loader.setAttribute('aria-hidden', 'false');

    const button = form.querySelector('button[type="submit"]');
    if (button) button.disabled = true;

    const kicker = loader.querySelector('[data-loader-kicker]');
    const product = loader.querySelector('[data-loader-product]');
    const title = loader.querySelector('[data-loader-title]');
    const text = loader.querySelector('[data-loader-text]');
    const stage = loader.querySelector('[data-loader-stage]');
    const progress = loader.querySelector('[data-loader-progress]');
    const dots = Array.from(loader.querySelectorAll('.ritual-step-dots i'));
    if (kicker) kicker.textContent = theme.kicker;
    if (product) product.textContent = `${productName} · ${ritualName}`;

    const phases = theme.phases;
    const span = duration / phases.length;
    phases.forEach((phase, index) => window.setTimeout(() => {
      if (stage) stage.textContent = phase[0];
      if (title) title.textContent = phase[1];
      if (text) text.textContent = phase[2];
      dots.forEach((dot, dotIndex) => {
        dot.classList.toggle('is-active', dotIndex === index);
        dot.classList.toggle('is-complete', dotIndex < index);
      });
      loader.classList.toggle('is-final-phase', index === phases.length - 1);
    }, Math.round(index * span)));

    if (progress) {
      progress.style.transitionDuration = `${duration}ms`;
      requestAnimationFrame(() => { progress.style.width = '100%'; });
    }
    window.setTimeout(() => HTMLFormElement.prototype.submit.call(form), duration);
  });

  window.addEventListener('pageshow', reset);
}

function setupResultNumberReveal() {
  const groups = Array.from(document.querySelectorAll('.number-reveal-group'));
  if (!groups.length) return;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  groups.forEach((group, groupIndex) => {
    const productId = group.dataset.revealProduct || 'loto6';
    const numbers = Array.from(group.querySelectorAll('.num, .digit-tile'));
    group.classList.add('is-revealing');
    numbers.forEach((number, index) => {
      let delay = groupIndex * 0.28 + index * 0.15;
      if (productId === 'loto7') delay = groupIndex * 0.25 + index * 0.19;
      if (productId === 'numbers3') delay = groupIndex * 0.22 + index * 0.28;
      if (productId === 'numbers4') delay = groupIndex * 0.22 + index * 0.22;
      number.style.setProperty('--reveal-delay', `${reduceMotion ? 0 : delay}s`);
      number.style.setProperty('--reveal-index', String(index));
    });
    requestAnimationFrame(() => group.classList.add('reveal-start'));
  });
}

window.addEventListener('DOMContentLoaded', () => {
  setupGenerateForm();
  setupScrollTop();
  setupSmoothAccordions();
  setupDrawAnimation();
  setupResultRepeatForm();
  setupResultNumberReveal();
});
