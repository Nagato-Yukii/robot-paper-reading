'use strict';
(async () => {
  const fields = [...document.querySelectorAll('.user-comment')].map(input => ({
    input, paper: input.dataset.paper, saved: '', dirty: false, saving: false, composing: false, timer: null,
    status: document.getElementById(input.getAttribute('aria-describedby')),
    retry: input.parentElement.querySelector('.comment-retry'),
    key: 'rpr-comment-draft:v1:' + input.dataset.paper
  }));
  let ready = false;
  const request = async (method = 'GET', body, keepalive = false) => {
    const response = await fetch('/api/comments', {method, cache: 'no-store', keepalive,
      headers: body ? {'Content-Type': 'application/json'} : {},
      body: body ? JSON.stringify(body) : undefined});
    if (!response.ok) throw new Error('Comment service unavailable');
    return response.json();
  };
  const draft = field => {
    try { localStorage.setItem(field.key, JSON.stringify({text: field.input.value})); } catch (_) {}
  };
  const clearDraft = field => {
    try { localStorage.removeItem(field.key); } catch (_) {}
  };
  const report = (field, text, failed = false) => {
    field.status.textContent = text;
    field.retry.hidden = !failed;
  };
  async function save(field, keepalive = false) {
    clearTimeout(field.timer);
    if (!ready || !field.dirty || field.saving || field.composing) return;
    if (field.input.value === field.saved) {
      field.dirty = false;
      clearDraft(field);
      report(field, field.saved ? '已保存到数据库' : '未填写');
      return;
    }
    field.saving = true;
    try {
      while (field.input.value !== field.saved && !field.composing) {
        const text = field.input.value;
        report(field, '正在保存…');
        const result = await request('PUT', {paper: field.paper, text}, keepalive);
        if (!result.saved) throw new Error('Comment not saved');
        field.saved = text;
      }
      if (field.input.value === field.saved) {
        field.dirty = false;
        clearDraft(field);
        report(field, field.saved ? '已保存到数据库' : '未填写');
      }
    } catch (_) {
      draft(field);
      report(field, '尚未保存，内容已暂存在此浏览器', true);
    } finally { field.saving = false; }
  }
  for (const field of fields) {
    try {
      const stored = JSON.parse(localStorage.getItem(field.key));
      if (stored && typeof stored.text === 'string' && stored.text.length <= 5000) {
        field.input.value = stored.text;
        field.dirty = true;
      }
    } catch (_) {}
    field.input.addEventListener('input', event => {
      field.dirty = true;
      draft(field);
      clearTimeout(field.timer);
      report(field, '尚未保存');
      if (!event.isComposing && !field.composing) field.timer = setTimeout(() => save(field), 600);
    });
    field.input.addEventListener('compositionstart', () => { field.composing = true; clearTimeout(field.timer); });
    field.input.addEventListener('compositionend', () => {
      field.composing = false;
      draft(field);
      field.timer = setTimeout(() => save(field), 600);
    });
    field.input.addEventListener('blur', () => save(field));
    field.retry.addEventListener('click', () => save(field));
  }
  try {
    const data = await request();
    if (!data.comments || typeof data.comments !== 'object') throw new Error('Invalid comments');
    ready = true;
    for (const field of fields) {
      field.saved = typeof data.comments[field.paper] === 'string' ? data.comments[field.paper] : '';
      if (field.dirty) {
        if (field.input.value !== field.saved) save(field);
        else { field.dirty = false; clearDraft(field); report(field, field.saved ? '已保存到数据库' : '未填写'); }
      } else {
        field.input.value = field.saved;
        report(field, field.saved ? '已保存到数据库' : '未填写');
      }
    }
  } catch (_) {
    ready = true;
    fields.forEach(field => report(field, '数据库未连接，可先填写，稍后重试保存', true));
  }
  addEventListener('pagehide', () => fields.forEach(field => {
    if (field.input.value !== field.saved) { draft(field); save(field, true); }
  }));
})();
