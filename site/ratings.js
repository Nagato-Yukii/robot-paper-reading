'use strict';
(async () => {
  const prefix = 'robot-paper-reading.rating.v1.';
  const status = document.getElementById('rating-status');
  const groups = [...document.querySelectorAll('.stars')].map(element => ({
    element, paper: element.dataset.paper, metric: element.dataset.metric,
    buttons: [...element.querySelectorAll('.star')], selected: 0
  }));
  const render = group => {
    for (const button of group.buttons) {
      const value = Number(button.dataset.value);
      const lit = value <= group.selected;
      button.classList.toggle('lit', lit);
      button.textContent = lit ? '★' : '☆';
      button.setAttribute('aria-pressed', String(value === group.selected));
    }
  };
  const disable = (group, disabled) => group.buttons.forEach(button => { button.disabled = disabled; });
  const request = async (path, method = 'GET', body) => {
    const response = await fetch(path, {
      method, cache: 'no-store',
      headers: body ? { 'Content-Type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined
    });
    if (!response.ok) throw new Error('评分服务未响应');
    return response.json();
  };
  groups.forEach(group => disable(group, true));
  status.textContent = '正在读取数据库评分…';
  let data;
  try {
    data = await request('/api/ratings');
    const legacy = [];
    for (const group of groups) {
      try {
        const value = Number(localStorage.getItem(prefix + group.paper + '.' + group.metric));
        if (Number.isInteger(value) && value >= 1 && value <= 5) {
          legacy.push({ paper: group.paper, metric: group.metric, value });
        }
      } catch { /* Database editing remains available without browser storage. */ }
    }
    if (legacy.length) {
      data = await request('/api/ratings/import', 'POST', { ratings: legacy });
      for (const entry of legacy) {
        try { localStorage.removeItem(prefix + entry.paper + '.' + entry.metric); } catch { /* Safe to retry next time. */ }
      }
    }
    if (!data.ratings || typeof data.ratings !== 'object') throw new Error('评分数据格式错误');
    for (const group of groups) {
      const value = data.ratings[group.paper]?.[group.metric];
      group.selected = Number.isInteger(value) && value >= 0 && value <= 5 ? value : 0;
      render(group);
      disable(group, false);
    }
    status.textContent = legacy.length ? '原有本地评分已迁入数据库，可直接点击星星修改。' : '已连接数据库，可直接点击星星修改。';
  } catch {
    status.textContent = '无法连接评分数据库。请使用本机评分服务打开页面，然后刷新重试；原有评分未删除。';
    return;
  }
  let pending = 0;
  let saveFailed = false;
  for (const group of groups) {
    for (const button of group.buttons) {
      button.addEventListener('click', async () => {
        const previous = group.selected;
        const value = Number(button.dataset.value);
        group.selected = group.selected === value ? 0 : value;
        render(group);
        disable(group, true);
        pending += 1;
        status.textContent = '正在保存到数据库…';
        try {
          const result = await request('/api/ratings', 'PUT', {
            paper: group.paper, metric: group.metric, value: group.selected
          });
          if (!result.saved) throw new Error('评分未保存');
        } catch {
          group.selected = previous;
          render(group);
          saveFailed = true;
        } finally {
          pending -= 1;
          disable(group, false);
          if (pending === 0) {
            status.textContent = saveFailed ? '有评分保存失败，已恢复原分数，请重新点击评分。' : '已保存到数据库';
            saveFailed = false;
          }
        }
      });
    }
  }
})();
