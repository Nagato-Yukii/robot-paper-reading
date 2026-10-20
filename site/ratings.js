'use strict';
(() => {
  const prefix = 'robot-paper-reading.rating.v1.';
  const status = document.getElementById('rating-status');
  for (const group of document.querySelectorAll('.stars')) {
    const key = prefix + group.dataset.paper + '.' + group.dataset.metric;
    const buttons = [...group.querySelectorAll('.star')];
    let selected = 0;
    const render = () => {
      for (const button of buttons) {
        const value = Number(button.dataset.value);
        const lit = value <= selected;
        button.classList.toggle('lit', lit);
        button.textContent = lit ? '★' : '☆';
        button.setAttribute('aria-pressed', String(value === selected));
      }
    };
    try {
      const stored = Number(localStorage.getItem(key));
      if (Number.isInteger(stored) && stored >= 1 && stored <= 5) selected = stored;
    } catch {
      status.textContent = '当前浏览器无法保存评分，关闭页面后本次评分会丢失。';
    }
    render();
    for (const button of buttons) {
      button.addEventListener('click', () => {
        const value = Number(button.dataset.value);
        selected = selected === value ? 0 : value;
        render();
        try {
          if (selected) localStorage.setItem(key, String(selected));
          else localStorage.removeItem(key);
        } catch {
          status.textContent = '当前浏览器无法保存评分，关闭页面后本次评分会丢失。';
        }
      });
    }
  }
})();
