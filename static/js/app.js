// iOS Safari は :active 疑似クラスがタッチだけでは発火しないことがあるため、
// 空の touchstart リスナーを登録してボタン等のタップフィードバックを有効化する。
document.addEventListener('touchstart', function () {}, { passive: true });

function limitNumberInputs() {
  document.querySelectorAll('.num-box').forEach((input, index, inputs) => {
    input.addEventListener('input', () => {
      input.value = input.value.replace(/[^0-9]/g, '').slice(0, 2);
      const n = Number(input.value);
      if (n > 43) input.value = '43';
      if (input.value.length >= 2 && inputs[index + 1]) inputs[index + 1].focus();
    });
  });
}

function setupScrollTop() {
  document.querySelectorAll('[data-scroll-top]').forEach((button) => {
    button.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  });
}

function getContent(details) {
  return details.querySelector(':scope > .smooth-content');
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
  details.classList.add('is-opening');
  details.classList.remove('is-closing');

  content.style.height = '0px';
  content.style.opacity = '0';
  content.style.transform = 'translateY(-4px)';

  requestAnimationFrame(() => {
    // Force the browser to commit the collapsed state before expanding.
    // This prevents the opening animation from snapping open on some mobile browsers.
    void content.offsetHeight;
    const targetHeight = content.scrollHeight;
    content.style.height = `${targetHeight}px`;
    content.style.opacity = '1';
    content.style.transform = 'translateY(0)';
  });

  const finish = () => {
    content.style.height = 'auto';
    details.dataset.animating = '0';
    details.classList.remove('is-opening');
    content.removeEventListener('transitionend', finish);
  };
  content.addEventListener('transitionend', finish);
  setTimeout(finish, 950);
}

function closeDetails(details) {
  const content = getContent(details);
  if (!content || details.dataset.animating === '1' || !details.open) return;

  details.dataset.animating = '1';
  details.classList.add('is-closing');
  details.classList.remove('is-opening');

  content.style.height = `${content.scrollHeight}px`;
  content.style.opacity = '1';
  content.style.transform = 'translateY(0)';

  requestAnimationFrame(() => {
    content.style.height = '0px';
    content.style.opacity = '0';
    content.style.transform = 'translateY(-4px)';
  });

  const finish = () => {
    details.open = false;
    details.dataset.animating = '0';
    details.classList.remove('is-closing');
    content.removeEventListener('transitionend', finish);
  };
  content.addEventListener('transitionend', finish);
  setTimeout(finish, 520);
}

function setupSmoothAccordions() {
  const selector = 'details.accordion, details.compact-ticket, details.advanced';
  document.querySelectorAll(selector).forEach((details) => {
    wrapDetailsContent(details);
    const summary = details.querySelector(':scope > summary');
    if (!summary) return;

    summary.addEventListener('click', (event) => {
      event.preventDefault();
      if (details.open) {
        closeDetails(details);
      } else {
        openDetails(details);
      }
    });
  });
}



function setupDrawAnimation() {
  const form = document.querySelector('form[data-generate-form]');
  const loader = document.getElementById('draw-loader');
  if (!form || !loader) return;

  form.addEventListener('submit', (event) => {
    if (form.dataset.submitted === '1') return;
    event.preventDefault();
    form.dataset.submitted = '1';
    document.body.classList.add('is-drawing');
    loader.classList.add('is-active');
    loader.setAttribute('aria-hidden', 'false');

    const button = form.querySelector('button[type="submit"]');
    if (button) {
      button.disabled = true;
      button.textContent = '数字をスコープ中...';
    }

    window.setTimeout(() => {
      form.submit();
    }, 3000);
  });
}

window.addEventListener('DOMContentLoaded', () => {
  limitNumberInputs();
  setupScrollTop();
  setupSmoothAccordions();
  setupDrawAnimation();
});
