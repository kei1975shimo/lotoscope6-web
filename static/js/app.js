document.addEventListener('touchstart', function () {}, { passive: true });

function getBirthDateControls(form) {
  return {
    hidden: form.querySelector('#birth_date'),
    year: form.querySelector('#birth_year'),
    month: form.querySelector('#birth_month'),
    day: form.querySelector('#birth_day'),
  };
}

function selectedProduct(form) {
  return form.querySelector('input[name="product"]:checked');
}

function selectedDivination(form) {
  return form.querySelector('input[name="divination"]:checked');
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
    if (!target.validationMessage) target.setCustomValidity('生年月日をもう一度確かめてください。');
    target.reportValidity();
  }
  return { complete, valid, value: hidden.value };
}

const previewState = new WeakMap();

function resetDivinationPreview(form) {
  const preview = form.querySelector('[data-divination-preview]');
  if (preview) preview.hidden = true;
  previewState.delete(form);
}

function renderDivinationPreview(form, data) {
  const preview = form.querySelector('[data-divination-preview]');
  if (!preview) return;
  const items = Array.isArray(data.summary_items) ? data.summary_items.slice(0, 3) : [];
  preview.querySelectorAll('[data-preview-item]').forEach((node, index) => {
    const item = items[index] || {};
    const small = node.querySelector('small');
    const strong = node.querySelector('strong');
    const span = node.querySelector('span');
    if (small) small.textContent = item.label || 'READING';
    if (strong) strong.textContent = item.value || '—';
    if (span) span.textContent = item.detail || '';
  });
  preview.hidden = false;
}

