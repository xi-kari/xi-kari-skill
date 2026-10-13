(() => {
  'use strict';
  const root = document.documentElement;
  const article = document.getElementById('document');
  const search = document.getElementById('reader-search');
  const status = document.getElementById('search-status');
  const previous = document.getElementById('previous-match');
  const next = document.getElementById('next-match');
  const navToggle = document.getElementById('nav-toggle');
  const themeToggle = document.getElementById('theme-toggle');
  const sizes = ['small', 'medium', 'large', 'largest'];
  let matches = [], active = -1, timer, lastQuery = '';
  function saved(name, value) {
    try {
      if (value !== undefined) localStorage.setItem('xikari-reader-' + name, value);
      else return localStorage.getItem('xikari-reader-' + name);
    } catch (_) { /* File readers may disable local storage. */ }
    return null;
  }
  function theme(value) {
    root.dataset.theme = value === 'night' ? 'night' : 'paper';
    themeToggle.setAttribute('aria-pressed', String(root.dataset.theme === 'night'));
    themeToggle.textContent = root.dataset.theme === 'night' ? '日读' : '夜读';
  }
  function font(value) {
    root.dataset.font = sizes.includes(value) ? value : 'medium';
    const index = sizes.indexOf(root.dataset.font);
    document.getElementById('font-smaller').disabled = index === 0;
    document.getElementById('font-larger').disabled = index === sizes.length - 1;
  }
  theme(saved('theme')); font(saved('font'));
  themeToggle.addEventListener('click', () => {
    theme(root.dataset.theme === 'night' ? 'paper' : 'night'); saved('theme', root.dataset.theme);
  });
  for (const [id, step] of [['font-smaller', -1], ['font-larger', 1]]) {
    document.getElementById(id).addEventListener('click', () => {
      font(sizes[Math.max(0, Math.min(sizes.length - 1, sizes.indexOf(root.dataset.font) + step))]);
      saved('font', root.dataset.font);
    });
  }
  document.getElementById('print-reader').addEventListener('click', () => window.print());
  function nav(open) {
    document.body.classList.toggle('nav-open', open);
    navToggle.setAttribute('aria-expanded', String(open));
  }
  navToggle.addEventListener('click', () => nav(!document.body.classList.contains('nav-open')));
  document.querySelectorAll('#contents a[href^="#"], .reader-footer a').forEach(link => {
    link.addEventListener('click', () => {
      const destination = document.getElementById(link.hash.slice(1));
      nav(false);
      if (destination) destination.focus({ preventScroll: true });
    });
  });
  function clearMarks() {
    article.querySelectorAll('mark[data-match]').forEach(mark => mark.replaceWith(document.createTextNode(mark.textContent)));
    article.normalize(); matches = []; active = -1;
  }
  function select(index, scroll = true) {
    article.querySelectorAll('.current-match').forEach(mark => mark.classList.remove('current-match'));
    if (!matches.length) return;
    active = (index + matches.length) % matches.length;
    const pieces = article.querySelectorAll(`mark[data-match="${active}"]`);
    pieces.forEach(mark => mark.classList.add('current-match'));
    status.textContent = `${active + 1} / ${matches.length} 处`;
    if (scroll && pieces.length) pieces[0].scrollIntoView({ block: 'center', behavior: 'auto' });
  }
  function find() {
    clearMarks();
    const query = search.value.trim();
    lastQuery = query;
    previous.disabled = next.disabled = true;
    if (!query) { status.textContent = '保留全部正文'; return; }
    const walker = document.createTreeWalker(article, NodeFilter.SHOW_TEXT);
    const nodes = []; let text = '', node;
    while ((node = walker.nextNode())) {
      nodes.push({ node, start: text.length, end: text.length + node.data.length });
      text += node.data;
    }
    const pattern = new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'giu');
    let hit;
    while ((hit = pattern.exec(text)) !== null) {
      matches.push({ start: hit.index, end: hit.index + hit[0].length });
    }
    if (!matches.length) { status.textContent = '未找到，可换词'; return; }
    let first = 0;
    nodes.forEach(entry => {
      while (first < matches.length && matches[first].end <= entry.start) first++;
      const fragment = document.createDocumentFragment(); let cursor = 0, touched = false;
      for (let i = first; i < matches.length && matches[i].start < entry.end; i++) {
        const start = Math.max(0, matches[i].start - entry.start);
        const end = Math.min(entry.node.data.length, matches[i].end - entry.start);
        fragment.append(document.createTextNode(entry.node.data.slice(cursor, start)));
        const mark = document.createElement('mark'); mark.dataset.match = String(i);
        mark.textContent = entry.node.data.slice(start, end); fragment.append(mark);
        cursor = end; touched = true;
      }
      if (touched) {
        fragment.append(document.createTextNode(entry.node.data.slice(cursor)));
        entry.node.replaceWith(fragment);
      }
    });
    previous.disabled = next.disabled = false; select(0);
  }
  search.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(find, 160); });
  search.addEventListener('keydown', event => {
    if (event.key === 'Enter') {
      event.preventDefault(); clearTimeout(timer);
      if (!matches.length || lastQuery !== search.value.trim()) find(); else select(active + (event.shiftKey ? -1 : 1));
    }
    if (event.key === 'Escape') { search.value = ''; clearTimeout(timer); find(); }
  });
  previous.addEventListener('click', () => select(active - 1));
  next.addEventListener('click', () => select(active + 1));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && document.body.classList.contains('nav-open')) {
      nav(false); navToggle.focus();
    }
    if (event.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
      event.preventDefault(); search.focus();
    }
  });
  const headingLinks = new Map([...document.querySelectorAll('#contents nav a')].map(link => [link.hash.slice(1), link]));
  const headings = [...article.querySelectorAll('[id]')];
  let scrollPending = false;
  function updateCurrent() {
    scrollPending = false;
    const top = document.querySelector('.reader-toolbar').getBoundingClientRect().height + 48;
    let activeHeading = headings[0];
    for (const heading of headings) {
      if (heading.getBoundingClientRect().top <= top) activeHeading = heading;
    }
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 8) activeHeading = headings.at(-1);
    headingLinks.forEach(link => link.removeAttribute('aria-current'));
    const current = activeHeading && headingLinks.get(activeHeading.id);
    if (current) current.setAttribute('aria-current', 'location');
  }
  window.addEventListener('scroll', () => {
    if (!scrollPending) { scrollPending = true; requestAnimationFrame(updateCurrent); }
  }, { passive: true });
  updateCurrent();
})();
