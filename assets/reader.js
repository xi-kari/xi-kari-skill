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
  const sections = [...article.querySelectorAll('[data-reader-section]')];
  const sizes = ['small', 'medium', 'large', 'largest'];
  const toolbar = document.querySelector('.reader-toolbar');
  function updateToolbarHeight() {
    const height = Math.ceil(toolbar.getBoundingClientRect().height);
    if (height > 0) root.style.setProperty('--toolbar-height', `${height}px`);
  }
  if (window.ResizeObserver) new ResizeObserver(updateToolbarHeight).observe(toolbar);
  window.addEventListener('resize', updateToolbarHeight, { passive: true });
  updateToolbarHeight();
  let matches = [], active = -1, timer, lastQuery = '';
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

  const questionButton = document.getElementById('quote-question');
  const questionPanel = document.getElementById('question-panel');
  const questionText = document.getElementById('question-text');
  const questionStatus = document.getElementById('question-status');
  const sectionSelect = document.getElementById('question-section');
  const copyQuestion = document.getElementById('copy-question');
  let selectedPassage = null;
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
    return value + (node.nodeType === Node.ELEMENT_NODE && /^(P|DIV|LI|TR|H[1-6]|BLOCKQUOTE|PRE)$/.test(node.tagName) ? '\n' : '');
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
  document.addEventListener('selectionchange', () => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !selection.rangeCount) return;
    const range = selection.getRangeAt(0);
    if (!article.contains(range.startContainer) || !article.contains(range.endContainer)) return;
    const passage = passageFromRange(range);
    if (passage.quote) {
      selectedPassage = passage;
      questionButton.textContent = '追问选段';
    }
  });
  function fillQuestion(passage) {
    const location = passage.sections.length ? passage.sections.map(section => `${section.title}（#${section.id}）`).join(' → ') : '开篇（#document）';
    questionText.value = `作品：《${document.title}》\n章节位置：${location}\n\n原文选段：\n${passage.quote}\n\n我的追问：\n请围绕这段原文继续展开，说明依据、适用条件和可能改变判断的材料。`;
    copyQuestion.disabled = false;
    questionStatus.textContent = passage.expanded ? '已包含完整公式或脚注标记，可修改追问后复制。' : '原文已放入，可修改追问后复制。';
  }
  questionButton.addEventListener('click', () => {
    questionPanel.hidden = false;
    questionButton.setAttribute('aria-expanded', 'true');
    if (selectedPassage) fillQuestion(selectedPassage);
    questionText.focus();
  });
  document.getElementById('close-question').addEventListener('click', () => {
    questionPanel.hidden = true;
    questionButton.setAttribute('aria-expanded', 'false');
    questionButton.focus();
  });
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
  document.querySelectorAll('#contents a[href^="#"], .reader-footer a, .footnote-ref a, .footnote-backref').forEach(link => {
    link.addEventListener('click', () => {
      const destination = document.getElementById(link.hash.slice(1));
      nav(false);
      if (destination) destination.focus({ preventScroll: true });
    });
  });
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
    status.textContent = `${active + 1} / ${matches.length} 处`;
    if (scroll && pieces.length) pieces[0].scrollIntoView({ block: 'center', behavior: 'auto' });
  }
  function find() {
    clearMarks();
    const query = search.value.trim();
    lastQuery = query;
    previous.disabled = next.disabled = true;
    if (!query) { status.textContent = '保留全部正文'; return; }
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
    if (!matches.length) { status.textContent = '未找到，可换词'; return; }
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
    if (event.key === 'Escape') { search.value = ''; clearTimeout(timer); find(); }
  });
  previous.addEventListener('click', () => select(active - 1));
  next.addEventListener('click', () => select(active + 1));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && document.body.classList.contains('nav-open')) {
      nav(false); navToggle.focus();
    }
    if (event.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName) && !document.activeElement.isContentEditable) {
      event.preventDefault(); search.focus();
    }
  });
  const headingLinks = new Map([...document.querySelectorAll('#contents nav a')].map(link => [link.hash.slice(1), link]));
  const headings = sections;
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