async function requestDivinationPreview(form, birthDate) {
  const selected = selectedDivination(form);
  if (!selected || !birthDate) return;
  const divinationId = selected.value || 'astrology';
  const key = `${divinationId}:${birthDate}`;
  const oldState = previewState.get(form);
  if (oldState?.key === key && oldState?.ready) return;
  oldState?.controller?.abort();

  const controller = new AbortController();
  previewState.set(form, { key, controller, ready: false });
  const preview = form.querySelector('[data-divination-preview]');
  if (preview) preview.hidden = false;
  try {
    const response = await fetch(`/divination-preview?divination=${encodeURIComponent(divinationId)}&birth_date=${encodeURIComponent(birthDate)}`, {
      headers: { Accept: 'application/json' }, signal: controller.signal,
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || '占いを読み取れませんでした。');
    if (form.querySelector('#birth_date')?.value !== birthDate || selectedDivination(form)?.value !== divinationId) return;
    renderDivinationPreview(form, data);
    previewState.set(form, { key, controller: null, ready: true });
  } catch (error) {
    if (error.name === 'AbortError') return;
    resetDivinationPreview(form);
  }
}

function updateBirthDatePreview(form) {
  const preview = form.querySelector('[data-birth-preview]');
  const statusNode = form.querySelector('[data-birth-preview-status]');
  const methodName = form.querySelector('[data-preview-method-name]');
  const methodSymbol = form.querySelector('[data-preview-method-symbol]');
  const divination = selectedDivination(form);
  if (!preview || !statusNode) return;

  if (methodName) methodName.textContent = divination?.dataset.divinationEnglish || 'DIVINATION PROFILE';
  if (methodSymbol) methodSymbol.textContent = divination?.dataset.divinationSymbol || '✦';

  const result = syncBirthDate(form);
  if (result.complete && result.valid) {
    statusNode.textContent = 'READY';
    preview.classList.add('is-complete');
    requestDivinationPreview(form, result.value);
  } else {
    statusNode.textContent = 'WAITING';
    preview.classList.remove('is-complete');
    resetDivinationPreview(form);
  }
}

const PRODUCT_RITUAL_CLASSES = ['ritual-miniloto', 'ritual-loto6', 'ritual-loto7', 'ritual-numbers3', 'ritual-numbers4'];
const DIVINATION_RITUAL_CLASSES = ['divination-astrology', 'divination-kabbalah', 'divination-tarot'];
const RITUAL_PHASE_CLASSES = ['ritual-phase-0', 'ritual-phase-1', 'ritual-phase-2', 'ritual-phase-3'];

function applyRitualTheme(productId) {
  const safeId = ['miniloto', 'loto6', 'loto7', 'numbers3', 'numbers4'].includes(productId) ? productId : 'loto6';
  document.body.classList.remove(...PRODUCT_RITUAL_CLASSES.map((name) => name.replace('ritual-', 'ritual-theme-')));
  document.body.classList.add(`ritual-theme-${safeId}`);
}

const DIVINATION_RITUALS = {
  astrology: {
    kicker: 'ASTROLOGY · CELESTIAL READING',
    phases: [
      ['誕生星の照合', '生まれた日の星を読み取っています', '太陽・月・惑星の位置を、今日の空と重ねています'],
      ['七天体の共鳴', '天体同士の響きを確かめています', '主要アスペクトへ近い配置ほど、数字への重みを強めています'],
      ['数字への転写', '星の響きをくじの数字へ変換しています', '選んだ券種の範囲に合わせ、中心数字と周辺候補を整えています'],
      ['星読みの結晶', '数字の組み合わせを結んでいます', '星の重みと数字のバランスから、候補がまもなく現れます'],
    ],
  },
  kabbalah: {
    kicker: 'KABBALAH NUMEROLOGY · NUMBER READING',
    phases: [
      ['誕生日の還元', '生年月日を基礎数へ還元しています', '生命数・誕生日数・態度数を一つずつ導いています'],
      ['周期数の照合', '今日へつながる数の周期を読んでいます', 'パーソナルイヤーと月の数を、誕生日の基礎数へ重ねています'],
      ['数の展開', '数秘の基礎数をくじの範囲へ展開しています', 'マスターナンバーを含む強い数から、候補の重みを作っています'],
      ['数秘の結晶', '数字の組み合わせを結んでいます', '数秘の響きと数字のバランスから、候補がまもなく現れます'],
    ],
  },
  tarot: {
    kicker: 'TAROT · MAJOR ARCANA READING',
    phases: [
      ['大アルカナを開く', '誕生日に対応するカードを開いています', '22枚の大アルカナから、誕生カードと魂のカードを導いています'],
      ['今日のカード', '生成日のカードを重ねています', '誕生カードと今日の数を結び、今の流れを示すカードを開いています'],
      ['カード番号の転写', 'アルカナの数字をくじへ映しています', 'カード番号とその組み合わせを、選んだ券種の数字範囲へ展開しています'],
      ['アルカナの結晶', 'カードの導きを数字へ結んでいます', '大アルカナの重みと数字のバランスから、候補がまもなく現れます'],
    ],
  },
};

function swapRitualCopy(copyZone, nodes, phase, reduceMotion, firstPhase = false) {
  const [stage, title, text] = nodes;
  const applyCopy = () => {
    if (stage) stage.textContent = phase[0];
    if (title) title.textContent = phase[1];
    if (text) text.textContent = phase[2];
  };
  if (!copyZone || reduceMotion) {
    applyCopy();
    return;
  }

  // Animate the fixed-height copy zone as one surface. This avoids forced
  // reflow and keeps the visual stage moving continuously behind the text.
  if (copyZone.getAnimations) copyZone.getAnimations().forEach((animation) => animation.cancel());
  if (firstPhase) {
    applyCopy();
    copyZone.animate(
      [{ opacity: 0.58, transform: 'translateY(3px)' }, { opacity: 1, transform: 'translateY(0)' }],
      { duration: 320, easing: 'cubic-bezier(.2,.75,.2,1)', fill: 'both' },
    );
    return;
  }

  const fadeOut = copyZone.animate(
    [{ opacity: 1, transform: 'translateY(0)' }, { opacity: 0.16, transform: 'translateY(-3px)' }],
    { duration: 135, easing: 'ease-in', fill: 'forwards' },
  );
  fadeOut.onfinish = () => {
    applyCopy();
    copyZone.animate(
      [{ opacity: 0.16, transform: 'translateY(3px)' }, { opacity: 1, transform: 'translateY(0)' }],
      { duration: 285, easing: 'cubic-bezier(.16,.82,.24,1)', fill: 'both' },
    );
  };
}

function runRitual({ loader, productId, productName, divinationId, divinationName, divinationSymbol, ritualDuration, onButtonStart, onComplete }) {
  const ritual = DIVINATION_RITUALS[divinationId] || DIVINATION_RITUALS.astrology;
  const productClass = `ritual-${productId || 'loto6'}`;
  const safeDivinationId = ['astrology', 'kabbalah', 'tarot'].includes(divinationId) ? divinationId : 'astrology';
  const divinationClass = `divination-${safeDivinationId}`;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const configuredDuration = Number(ritualDuration) || 4400;
  const duration = reduceMotion ? 900 : configuredDuration;

  document.body.classList.add('is-drawing');
  loader.classList.remove(...PRODUCT_RITUAL_CLASSES, ...DIVINATION_RITUAL_CLASSES, ...RITUAL_PHASE_CLASSES, 'is-final-phase');
  loader.classList.add('is-active', productClass, divinationClass, 'ritual-phase-0');
  loader.setAttribute('aria-hidden', 'false');
  if (onButtonStart) onButtonStart();

  const kicker = loader.querySelector('[data-loader-kicker]');
  const product = loader.querySelector('[data-loader-product]');
  const title = loader.querySelector('[data-loader-title]');
  const text = loader.querySelector('[data-loader-text]');
  const stage = loader.querySelector('[data-loader-stage]');
  const progress = loader.querySelector('[data-loader-progress]');
  const dots = Array.from(loader.querySelectorAll('.ritual-step-dots i'));
  if (kicker) kicker.textContent = ritual.kicker;
  if (product) product.textContent = `${productName} × ${divinationName}`;

  const copyZone = loader.querySelector('.ritual-copy-zone');
  const span = duration / ritual.phases.length;
  const timers = ritual.phases.map((phase, index) => window.setTimeout(() => {
    swapRitualCopy(copyZone, [stage, title, text], phase, reduceMotion, index === 0);

    loader.classList.remove(...RITUAL_PHASE_CLASSES);
    loader.classList.add(`ritual-phase-${index}`);
    dots.forEach((dot, dotIndex) => {
      dot.classList.toggle('is-active', dotIndex === index);
      dot.classList.toggle('is-complete', dotIndex < index);
    });
    loader.classList.toggle('is-final-phase', index === ritual.phases.length - 1);
  }, Math.round(index * span)));

  if (progress) {
    progress.style.transitionDuration = `${duration}ms`;
    requestAnimationFrame(() => { progress.style.width = '100%'; });
  }

  let done = false;
  const finish = () => {
    if (done) return;
    done = true;
    timers.forEach((id) => window.clearTimeout(id));
    window.clearTimeout(completeTimer);
    onComplete();
  };
  const completeTimer = window.setTimeout(finish, duration);
}

function resetRitualLoader(loader) {
  document.body.classList.remove('is-drawing');
  loader.classList.remove('is-active', 'is-final-phase', ...PRODUCT_RITUAL_CLASSES, ...DIVINATION_RITUAL_CLASSES, ...RITUAL_PHASE_CLASSES);
  loader.classList.add('ritual-loto6');
  loader.setAttribute('aria-hidden', 'true');
  loader.querySelectorAll('.ritual-step-dots i').forEach((dot) => dot.classList.remove('is-active', 'is-complete'));
  const progress = loader.querySelector('[data-loader-progress]');
  if (progress) { progress.style.transitionDuration = '0ms'; progress.style.width = '0%'; }
}

function updateSelectionSummary() {
  const form = document.querySelector('form[data-generate-form]');
  if (!form) return;
  const product = selectedProduct(form);
  const divination = selectedDivination(form);
  const countInput = form.querySelector('#count');
  if (!product || !divination || !countInput) return;

  const count = Math.max(1, Number(countInput.value) || 1);
  applyRitualTheme(product.value || 'loto6');
  const divName = divination.dataset.divinationName || '占い';
  const divSymbol = divination.dataset.divinationSymbol || '✦';
  const buttonLabel = '本日の数字を開く';

  const divNameNode = document.getElementById('selected-divination-name');
  const productNameNode = document.getElementById('selected-product-name');
  const totalNode = document.getElementById('planned-total');
  const descriptionNode = form.querySelector('[data-divination-description]');
  const button = form.querySelector('[data-generate-button]');
  if (divNameNode) divNameNode.textContent = divName;
  if (productNameNode) productNameNode.textContent = product.dataset.productName || '宝くじ';
  if (totalNode) totalNode.textContent = `${count}口`;
  if (descriptionNode) descriptionNode.textContent = divination.dataset.divinationDescription || '';
  if (button) button.innerHTML = `<span aria-hidden="true">${divSymbol}</span> ${buttonLabel}`;
  updateBirthDatePreview(form);
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
  form.querySelectorAll('input[name="product"], input[name="divination"], #count').forEach((input) => {
    input.addEventListener('input', updateSelectionSummary);
    input.addEventListener('change', updateSelectionSummary);
  });
  form.addEventListener('submit', (event) => {
    const result = syncBirthDate(form, { report: true });
    if (!result.complete || !result.valid) event.preventDefault();
  });

  updateDays();
  syncBirthDate(form);
  updateSelectionSummary();
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
    resetRitualLoader(loader);
    const button = form.querySelector('button[type="submit"]');
    if (button) button.disabled = false;
    updateSelectionSummary();
  };

  form.addEventListener('submit', (event) => {
    if (event.defaultPrevented || !form.checkValidity()) return;
    if (form.dataset.submitted === '1') { event.preventDefault(); return; }
    event.preventDefault();
    form.dataset.submitted = '1';

    const product = selectedProduct(form);
    const divination = selectedDivination(form);
    const button = form.querySelector('button[type="submit"]');
    const productId = product?.value || 'loto6';
    const productName = product?.dataset.productName || '数字';
    const divinationId = divination?.value || 'astrology';
    const divinationName = divination?.dataset.divinationName || '占い';
    const divinationSymbol = divination?.dataset.divinationSymbol || '✦';

    runRitual({
      loader, productId, productName, divinationId, divinationName, divinationSymbol,
      ritualDuration: product?.dataset.ritualDuration,
      onButtonStart: () => { if (button) { button.disabled = true; button.innerHTML = `<span aria-hidden="true">${divinationSymbol}</span> 本日の導きを読み解いています`; } },
      onComplete: () => form.submit(),
    });
  });

  window.addEventListener('pageshow', resetLoader);
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
  setupResultNumberReveal();
});
