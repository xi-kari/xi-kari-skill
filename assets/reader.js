(() => {
  'use strict';
  const root = document.documentElement;
  const article = document.getElementById('document');
  const toolbar = document.querySelector('.reader-toolbar');
  const sidebar = document.getElementById('contents');
  const search = document.getElementById('reader-search');
  const searchControl = search.closest('.search-control') || search.parentElement;
  const status = document.getElementById('search-status');
  const previous = document.getElementById('previous-match');
  const next = document.getElementById('next-match');
  const navToggle = document.getElementById('nav-toggle');
  const scrim = document.getElementById('nav-scrim');
  const themeToggle = document.getElementById('theme-toggle');
  const progressBar = document.getElementById('reader-progress-bar');
  const sectionLabel = document.getElementById('toolbar-section');
  const searchToggle = document.getElementById('search-toggle');
  const searchClose = document.getElementById('search-close');
  const toolsToggle = document.getElementById('tools-toggle');
  const sections = [...article.querySelectorAll('[data-reader-section]')];
  const sizes = ['small', 'medium', 'large', 'largest'];
  const media = query => (typeof window.matchMedia === 'function' ? window.matchMedia(query) : null);

  function updateToolbarHeight() {
    const height = Math.ceil(toolbar.getBoundingClientRect().height);
    if (height > 0) root.style.setProperty('--toolbar-height', `${height}px`);
  }
  if (window.ResizeObserver) new ResizeObserver(updateToolbarHeight).observe(toolbar);
  window.addEventListener('resize', updateToolbarHeight, { passive: true });
  updateToolbarHeight();

  /* Formulas: render with the bundled KaTeX; keep the original source when it fails. */
  article.querySelectorAll('.reader-math').forEach(element => {
    if (!window.katex) return;
    const display = document.createElement('span');
    display.className = 'math-rendered';
    try {
      window.katex.render(element.dataset.tex, display, {
        displayMode: element.dataset.display === 'true', throwOnError: true,
        trust: false, strict: 'warn', maxExpand: 1000, maxSize: 20,
        output: 'htmlAndMathml', macros: {}
      });
      if (display.querySelector('.katex-error')) {
        element.classList.add('math-error');
        element.setAttribute('title', '公式未能排版，保留原式');
      } else {
        element.append(display);
        element.querySelector('.math-source').hidden = true;
        element.dataset.mathRendered = 'true';
      }
    } catch (_) {
      element.classList.add('math-error');
      element.setAttribute('title', '公式未能排版，保留原式');
    }
  });

  /* Follow-up questions quote the reader's own selection with its location. */
  const questionButton = document.getElementById('quote-question');
  const questionLabel = questionButton.querySelector('.button-label');
  const questionPanel = document.getElementById('question-panel');
  const questionText = document.getElementById('question-text');
  const questionStatus = document.getElementById('question-status');
  const sectionSelect = document.getElementById('question-section');
  const copyQuestion = document.getElementById('copy-question');
  const bubble = document.getElementById('selection-question');
  let selectedPassage = null, bubbleTimer;
  function elementAt(node) { return node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement; }
  function sectionAt(node) {
    const element = elementAt(node);
    const note = element?.closest('.footnotes');
    if (note) return element.closest('.footnotes li[id]') || note;
    return sections.filter(section => section === node || section.contains(node) || (section.compareDocumentPosition(node) & Node.DOCUMENT_POSITION_FOLLOWING)).at(-1);
  }
  function passageText(node) {
    if (node.nodeType === Node.TEXT_NODE) return node.data;
    if (node.nodeType === Node.ELEMENT_NODE) {
      if (node.matches('.reader-math')) return node.dataset.mathSource;
      if (node.matches('.footnote-ref')) return node.dataset.footnoteSource;
      if (node.matches('.footnote-backref, .legacy-anchor, .footnote-returns')) return '';
      if (node.tagName === 'BR') return '\n';
      if (node.tagName === 'TD' || node.tagName === 'TH') return [...node.childNodes].map(passageText).join('') + '\t';
    }
    const value = [...node.childNodes].map(passageText).join('');
    return value + (node.nodeType === Node.ELEMENT_NODE && /^(P|DIV|LI|TR|H[1-6]|BLOCKQUOTE|PRE|FIGCAPTION)$/.test(node.tagName) ? '\n' : '');
  }
  function passageFromRange(original) {
    const range = original.cloneRange();
    let expanded = false;
    for (const boundary of ['start', 'end']) {
      const container = boundary === 'start' ? range.startContainer : range.endContainer;
      const special = elementAt(container)?.closest('.reader-math, .footnote-ref');
      if (special) {
        if (boundary === 'start') range.setStartBefore(special); else range.setEndAfter(special);
        expanded = true;
      }
    }
    const start = range.startContainer.nodeType === Node.ELEMENT_NODE ? range.startContainer.childNodes[range.startOffset] || range.startContainer : range.startContainer;
    const end = range.endContainer.nodeType === Node.ELEMENT_NODE ? range.endContainer.childNodes[Math.max(0, range.endOffset - 1)] || range.endContainer : range.endContainer;
    const first = sectionAt(start), last = sectionAt(end);
    const quote = passageText(range.cloneContents()).trim();
    const relevant = first ? (last && last !== first ? [first, last] : [first]) : (last ? [last] : []);
    return { quote, sections: relevant.map(section => ({ title: section.dataset.sectionTitle, id: section.id })), expanded };
  }
  function articleRange() {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !selection.rangeCount) return null;
    const range = selection.getRangeAt(0);
    return article.contains(range.startContainer) && article.contains(range.endContainer) ? range : null;
  }
  function hideBubble() { clearTimeout(bubbleTimer); if (bubble) bubble.hidden = true; }
  function placeBubble() {
    if (!bubble) return;
    try {
      const range = articleRange();
      if (!range || typeof range.getClientRects !== 'function' || !questionPanel.hidden) { bubble.hidden = true; return; }
      const rects = [...range.getClientRects()].filter(rect => rect.width > 0 && rect.height > 0);
      if (!rects.length) { bubble.hidden = true; return; }
      bubble.hidden = false;
      const width = bubble.offsetWidth || 104, height = bubble.offsetHeight || 34;
      const coarse = media('(pointer: coarse)')?.matches;
      const firstLine = rects[0], lastLine = rects.at(-1);
      const topLimit = toolbar.getBoundingClientRect().bottom + 8;
      let top = coarse ? lastLine.bottom + 12 : firstLine.top - height - 10;
      let left = coarse ? lastLine.right - width / 2 : firstLine.left + Math.min(firstLine.width, 360) / 2 - width / 2;
      if (top < topLimit) top = lastLine.bottom + 12;
      left = Math.max(8, Math.min(left, document.documentElement.clientWidth - width - 8));
      bubble.style.left = `${Math.round(left + window.scrollX)}px`;
      bubble.style.top = `${Math.round(top + window.scrollY)}px`;
    } catch (_) {
      bubble.hidden = true;
    }
  }
  document.addEventListener('selectionchange', () => {
    const range = articleRange();
    if (!range) {
      const selection = window.getSelection();
      if (!selection || selection.isCollapsed) hideBubble();
      return;
    }
    const passage = passageFromRange(range);
    if (passage.quote) {
      selectedPassage = passage;
      if (questionLabel) questionLabel.textContent = '追问选段';
      clearTimeout(bubbleTimer);
      bubbleTimer = setTimeout(placeBubble, 160);
    }
  });
  function fillQuestion(passage) {
    const location = passage.sections.length ? passage.sections.map(section => `${section.title}（#${section.id}）`).join(' → ') : '开篇（#document）';
    questionText.value = `作品：《${document.title}》\n章节位置：${location}\n\n原文选段：\n${passage.quote}\n\n我的追问：\n请围绕这段原文继续展开，说明依据、适用条件和可能改变判断的材料。`;
    copyQuestion.disabled = false;
    questionStatus.textContent = passage.expanded ? '已包含完整公式或脚注标记，可修改追问后复制。' : '原文已放入，可修改追问后复制。';
  }
  function openQuestion() {
    hideBubble();
    setTools(false);
    questionPanel.hidden = false;
    questionButton.setAttribute('aria-expanded', 'true');
    if (selectedPassage) fillQuestion(selectedPassage);
    questionText.focus({ preventScroll: true });
  }
  function closeQuestion() {
    questionPanel.hidden = true;
    questionButton.setAttribute('aria-expanded', 'false');
    questionButton.focus();
  }
  questionButton.addEventListener('click', openQuestion);
  if (bubble) {
    bubble.addEventListener('mousedown', event => event.preventDefault());
    bubble.addEventListener('click', openQuestion);
  }
  document.getElementById('close-question').addEventListener('click', closeQuestion);
  sectionSelect.addEventListener('change', () => { document.getElementById('quote-section').disabled = !sectionSelect.value; });
  document.getElementById('quote-section').addEventListener('click', () => {
    const section = document.getElementById(sectionSelect.value);
    if (!section) return;
    const position = sections.indexOf(section);
    const nextSection = sections.slice(position + 1).find(item => Number(item.dataset.readerSection) <= Number(section.dataset.readerSection));
    const range = document.createRange();
    range.setStartBefore(section);
    if (nextSection) range.setEndBefore(nextSection); else range.setEnd(article, article.childNodes.length);
    fillQuestion(passageFromRange(range)); questionText.focus();
  });
  questionText.addEventListener('input', () => { copyQuestion.disabled = !questionText.value.trim(); });
  copyQuestion.addEventListener('click', async () => {
    if (!questionText.value.trim()) return;
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(questionText.value);
      questionStatus.textContent = '已复制，可粘贴到你的对话中。';
    } catch (_) {
      questionText.focus(); questionText.select();
      questionStatus.textContent = '浏览器未允许自动复制，文本已选中，请按 Ctrl+C 或使用复制菜单。';
    }
  });

  /* Reading preferences stay in this browser only. */
  function saved(name, value) {
    try {
      if (value !== undefined) localStorage.setItem('xikari-reader-' + name, value);
      else return localStorage.getItem('xikari-reader-' + name);
    } catch (_) { /* File readers may disable local storage. */ }
    return null;
  }
  const systemDark = media('(prefers-color-scheme: dark)');
  function theme(value) {
    root.dataset.theme = value === 'night' ? 'night' : 'paper';
    const night = root.dataset.theme === 'night';
    themeToggle.setAttribute('aria-pressed', String(night));
    themeToggle.title = night ? '切换到日间阅读' : '切换到夜间阅读';
  }
  function font(value) {
    root.dataset.font = sizes.includes(value) ? value : 'medium';
    const index = sizes.indexOf(root.dataset.font);
    document.getElementById('font-smaller').disabled = index === 0;
    document.getElementById('font-larger').disabled = index === sizes.length - 1;
  }
  theme(saved('theme') || (systemDark?.matches ? 'night' : 'paper'));
  font(saved('font'));
  systemDark?.addEventListener?.('change', event => { if (!saved('theme')) theme(event.matches ? 'night' : 'paper'); });
  themeToggle.addEventListener('click', () => {
    theme(root.dataset.theme === 'night' ? 'paper' : 'night'); saved('theme', root.dataset.theme);
  });
  for (const [id, step] of [['font-smaller', -1], ['font-larger', 1]]) {
    document.getElementById(id).addEventListener('click', () => {
      font(sizes[Math.max(0, Math.min(sizes.length - 1, sizes.indexOf(root.dataset.font) + step))]);
      saved('font', root.dataset.font);
    });
  }
  document.getElementById('print-reader').addEventListener('click', () => { setTools(false); window.print(); });

  /* Contents drawer on narrow screens; tool menu and search overlay on phones. */
  function nav(open) {
    document.body.classList.toggle('nav-open', open);
    navToggle.setAttribute('aria-expanded', String(open));
    navToggle.setAttribute('aria-label', open ? '收起目录' : '打开目录');
    if (scrim) scrim.hidden = !open;
  }
  function setTools(open) {
    if (!toolsToggle) return;
    toolbar.classList.toggle('tools-open', open);
    toolsToggle.setAttribute('aria-expanded', String(open));
  }
  function setSearching(open) {
    toolbar.classList.toggle('searching', open);
    if (searchToggle) searchToggle.setAttribute('aria-expanded', String(open));
  }
  navToggle.addEventListener('click', () => nav(!document.body.classList.contains('nav-open')));
  scrim?.addEventListener('click', () => nav(false));
  toolsToggle?.addEventListener('click', () => setTools(!toolbar.classList.contains('tools-open')));
  searchToggle?.addEventListener('click', () => { setTools(false); setSearching(true); search.focus(); });
  searchClose?.addEventListener('click', () => {
    search.value = ''; clearTimeout(timer); find(); setSearching(false); searchToggle?.focus();
  });
  document.addEventListener('click', event => {
    if (toolbar.classList.contains('tools-open') && !event.target.closest('#reading-controls, #tools-toggle')) setTools(false);
  });
  document.querySelectorAll('#contents a[href^="#"], .reader-footer a, .footnote-ref a, .footnote-backref').forEach(link => {
    link.addEventListener('click', () => {
      const destination = document.getElementById(link.hash.slice(1));
      nav(false);
      hidePreview();
      if (destination) destination.focus({ preventScroll: true });
    });
  });

  /* Search highlights in place; unmatched text is never hidden. */
  let matches = [], active = -1, timer, lastQuery = '';
  function clearMarks() {
    article.querySelectorAll('mark[data-match]').forEach(mark => mark.replaceWith(document.createTextNode(mark.textContent)));
    article.querySelectorAll('[data-math-match]').forEach(element => {
      element.removeAttribute('data-math-match'); element.classList.remove('math-match', 'current-match');
    });
    article.normalize(); matches = []; active = -1;
  }
  function select(index, scroll = true) {
    article.querySelectorAll('.current-match').forEach(mark => mark.classList.remove('current-match'));
    if (!matches.length) return;
    active = (index + matches.length) % matches.length;
    const pieces = article.querySelectorAll(`mark[data-match="${active}"], [data-math-match~="${active}"]`);
    pieces.forEach(mark => mark.classList.add('current-match'));
    status.textContent = `${active + 1} / ${matches.length}`;
    if (scroll && pieces.length) pieces[0].scrollIntoView({ block: 'center', behavior: 'auto' });
  }
  function find() {
    clearMarks();
    const query = search.value.trim();
    lastQuery = query;
    previous.disabled = next.disabled = true;
    searchControl.classList.toggle('has-query', Boolean(query));
    if (!query) { status.textContent = ''; return; }
    const walker = document.createTreeWalker(article, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
    const nodes = []; let text = '', node;
    while ((node = walker.nextNode())) {
      const math = node.nodeType === Node.ELEMENT_NODE && node.matches('.reader-math');
      if (!math && (node.nodeType !== Node.TEXT_NODE || node.parentElement.closest('.reader-math'))) continue;
      const value = math ? node.dataset.mathSource : node.data;
      nodes.push({ node, math, start: text.length, end: text.length + value.length });
      text += value;
    }
    const pattern = new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'giu');
    let hit;
    while ((hit = pattern.exec(text)) !== null) {
      matches.push({ start: hit.index, end: hit.index + hit[0].length });
    }
    if (!matches.length) { status.textContent = '没有匹配'; return; }
    let first = 0;
    nodes.forEach(entry => {
      while (first < matches.length && matches[first].end <= entry.start) first++;
      if (entry.math) {
        const positions = [];
        for (let i = first; i < matches.length && matches[i].start < entry.end; i++) positions.push(i);
        if (positions.length) {
          entry.node.dataset.mathMatch = positions.join(' '); entry.node.classList.add('math-match');
        }
        return;
      }
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
    if (event.key === 'Escape') {
      event.stopPropagation();
      search.value = ''; clearTimeout(timer); find();
      if (toolbar.classList.contains('searching')) { setSearching(false); searchToggle?.focus(); }
    }
  });
  previous.addEventListener('click', () => select(active - 1));
  next.addEventListener('click', () => select(active + 1));

  /* Footnote preview: read the note where it is cited; the link still jumps to the full note. */
  const preview = document.createElement('div');
  preview.className = 'footnote-preview'; preview.id = 'footnote-preview';
  preview.setAttribute('role', 'tooltip'); preview.hidden = true;
  document.body.append(preview);
  let previewTimer;
  function hidePreview() { clearTimeout(previewTimer); preview.hidden = true; }
  function showPreview(link) {
    const note = document.getElementById(link.hash.slice(1));
    if (!note) return;
    const copy = note.cloneNode(true);
    copy.querySelectorAll('.footnote-returns, .footnote-unused').forEach(item => item.remove());
    copy.querySelectorAll('[id]').forEach(item => item.removeAttribute('id'));
    const label = document.createElement('span');
    label.className = 'preview-label'; label.textContent = `脚注 ${link.textContent.trim()}`;
    preview.replaceChildren(label, ...copy.childNodes);
    preview.hidden = false;
    try {
      const rect = link.getBoundingClientRect();
      const width = preview.offsetWidth, height = preview.offsetHeight;
      let top = rect.top - height - 10;
      if (top < toolbar.getBoundingClientRect().bottom + 8) top = rect.bottom + 10;
      const left = Math.max(12, Math.min(rect.left + rect.width / 2 - width / 2, document.documentElement.clientWidth - width - 12));
      preview.style.left = `${Math.round(left + window.scrollX)}px`;
      preview.style.top = `${Math.round(top + window.scrollY)}px`;
    } catch (_) {
      preview.hidden = true;
    }
  }
  const hover = media('(hover: hover)');
  article.querySelectorAll('.footnote-ref a').forEach(link => {
    link.addEventListener('mouseenter', () => {
      if (hover && !hover.matches) return;
      clearTimeout(previewTimer); previewTimer = setTimeout(() => showPreview(link), 220);
    });
    link.addEventListener('mouseleave', hidePreview);
    link.addEventListener('focus', () => { clearTimeout(previewTimer); previewTimer = setTimeout(() => showPreview(link), 120); });
    link.addEventListener('blur', hidePreview);
  });

  document.addEventListener('keydown', event => {
    const typing = ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName) || document.activeElement.isContentEditable;
    if (event.key === 'Escape') {
      if (!preview.hidden) { hidePreview(); return; }
      if (toolbar.classList.contains('tools-open')) { setTools(false); toolsToggle?.focus(); return; }
      if (bubble && !bubble.hidden) { hideBubble(); return; }
      if (!questionPanel.hidden && questionPanel.contains(document.activeElement)) { closeQuestion(); return; }
      if (document.body.classList.contains('nav-open')) { nav(false); navToggle.focus(); }
    }
    if (event.key === '/' && !typing) {
      event.preventDefault();
      if (searchToggle && getComputedStyle(searchToggle).display !== 'none') setSearching(true);
      search.focus();
    }
  });

  /* Current chapter, progress line and contents position follow the scroll. */
  const headingLinks = new Map([...document.querySelectorAll('#contents nav a')].map(link => [link.hash.slice(1), link]));
  const headings = sections;
  const titleHeading = article.querySelector('h1');
  function alignLegacyAnchor() {
    const anchor = document.getElementById(window.location.hash.slice(1));
    if (!anchor?.classList.contains('legacy-anchor')) return;
    const heading = anchor.nextElementSibling;
    if (heading?.matches('[data-reader-section]')) heading.scrollIntoView({ block: 'start', behavior: 'auto' });
  }
  window.addEventListener('hashchange', alignLegacyAnchor);
  window.addEventListener('load', alignLegacyAnchor);
  function keepVisible(link) {
    if (!sidebar || sidebar.scrollHeight <= sidebar.clientHeight + 2 || document.body.classList.contains('nav-open')) return;
    const box = sidebar.getBoundingClientRect(), item = link.getBoundingClientRect();
    if (!box.height) return;
    if (item.top < box.top + 56 || item.bottom > box.bottom - 120) sidebar.scrollTop += item.top - box.top - box.height / 3;
  }
  let scrollPending = false, currentId = '';
  function updateCurrent() {
    scrollPending = false;
    const toolbarHeight = toolbar.getBoundingClientRect().height;
    const top = toolbarHeight + 48;
    let activeHeading = headings[0];
    for (const heading of headings) {
      if (heading.getBoundingClientRect().top <= top) activeHeading = heading;
    }
    const reachedEnd = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 8;
    if (reachedEnd) activeHeading = headings.at(-1);
    headingLinks.forEach(link => link.removeAttribute('aria-current'));
    const current = activeHeading && headingLinks.get(activeHeading.id);
    if (current) {
      current.setAttribute('aria-current', 'location');
      if (activeHeading.id !== currentId) { currentId = activeHeading.id; keepVisible(current); }
    }
    if (sectionLabel) {
      const label = activeHeading && activeHeading !== titleHeading ? activeHeading.dataset.sectionTitle : (titleHeading?.dataset.sectionTitle || document.title);
      if (sectionLabel.textContent !== label) sectionLabel.textContent = label;
    }
    toolbar.classList.toggle('show-heading', Boolean(titleHeading) && titleHeading.getBoundingClientRect().bottom < toolbarHeight);
    toolbar.classList.toggle('is-scrolled', window.scrollY > 2);
    const scrollable = document.documentElement.scrollHeight - window.innerHeight;
    const ratio = scrollable > 0 ? Math.min(1, Math.max(0, window.scrollY / scrollable)) : 0;
    progressBar.style.width = `${(ratio * 100).toFixed(2)}%`;
  }
  window.addEventListener('scroll', () => {
    hidePreview();
    if (!scrollPending) { scrollPending = true; requestAnimationFrame(updateCurrent); }
  }, { passive: true });
  updateCurrent();
})();
