/* Persistent reading highlights. Ranges paint text without changing paper markup. */
(function () {
  'use strict';
  function initialize() {
  const root = document.querySelector('main') || document.querySelector('.grid');
  if (!root) return;
  const page = root.matches('main')
    ? new URL('.', location.href).pathname.split('/').filter(Boolean).pop()
    : 'library';
  const key = 'rpr-highlights:v1:' + page;
  const online = location.protocol === 'http:' || location.protocol === 'https:';
  const supported = !!(window.CSS && CSS.highlights && window.Highlight);
  let state = {marks: [], pending: [], deleted: []};
  let syncing = false;
  try {
    const saved = JSON.parse(localStorage.getItem(key));
    if (saved && Array.isArray(saved.marks) && Array.isArray(saved.pending) && Array.isArray(saved.deleted)) state = saved;
  } catch (_) { /* Reading still works when browser storage is unavailable. */ }
  const valid = m => m && typeof m.id === 'string' && /^[\da-f-]{36}$/i.test(m.id)
    && Number.isInteger(m.start) && Number.isInteger(m.end) && m.start >= 0 && m.end > m.start
    && typeof m.quote === 'string' && m.quote.length === m.end - m.start
    && typeof m.prefix === 'string' && typeof m.suffix === 'string';
  state.marks = state.marks.filter(valid);
  state.pending = state.pending.filter(valid);
  state.deleted = state.deleted.filter(id => typeof id === 'string' && /^[\da-f-]{36}$/i.test(id));

  const style = document.createElement('style');
  style.textContent = `
    ::highlight(paper-notes){background-color:#fff0a6;color:inherit}
    main ::selection,.grid ::selection{background-color:#fff0a6;color:inherit}
    .highlight-tools{position:fixed;bottom:16px;right:18px;z-index:70;display:flex;gap:12px;align-items:center;
      max-width:calc(100vw - 36px);padding:9px 12px;border:1px solid #e2ddd3;border-radius:10px;
      background:#fffefbf5;box-shadow:0 2px 12px #0000000b;font:12px/1.5 system-ui,sans-serif;color:#5d636b}
    .highlight-tools button{border:0;background:transparent;color:#5952a6;cursor:pointer;white-space:nowrap;font:inherit}
    .highlight-tools button:disabled{color:#999;cursor:default}
    @media print{.highlight-tools{display:none}}
  `;
  document.head.append(style);
  const toolbar = document.createElement('div');
  toolbar.className = 'highlight-tools';
  const status = document.createElement('span');
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  const undo = document.createElement('button');
  undo.type = 'button';
  undo.textContent = '撤销上一处';
  toolbar.append(status, undo);
  document.body.append(toolbar);

  function message(text) { status.textContent = text; }
  function cache() {
    try { localStorage.setItem(key, JSON.stringify(state)); } catch (_) { /* The database can still save. */ }
  }
  function documentText() {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    let node;
    while ((node = walker.nextNode())) nodes.push(node);
    return {nodes, text: nodes.map(n => n.data).join('')};
  }
  function locate(mark, text) {
    if (text.slice(mark.start, mark.end) === mark.quote) return mark.start;
    // A changed paragraph earlier in the document must not move a saved highlight to unrelated text.
    const candidates = [];
    const exact = [];
    let start = text.indexOf(mark.quote);
    while (start !== -1) {
      exact.push(start);
      if ((!mark.prefix || text.slice(Math.max(0, start - mark.prefix.length), start) === mark.prefix)
          && (!mark.suffix || text.slice(start + mark.quote.length, start + mark.quote.length + mark.suffix.length) === mark.suffix)) candidates.push(start);
      start = text.indexOf(mark.quote, start + 1);
    }
    if (candidates.length === 1) return candidates[0];
    // Restoring nearby math changes context and offsets, but a long unique
    // quotation still identifies the same passage without rewriting user data.
    return exact.length === 1 && mark.quote.trim().length >= 8 ? exact[0] : null;
  }
  function rangeAt(nodes, start, end) {
    let offset = 0;
    const range = document.createRange();
    let started = false;
    for (const node of nodes) {
      const next = offset + node.length;
      if (!started && start < next) { range.setStart(node, start - offset); started = true; }
      if (started && end <= next) { range.setEnd(node, end - offset); return range; }
      offset = next;
    }
    return null;
  }
  function paint() {
    undo.disabled = !state.marks.length;
    if (!supported) return;
    const {nodes, text} = documentText();
    const ranges = state.marks.map(m => {
      const start = locate(m, text);
      return start === null ? null : rangeAt(nodes, start, start + m.quote.length);
    }).filter(Boolean);
    CSS.highlights.set('paper-notes', new Highlight(...ranges));
  }
  async function api(method, data) {
    const url = '/api/highlights' + (method === 'GET' ? '?page=' + encodeURIComponent(page) : '');
    const response = await fetch(url, {method, headers: {'Content-Type': 'application/json'},
      ...(method === 'GET' ? {} : {body: JSON.stringify({...data, page})})});
    if (!response.ok) throw new Error('Highlight request failed');
    return response.json();
  }
  async function flush() {
    if (!online || syncing) return;
    syncing = true;
    try {
      while (state.pending.length) {
        const mark = state.pending[0];
        await api('POST', mark);
        state.pending = state.pending.filter(m => m.id !== mark.id);
        cache();
      }
      while (state.deleted.length) {
        const id = state.deleted[0];
        await api('DELETE', {id});
        state.deleted = state.deleted.filter(value => value !== id);
        cache();
      }
      message('划词高亮 · 已保存到数据库');
    } catch (_) {
      message('划词高亮 · 暂存当前浏览器，数据库未同步');
    } finally { syncing = false; }
  }
  function capture() {
    if (!supported) return;
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || selection.rangeCount !== 1) return;
    const range = selection.getRangeAt(0);
    if (!root.contains(range.startContainer) || !root.contains(range.endContainer)) return;
    const quote = range.toString();
    if (!quote.trim() || quote.length > 20000) return;
    const before = document.createRange();
    before.selectNodeContents(root);
    before.setEnd(range.startContainer, range.startOffset);
    const start = before.toString().length;
    const end = start + quote.length;
    const {text} = documentText();
    if (text.slice(start, end) !== quote || state.marks.some(m => m.start === start && m.end === end && m.quote === quote)) return;
    const mark = {id: crypto.randomUUID(), start, end, quote,
      prefix: Array.from(text.slice(0, start)).slice(-20).join(''), suffix: Array.from(text.slice(end)).slice(0, 20).join('')};
    state.marks.push(mark);
    state.pending.push(mark);
    cache();
    paint();
    message(online ? '划词高亮 · 正在保存…' : '划词高亮 · 已保存在当前浏览器');
    flush();
  }
  root.addEventListener('pointerup', () => setTimeout(capture, 0));
  undo.addEventListener('click', () => {
    const mark = state.marks.pop();
    window.getSelection()?.removeAllRanges();
    if (!mark) return;
    state.pending = state.pending.filter(m => m.id !== mark.id);
    state.deleted.push(mark.id);
    cache();
    paint();
    message(online ? '已撤销高亮 · 正在保存…' : '已撤销高亮');
    flush();
  });
  paint();
  message(supported ? '拖选文字即可淡黄高亮' : '此浏览器不支持保存文字高亮');
  if (online) api('GET').then(data => {
    const deleted = new Set(state.deleted);
    const marks = new Map(data.highlights.filter(valid).map(m => [m.id, m]));
    state.pending.forEach(m => marks.set(m.id, m));
    state.marks = [...marks.values()].filter(m => !deleted.has(m.id));
    cache();
    paint();
    message('拖选文字即可高亮 · 已连接数据库');
    if (state.pending.length || state.deleted.length) flush();
  }).catch(() => message('划词高亮 · 当前浏览器保存，数据库暂不可用'));
  }
  if (document.readyState === 'complete') initialize();
  else document.addEventListener('DOMContentLoaded', initialize, {once: true});
})();
