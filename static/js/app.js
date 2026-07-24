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
  const controls = getBirthDateControls(form);
  const { hidden, year, month, day } = controls;
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
    if (valid && todayText) {
      const today = new Date(`${todayText}T23:59:59`);
      if (candidate > today) {
        valid = false;
        year.setCustomValidity('未来の生年月日は選択できません。');
      }
    }
  }

  if (complete && valid) {
    hidden.value = `${String(y).padStart(4, '0')}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
  } else {
    hidden.value = '';
  }

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
  const zodiacNode = form.querySelector('[data-birth-zodiac]');
  if (!zodiacNode) return;
  zodiacNode.hidden = true;
  zodiacNode.classList.remove('is-ready', 'is-reading');
  zodiacPreviewState.delete(form);
}

async function requestZodiacPreview(form, birthDate) {
  const zodiacNode = form.querySelector('[data-birth-zodiac]');
  const symbolNode = form.querySelector('[data-zodiac-symbol]');
  const nameNode = form.querySelector('[data-zodiac-name]');
  const englishNode = form.querySelector('[data-zodiac-english]');
  if (!zodiacNode || !symbolNode || !nameNode || !englishNode) return;

  const currentState = zodiacPreviewState.get(form);
  if (currentState?.birthDate === birthDate && currentState?.ready) return;
  currentState?.controller?.abort();

  const controller = new AbortController();
  zodiacPreviewState.set(form, { birthDate, controller, ready: false });
  zodiacNode.hidden = false;
  zodiacNode.classList.add('is-reading');
  zodiacNode.classList.remove('is-ready');
  symbolNode.textContent = '✦';
  nameNode.textContent = 'あなたの星を確かめています';
  englishNode.textContent = 'READING THE SUN';

  try {
    const response = await fetch(`/zodiac-preview?birth_date=${encodeURIComponent(birthDate)}`, {
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || '星座を読み取れませんでした。');
    if (form.querySelector('#birth_date')?.value !== birthDate) return;

    symbolNode.textContent = data.symbol || '✦';
    nameNode.textContent = data.name || '太陽星座';
    englishNode.textContent = data.english || 'SUN SIGN';
    zodiacNode.classList.remove('is-reading');
    zodiacNode.classList.add('is-ready');
    zodiacPreviewState.set(form, { birthDate, controller: null, ready: true });
  } catch (error) {
    if (error.name === 'AbortError') return;
    zodiacNode.classList.remove('is-reading', 'is-ready');
    symbolNode.textContent = '☉';
    nameNode.textContent = '星の位置を確かめられませんでした';
    englishNode.textContent = 'TRY AGAIN';
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

function setupGenerateValidation() {
  const form = document.querySelector('form[data-generate-form]');
  if (!form) return;

  form.addEventListener('submit', (event) => {
    const result = syncBirthDate(form, { report: true });
    if (!result.complete || !result.valid) event.preventDefault();
  });
}

function updatePlannedTotal() {
  const form = document.querySelector('form[data-generate-form]');
  if (!form) return;
  const countInput = form.querySelector('#count');
  const selectedMode = form.querySelector('input[name="mode"]:checked');
  const totalNode = document.getElementById('planned-total');
  const detailNode = document.getElementById('planned-total-detail');
  if (!countInput || !selectedMode || !totalNode || !detailNode) return;

  const count = Math.max(1, Number(countInput.value) || 1);
  const astrologyModeCount = Number(form.dataset.modeCountAstrology || 5);
  const modeCount = selectedMode.value === 'all' ? astrologyModeCount : 1;
  const total = count * modeCount;
  totalNode.textContent = `${total}口`;
  detailNode.textContent = selectedMode.value === 'all'
    ? `各${count}口 × ${modeCount}種類 ＝ 合計${total}口`
    : `${count}口を生成`;
}

function setupAstrologyControls() {
  const form = document.querySelector('form[data-generate-form]');
  if (!form) return;
  const fields = form.querySelector('[data-astrology-fields]');
  const entry = form.querySelector('[data-astrology-entry]');
  const controls = getBirthDateControls(form);
  const selects = [controls.year, controls.month, controls.day].filter(Boolean);
  if (!fields || !controls.hidden || selects.length !== 3) return;

  const updateDayOptions = () => {
    const year = Number(controls.year.value) || 2000;
    const month = Number(controls.month.value);
    const maxDay = month ? new Date(year, month, 0).getDate() : 31;
    Array.from(controls.day.options).forEach((option) => {
      if (!option.value) return;
      option.disabled = Number(option.value) > maxDay;
    });
    if (Number(controls.day.value) > maxDay) controls.day.value = '';
  };

  const update = () => {
    fields.classList.remove('is-disabled');
    entry?.classList.add('is-oracle-active');
    selects.forEach((select) => {
      select.required = true;
      select.disabled = false;
    });
    controls.hidden.disabled = false;
    syncBirthDate(form);
    updateBirthDatePreview(form);
    updatePlannedTotal();
  };

  selects.forEach((select) => {
    select.addEventListener('change', () => {
      updateDayOptions();
      syncBirthDate(form);
      updateBirthDatePreview(form);
      update();
    });
  });
  form.querySelectorAll('input[name="mode"]').forEach((radio) => radio.addEventListener('change', update));
  updateDayOptions();
  syncBirthDate(form);
  update();
}

function setupPlannedTotal() {
  const form = document.querySelector('form[data-generate-form]');
  if (!form) return;
  form.querySelectorAll('input[name="mode"], #count').forEach((input) => {
    input.addEventListener('input', updatePlannedTotal);
    input.addEventListener('change', updatePlannedTotal);
  });
  updatePlannedTotal();
}

function setupCheckMethod() {
  const form = document.querySelector('form[data-check-form]');
  if (!form) return;

  const update = () => {
    const selected = form.querySelector('input[name="check_method"]:checked')?.value || 'draw';
    form.querySelectorAll('[data-method-panel]').forEach((panel) => {
      const active = panel.dataset.methodPanel === selected;
      panel.hidden = !active;
      panel.querySelectorAll('input').forEach((input) => {
        input.disabled = !active;
        if (active) input.setCustomValidity('');
      });
    });
  };

  form.querySelectorAll('input[name="check_method"]').forEach((radio) => {
    radio.addEventListener('change', update);
  });

  form.addEventListener('submit', (event) => {
    const selected = form.querySelector('input[name="check_method"]:checked')?.value;
    if (selected !== 'manual') return;
    const mainInputs = Array.from(form.querySelectorAll('input[name^="main_"]:not(:disabled)'));
    if (!validateUnique(mainInputs, '本数字に {number} が重複しています。')) {
      event.preventDefault();
      return;
    }
    const bonus = form.querySelector('#bonus:not(:disabled)');
    const mainValues = new Set(mainInputs.filter((input) => input.value).map((input) => Number(input.value)));
    if (bonus && bonus.value && mainValues.has(Number(bonus.value))) {
      bonus.setCustomValidity('ボーナス数字は本数字と異なる数字を入力してください。');
      bonus.reportValidity();
      event.preventDefault();
    }
  });

  update();
}

function setupScrollTop() {
  document.querySelectorAll('[data-scroll-top]').forEach((button) => {
    button.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  });
}

function getContent(details) {
  return details.querySelector(':scope > .smooth-content');
}

function updateToggleLabel(details) {
  const label = details.querySelector(':scope > summary [data-toggle-label]');
  if (!label) return;
  label.textContent = details.open ? label.dataset.openLabel : label.dataset.closedLabel;
}

function wrapDetailsContent(details) {
  const summary = details.querySelector(':scope > summary');
  if (!summary || getContent(details)) return;

  const wrapper = document.createElement('div');
  wrapper.className = 'smooth-content';

  const nodes = [];
  let node = summary.nextSibling;
  while (node) {
    nodes.push(node);
    node = node.nextSibling;
  }
  nodes.forEach((child) => wrapper.appendChild(child));
  details.appendChild(wrapper);

  if (details.open) {
    wrapper.style.height = 'auto';
    wrapper.style.opacity = '1';
    wrapper.style.transform = 'translateY(0)';
  } else {
    wrapper.style.height = '0px';
    wrapper.style.opacity = '0';
    wrapper.style.transform = 'translateY(-4px)';
  }
  updateToggleLabel(details);
}

function openDetails(details) {
  const content = getContent(details);
  if (!content || details.dataset.animating === '1' || details.open) return;

  if (details.classList.contains('accordion') && details.parentElement?.classList.contains('accordion-group')) {
    details.parentElement.querySelectorAll(':scope > details.accordion[open]').forEach((other) => {
      if (other !== details) closeDetails(other);
    });
  }

  details.dataset.animating = '1';
  details.open = true;
  updateToggleLabel(details);
  content.style.height = '0px';
  content.style.opacity = '0';
  content.style.transform = 'translateY(-4px)';

  requestAnimationFrame(() => {
    void content.offsetHeight;
    content.style.height = `${content.scrollHeight}px`;
    content.style.opacity = '1';
    content.style.transform = 'translateY(0)';
  });

  let finished = false;
  const finish = () => {
    if (finished) return;
    finished = true;
    content.style.height = 'auto';
    details.dataset.animating = '0';
    content.removeEventListener('transitionend', finish);
  };
  content.addEventListener('transitionend', finish);
  window.setTimeout(finish, 560);
}

function closeDetails(details) {
  const content = getContent(details);
  if (!content || details.dataset.animating === '1' || !details.open) return;

  details.dataset.animating = '1';
  content.style.height = `${content.scrollHeight}px`;
  content.style.opacity = '1';
  content.style.transform = 'translateY(0)';

  requestAnimationFrame(() => {
    content.style.height = '0px';
    content.style.opacity = '0';
    content.style.transform = 'translateY(-4px)';
  });

  let finished = false;
  const finish = () => {
    if (finished) return;
    finished = true;
    details.open = false;
    details.dataset.animating = '0';
    updateToggleLabel(details);
    content.removeEventListener('transitionend', finish);
  };
  content.addEventListener('transitionend', finish);
  window.setTimeout(finish, 380);
}

function setupSmoothAccordions() {
  const selector = 'details.accordion, details.compact-ticket, details.advanced';
  document.querySelectorAll(selector).forEach((details) => {
    wrapDetailsContent(details);
    const summary = details.querySelector(':scope > summary');
    if (!summary) return;

    summary.addEventListener('click', (event) => {
      event.preventDefault();
      if (details.open) closeDetails(details);
      else openDetails(details);
    });
  });
}

function setupDrawAnimation() {
  const form = document.querySelector('form[data-generate-form]');
  const loader = document.getElementById('draw-loader');
  if (!form || !loader) return;

  form.addEventListener('submit', (event) => {
    if (event.defaultPrevented || !form.checkValidity()) return;
    if (form.dataset.submitted === '1') {
      event.preventDefault();
      return;
    }
    event.preventDefault();
    form.dataset.submitted = '1';
    document.body.classList.add('is-drawing');
    loader.classList.add('is-active');
    loader.setAttribute('aria-hidden', 'false');

    const button = form.querySelector('button[type="submit"]');
    if (button) {
      button.disabled = true;
      button.innerHTML = '<span aria-hidden="true">☾</span> 星の声に耳を澄ませています';
    }

    const loaderTitle = loader.querySelector('[data-loader-title]');
    const loaderText = loader.querySelector('[data-loader-text]');
    const loaderStage = loader.querySelector('[data-loader-stage]');
    const loaderProgress = loader.querySelector('[data-loader-progress]');
    const loaderCore = loader.querySelector('[data-loader-core]');
    const seals = Array.from(loader.querySelectorAll('[data-ritual-seal]'));
    const astrologyEnabled = true;
    const phases = astrologyEnabled
      ? [
          ['誕生の光', 'あなたが生まれた日の星をひらいています', '星空に刻まれた、あなたの最初の光をたどっています'],
          ['今日の空', '今この時の天体を重ねています', '七つの星が交わす、今日だけのささやきを読み取っています'],
          ['数字の記憶', 'これまでの数字の流れに耳を澄ませています', '過去から続く数字の気配を、星の円環へそっと重ねています'],
          ['星からの便り', 'あなたへ届ける六つの数字を結んでいます', '五つの導きをひとつに束ねています。あと少しだけお待ちください'],
        ]
      : [
          ['第一の円環', '数字の記憶をたどっています', '過去の出現傾向と数字構成を読み取っています'],
          ['第二の円環', '四つの読み方を重ねています', '異なる数字の流れを一つの円環へ集めています'],
          ['最終の啓示', '六つの数字へ結んでいます', '今回の候補を静かに整えています'],
        ];

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const totalDuration = reduceMotion ? 700 : 4400;
    const phaseSpan = totalDuration / phases.length;
    phases.forEach((phase, index) => {
      window.setTimeout(() => {
        if (loaderStage) loaderStage.textContent = phase[0];
        if (loaderTitle) loaderTitle.textContent = phase[1];
        if (loaderText) loaderText.textContent = phase[2];
        if (loaderCore) loaderCore.textContent = index === phases.length - 1 ? '6' : '✦';
        loader.classList.toggle('is-final-phase', index === phases.length - 1);
      }, Math.round(index * phaseSpan));
    });

    seals.forEach((seal, index) => {
      const lightAt = reduceMotion ? 80 + index * 70 : 650 + index * 520;
      window.setTimeout(() => seal.classList.add('is-lit'), lightAt);
    });
    if (loaderProgress) {
      loaderProgress.style.transitionDuration = `${totalDuration}ms`;
      requestAnimationFrame(() => { loaderProgress.style.width = '100%'; });
    }

    window.setTimeout(() => form.submit(), totalDuration);
  });

  window.addEventListener('pageshow', () => {
    form.dataset.submitted = '0';
    document.body.classList.remove('is-drawing');
    loader.classList.remove('is-active', 'is-final-phase');
    loader.setAttribute('aria-hidden', 'true');
    loader.querySelectorAll('[data-ritual-seal]').forEach((seal) => seal.classList.remove('is-lit'));
    const progress = loader.querySelector('[data-loader-progress]');
    if (progress) {
      progress.style.transitionDuration = '0ms';
      progress.style.width = '0%';
    }
    const button = form.querySelector('button[type="submit"]');
    if (button) {
      button.disabled = false;
      button.innerHTML = '<span aria-hidden="true">✦</span> 星からの数字を受け取る';
    }
  });
}

function setupResultNumberReveal() {
  const groups = Array.from(document.querySelectorAll('.number-reveal-group'));
  if (!groups.length) return;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  groups.forEach((group, groupIndex) => {
    const numbers = Array.from(group.querySelectorAll('.num'));
    group.classList.add('is-revealing');
    numbers.forEach((number, index) => {
      number.style.setProperty('--reveal-delay', `${reduceMotion ? 0 : groupIndex * 0.35 + index * 0.16}s`);
    });
    requestAnimationFrame(() => group.classList.add('reveal-start'));
  });
}

window.addEventListener('DOMContentLoaded', () => {
  setupGenerateValidation();
  setupAstrologyControls();
  setupPlannedTotal();
  setupCheckMethod();
  setupScrollTop();
  setupSmoothAccordions();
  setupDrawAnimation();
  setupResultNumberReveal();
});
