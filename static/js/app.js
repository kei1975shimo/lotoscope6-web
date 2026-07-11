document.addEventListener('touchstart', function () {}, { passive: true });

function numberInputsWithin(group) {
  return Array.from(group.querySelectorAll('.num-box'));
}

function limitNumberInputs() {
  document.querySelectorAll('[data-number-group]').forEach((group) => {
    const inputs = numberInputsWithin(group);
    inputs.forEach((input, index) => {
      input.addEventListener('input', () => {
        input.setCustomValidity('');
        const digits = String(input.value).replace(/[^0-9]/g, '').slice(0, 2);
        input.value = digits;
        const n = Number(digits);
        if (n > 43) input.value = '43';
        if (input.value.length >= 2 && inputs[index + 1] && !inputs[index + 1].value) {
          inputs[index + 1].focus();
        }
      });
    });
  });
}

function clearCustomValidity(inputs) {
  inputs.forEach((input) => input.setCustomValidity(''));
}

function validateUnique(inputs, message) {
  clearCustomValidity(inputs);
  const seen = new Map();
  for (const input of inputs) {
    if (!input.value) continue;
    const value = Number(input.value);
    if (seen.has(value)) {
      input.setCustomValidity(message.replace('{number}', String(value)));
      input.reportValidity();
      return false;
    }
    seen.set(value, input);
  }
  return true;
}

function setupGenerateValidation() {
  const form = document.querySelector('form[data-generate-form]');
  if (!form) return;

  form.addEventListener('submit', (event) => {
    const favorites = Array.from(form.querySelectorAll('input[name^="favorite_"]'));
    const avoided = Array.from(form.querySelectorAll('input[name^="avoid_"]'));
    if (!validateUnique(favorites, '好きな数字に {number} が重複しています。')) {
      event.preventDefault();
      return;
    }
    if (!validateUnique(avoided, '避けたい数字に {number} が重複しています。')) {
      event.preventDefault();
      return;
    }

    const favoriteValues = new Set(favorites.filter((input) => input.value).map((input) => Number(input.value)));
    clearCustomValidity(avoided);
    const overlap = avoided.find((input) => input.value && favoriteValues.has(Number(input.value)));
    if (overlap) {
      overlap.setCustomValidity(`数字 ${overlap.value} は「好きな数字」と「避けたい数字」の両方には指定できません。`);
      overlap.reportValidity();
      event.preventDefault();
    }
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
  const modeCount = selectedMode.value === 'all' ? Number(form.dataset.modeCount || 5) : 1;
  const total = count * modeCount;
  totalNode.textContent = `${total}口`;
  detailNode.textContent = selectedMode.value === 'all'
    ? `各${count}口 × ${modeCount}種類 ＝ 合計${total}口`
    : `${count}口を生成`;
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
      button.textContent = '買い目を作成しています…';
    }

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    window.setTimeout(() => form.submit(), reduceMotion ? 0 : 700);
  });

  window.addEventListener('pageshow', () => {
    form.dataset.submitted = '0';
    document.body.classList.remove('is-drawing');
    loader.classList.remove('is-active');
    loader.setAttribute('aria-hidden', 'true');
    const button = form.querySelector('button[type="submit"]');
    if (button) {
      button.disabled = false;
      button.textContent = '買い目候補を作成する';
    }
  });
}

window.addEventListener('DOMContentLoaded', () => {
  limitNumberInputs();
  setupGenerateValidation();
  setupPlannedTotal();
  setupCheckMethod();
  setupScrollTop();
  setupSmoothAccordions();
  setupDrawAnimation();
});
