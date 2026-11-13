(() => {
  'use strict';
  const root = document.documentElement;
  const english = (root.lang || '').toLowerCase().startsWith('en');
  const T = english ? {
    mathError: 'Formula could not be typeset; kept as written',
    askSelection: 'Ask about selection',
    start: 'Beginning (#document)',
    sectionRef: (title, id) => `${title} (#${id})`,
    question: (title, location, quote) => `Work: ${title}\nSection: ${location}\n\nPassage:\n${quote}\n\nMy question:\nPlease continue from this passage, explaining the grounds, the conditions of application, and what material would change the judgment.`,
    expanded: 'Complete formulas or footnote markers are included; edit the question, then copy it.',
    placed: 'The passage is in place; edit the question, then copy it.',
    copied: 'Copied; paste it into your conversation.',
    copyBlocked: 'The browser did not allow automatic copying. The text is selected; press Ctrl+C or use the copy menu.',
    toDay: 'Switch to day reading',
    toNight: 'Switch to night reading',
    closeContents: 'Close contents',
    openContents: 'Open contents',
    noMatch: 'No matches',
    footnote: number => `Footnote ${number}`,
    opening: 'Start',
    end: 'End',
    finished: 'Read to the end',
    read: percent => [{ n: `${percent}%` }, ' read'],
    left: (units, minutes) => [{ n: units.text }, ' words · ', { n: String(minutes) }, ' min to go'],
    barLeft: minutes => [{ n: String(minutes) }, ' min to go'],
    span: (units, minutes) => [{ n: units.text }, ' words · ', { n: String(minutes) }, ' min'],
    at: units => ['about ', { n: units.text }, ' words in'],
    held: { tables: 'Tables', figures: 'Figures', formulas: 'Formulas', notes: 'Notes' },
    scale: ['words', 'k words', 'k words'],
    key: { fix: 'Section', sub: 'Subsection', tables: 'Table', figures: 'Figure', formulas: 'Formula', flown: 'Read', found: 'Search hit' },
    copyCode: 'Copy code',
    zoom: 'Enlarge the image',
    closeZoom: 'Close the enlarged image',
    hits: 'hits',
    lastRead: title => `Last read: ${title}`
  } : {
    mathError: '公式未能排版，保留原式',
    askSelection: '追问选段',
    start: '开篇（#document）',
    sectionRef: (title, id) => `${title}（#${id}）`,
    question: (title, location, quote) => `作品：《${title}》\n章节位置：${location}\n\n原文选段：\n${quote}\n\n我的追问：\n请围绕这段原文继续展开，说明依据、适用条件和可能改变判断的材料。`,
    expanded: '已包含完整公式或脚注标记，可修改追问后复制。',
    placed: '原文已放入，可修改追问后复制。',
    copied: '已复制，可粘贴到你的对话中。',
    copyBlocked: '浏览器未允许自动复制，文本已选中，请按 Ctrl+C 或使用复制菜单。',
    toDay: '切换到日间阅读',
    toNight: '切换到夜间阅读',
    closeContents: '收起目录',
    openContents: '打开目录',
    noMatch: '没有匹配',
    footnote: number => `脚注 ${number}`,
    opening: '开篇',
    end: '文末',
    finished: '已读到文末',
    read: percent => ['已读 ', { n: `${percent}%` }],
    left: (units, minutes) => ['余 约 ', { n: units.text }, units.wan ? ' 万字 · ' : ' 字 · ', { n: String(minutes) }, ' 分钟'],
    barLeft: minutes => ['余 ', { n: String(minutes) }, ' 分钟'],
    span: (units, minutes) => ['约 ', { n: units.text }, units.wan ? ' 万字 · ' : ' 字 · ', { n: String(minutes) }, ' 分钟'],
    at: units => ['约 ', { n: units.text }, units.wan ? ' 万字处' : ' 字处'],
    held: { tables: '表', figures: '图', formulas: '式', notes: '注' },
    scale: ['字', '千字', '万字'],
    key: { fix: '章节', sub: '小节', tables: '表', figures: '图', formulas: '式', flown: '已读', found: '搜索命中' },
    copyCode: '复制代码',
    zoom: '放大查看图像',
    closeZoom: '关闭大图',
    hits: '命中',
    lastRead: title => `上次读到：${title}`
  };
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
  const faceToggle = document.getElementById('face-toggle');
  const progressBar = document.getElementById('reader-progress-bar');
  const barReadout = document.getElementById('bar-readout');
  const searchToggle = document.getElementById('search-toggle');
  const searchClose = document.getElementById('search-close');
  const toolsToggle = document.getElementById('tools-toggle');
  const rack = document.querySelector('#contents .rack');
  const rackFold = document.getElementById('rack-fold');
  const plate = document.getElementById('reader-plate');
  const chartBox = document.getElementById('reader-chart');
  const strip = document.getElementById('track-strip');
  const stripTrack = document.getElementById('strip-track');
  const stripChip = document.getElementById('strip-chip');
  const stripName = document.getElementById('strip-name');
  const stripGo = document.getElementById('strip-go');
  const dock = document.getElementById('reader-dock');
  const dockChip = document.getElementById('dock-chip');
  const dockTitle = document.getElementById('dock-title');
  const dockRead = document.getElementById('dock-read');
  const dockLeft = document.getElementById('dock-left');
  const resume = document.getElementById('resume-reading');
  const sections = [...article.querySelectorAll('[data-reader-section]')];
  const sizes = ['small', 'medium', 'large', 'largest'];
  const media = query => (typeof window.matchMedia === 'function' ? window.matchMedia(query) : null);
  const still = () => Boolean(media('(prefers-reduced-motion: reduce)')?.matches);
  const frameLater = window.requestAnimationFrame ? callback => window.requestAnimationFrame(callback) : callback => setTimeout(callback, 16);
  const round = value => Math.round(value * 10) / 10;

  function updateToolbarHeight() {
    const height = Math.ceil(toolbar.getBoundingClientRect().height);
    if (height > 0) root.style.setProperty('--toolbar-height', `${height}px`);
  }
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
        element.setAttribute('title', T.mathError);
      } else {
        element.append(display);
        element.querySelector('.math-source').hidden = true;
        element.dataset.mathRendered = 'true';
      }
    } catch (_) {
      element.classList.add('math-error');
      element.setAttribute('title', T.mathError);
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
      if (node.matches('[data-reader-chrome]')) return '';
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
      const width = bubble.offsetWidth || 112, height = bubble.offsetHeight || 36;
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
      if (questionLabel) questionLabel.textContent = T.askSelection;
      clearTimeout(bubbleTimer);
      bubbleTimer = setTimeout(placeBubble, 160);
    }
  });
  function fillQuestion(passage) {
    const location = passage.sections.length ? passage.sections.map(section => T.sectionRef(section.title, section.id)).join(' → ') : T.start;
    questionText.value = T.question(document.title, location, passage.quote);
    copyQuestion.disabled = false;
    questionStatus.textContent = passage.expanded ? T.expanded : T.placed;
  }
  function openQuestion() {
    hideBubble();
    setTools(false);
    questionPanel.hidden = false;
    document.body.classList.add('asking');
    questionButton.setAttribute('aria-expanded', 'true');
    if (selectedPassage) fillQuestion(selectedPassage);
    questionText.focus({ preventScroll: true });
  }
  function closeQuestion() {
    questionPanel.hidden = true;
    document.body.classList.remove('asking');
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
      questionStatus.textContent = T.copied;
    } catch (_) {
      questionText.focus(); questionText.select();
      questionStatus.textContent = T.copyBlocked;
    }
  });

  /* Reading preferences and the place last read stay in this browser only. */
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
    themeToggle.title = night ? T.toDay : T.toNight;
  }
  function font(value) {
    root.dataset.font = sizes.includes(value) ? value : 'medium';
    const index = sizes.indexOf(root.dataset.font);
    document.getElementById('font-smaller').disabled = index === 0;
    document.getElementById('font-larger').disabled = index === sizes.length - 1;
  }
  function face(value) {
    root.dataset.face = value === 'song' ? 'song' : 'sans';
    faceToggle?.setAttribute('aria-pressed', String(root.dataset.face === 'song'));
  }
  theme(saved('theme') || (systemDark?.matches ? 'night' : 'paper'));
  font(saved('font'));
  face(saved('face'));
  systemDark?.addEventListener?.('change', event => { if (!saved('theme')) theme(event.matches ? 'night' : 'paper'); });
  themeToggle.addEventListener('click', event => {
    const flip = () => { theme(root.dataset.theme === 'night' ? 'paper' : 'night'); saved('theme', root.dataset.theme); };
    if (typeof document.startViewTransition !== 'function' || still()) { flip(); return; }
    /* The other chart spreads outward from the switch. */
    const box = themeToggle.getBoundingClientRect();
    const x = event.clientX || box.left + box.width / 2, y = event.clientY || box.top + box.height / 2;
    const radius = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
    root.classList.add('theme-flip');
    const transition = document.startViewTransition(flip);
    transition.ready.then(() => root.animate(
      { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${radius}px at ${x}px ${y}px)`] },
      { duration: 620, easing: 'cubic-bezier(.3, .1, .2, 1)', pseudoElement: '::view-transition-new(root)' }
    )).catch(() => {});
    transition.finished.catch(() => {}).then(() => root.classList.remove('theme-flip'));
  });
  for (const [id, step] of [['font-smaller', -1], ['font-larger', 1]]) {
    document.getElementById(id).addEventListener('click', () => {
      font(sizes[Math.max(0, Math.min(sizes.length - 1, sizes.indexOf(root.dataset.font) + step))]);
      saved('font', root.dataset.font);
      refresh();
    });
  }
  faceToggle?.addEventListener('click', () => {
    face(root.dataset.face === 'song' ? 'sans' : 'song'); saved('face', root.dataset.face);
    refresh();
  });
  document.getElementById('print-reader').addEventListener('click', () => { setTools(false); window.print(); });

  /* Contents drawer on narrow screens; tool menu and search overlay on phones. */
  function nav(open) {
    document.body.classList.toggle('nav-open', open);
    navToggle.setAttribute('aria-expanded', String(open));
    navToggle.setAttribute('aria-label', open ? T.closeContents : T.openContents);
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
  function arrive(link) {
    const destination = document.getElementById((link.hash || link.getAttribute('href') || '').slice(1));
    nav(false);
    hidePreview();
    if (destination) destination.focus({ preventScroll: true });
  }
  document.querySelectorAll('#contents a[href^="#"], .reader-footer a, .bar-mark, .footnote-ref a, .footnote-backref').forEach(link => {
    link.addEventListener('click', () => arrive(link));
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
    if (!query) { status.textContent = ''; showFound(); return; }
    const walker = document.createTreeWalker(article, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
    const nodes = [], runs = []; let offset = 0, node, run;
    while ((node = walker.nextNode())) {
      const math = node.nodeType === Node.ELEMENT_NODE && node.matches('.reader-math');
      if (!math && (node.nodeType !== Node.TEXT_NODE || node.parentElement.closest('.reader-math, [data-reader-chrome]'))) continue;
      const value = math ? node.dataset.mathSource : node.data;
      const block = math && node.dataset.display === 'true' ? node : node.parentElement.closest('p, h1, h2, h3, h4, h5, h6, li, pre, td, th, figcaption') || article;
      if (!run || run.block !== block) {
        run = { block, text: '', starts: [], ends: [], space: false };
        runs.push(run);
      }
      nodes.push({ node, math, start: offset, end: offset + value.length });
      const collapse = !math && !node.parentElement.closest('pre');
      for (let i = 0; i < value.length; i++) {
        let character = value[i];
        const space = collapse && /[\t\n\f\r ]/.test(character);
        if (space && run.space) {
          run.ends[run.ends.length - 1] = offset + i + 1;
          continue;
        }
        if (space) character = ' ';
        run.text += character;
        run.starts.push(offset + i); run.ends.push(offset + i + 1);
        run.space = space;
      }
      offset += value.length;
    }
    const pattern = new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'giu');
    runs.forEach(item => {
      pattern.lastIndex = 0;
      let hit;
      while ((hit = pattern.exec(item.text)) !== null) {
        matches.push({ start: item.starts[hit.index], end: item.ends[hit.index + hit[0].length - 1] });
      }
    });
    if (!matches.length) { status.textContent = T.noMatch; showFound(); return; }
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
    showFound();
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
    label.className = 'preview-label'; label.textContent = T.footnote(link.textContent.trim());
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

  /* ---------- The track: the document measured as a route ---------- */
  const number = (element, name) => Number(element.dataset[name]) || 0;
  const model = sections.map(element => ({
    element, id: element.id, units: number(element, 'units'), minutes: number(element, 'minutes'),
    fix: element.hasAttribute('data-fix'), code: element.dataset.fix || '',
    label: element.dataset.label || element.dataset.sectionTitle || '',
    held: { tables: number(element, 'tables'), figures: number(element, 'figures'), formulas: number(element, 'formulas'), notes: number(element, 'notes') }
  }));
  let total = 0, totalMinutes = 0;
  {
    const first = article.dataset;
    total = Number(first.leadUnits) || 0; totalMinutes = Number(first.leadMinutes) || 0;
    model.forEach(item => {
      item.start = total; item.minutesStart = totalMinutes;
      total += item.units; totalMinutes += item.minutes;
    });
    total = Math.max(1, total);
  }
  const fixes = model.filter(item => item.fix);
  fixes.forEach((fix, index) => {
    const begin = model.indexOf(fix), finish = index + 1 < fixes.length ? model.indexOf(fixes[index + 1]) : model.length;
    const group = model.slice(begin, finish);
    fix.order = begin;
    fix.end = index + 1 < fixes.length ? fixes[index + 1].start : total;
    fix.span = Math.max(0, fix.end - fix.start);
    fix.time = group.reduce((sum, item) => sum + item.minutes, 0);
    fix.holds = {};
    for (const key of ['tables', 'figures', 'formulas', 'notes']) fix.holds[key] = group.reduce((sum, item) => sum + item.held[key], 0);
    fix.bay = document.querySelector(`#contents a[href="#${fix.id}"]`)?.closest('.rack-bay') || null;
  });
  const subsections = model.filter(item => !item.fix && item.start > 0);
  const hasTrack = fixes.length > 0;
  const entryBay = rack?.querySelector('.rack-entry') || null;
  const STRIP = 40;
  root.style.setProperty('--strip-height', hasTrack ? `${STRIP}px` : '0px');
  document.body.classList.toggle('has-track', hasTrack);

  function amount(units) {
    if (!english && units >= 10000) return { text: String(Math.round(units / 1000) / 10), wan: true };
    const rounded = units >= 1000 ? Math.round(units / 100) * 100 : units >= 20 ? Math.round(units / 10) * 10 : Math.round(units);
    return { text: rounded.toLocaleString('en-US'), wan: false };
  }
  function write(target, parts) {
    if (!target) return;
    const signature = parts.map(part => (typeof part === 'string' ? part : `#${part.n}`)).join('');
    if (target.dataset.shown === signature) return;
    target.dataset.shown = signature;
    target.replaceChildren(...parts.map(part => {
      if (typeof part === 'string') return document.createTextNode(part);
      const span = document.createElement('span');
      span.className = 'num'; span.textContent = part.n;
      return span;
    }));
  }

  /* Where the reading line is, in the document's own units. Headings are the survey points. */
  function survey() {
    const box = article.getBoundingClientRect();
    return {
      line: toolbar.getBoundingClientRect().height + (hasTrack ? STRIP : 0) + 48,
      tops: sections.map(element => element.getBoundingClientRect().top), top: box.top, bottom: box.bottom, tall: box.height > 0
    };
  }
  function measureAt(view, y) {
    let y0 = view.top, units0 = 0, minutes0 = 0;
    for (let index = 0; index <= model.length; index++) {
      const last = index === model.length;
      const y1 = last ? view.bottom : view.tops[index];
      const units1 = last ? total : model[index].start, minutes1 = last ? totalMinutes : model[index].minutesStart;
      if (y < y1) {
        const span = y1 - y0, part = span > 0 ? Math.min(1, Math.max(0, (y - y0) / span)) : 0;
        return { units: units0 + part * (units1 - units0), minutes: minutes0 + part * (minutes1 - minutes0) };
      }
      y0 = y1; units0 = units1; minutes0 = minutes1;
    }
    return { units: total, minutes: totalMinutes };
  }
  /* Scroll to a distance along the text: the inverse of measureAt. */
  function seek(units) {
    const view = survey();
    let y0 = view.top, units0 = 0;
    for (let index = 0; index <= model.length; index++) {
      const last = index === model.length;
      const y1 = last ? view.bottom : view.tops[index], units1 = last ? total : model[index].start;
      if (units < units1 || last) {
        const part = units1 > units0 ? Math.min(1, Math.max(0, (units - units0) / (units1 - units0))) : 0;
        window.scrollTo({ top: Math.max(0, window.scrollY + y0 + part * (y1 - y0) - view.line), behavior: still() ? 'auto' : 'smooth' });
        return;
      }
      y0 = y1; units0 = units1;
    }
  }

  const SVG = 'http://www.w3.org/2000/svg';
  const PLANE = 'M0 -11 L3 -4 L12 3 L12 6 L3 3 L2.2 9 L5 11.5 L5 13 L0 11.6 L-5 13 L-5 11.5 L-2.2 9 L-3 3 L-12 6 L-12 3 L-3 -4 Z';
  const HELD = {
    tables: 'M-4 -4h8v8h-8z M-4 0h8 M0 -4v8',
    figures: 'M-4 -4h8v8h-8z M-4 2.6l2.8-2.8 2 1.8 3.2-3.6',
    formulas: 'M3.6 -4h-6.6l3.4 4-3.4 4h6.6'
  };
  const heldKinds = [['tables', 'table'], ['figures', '.figure-image img'], ['formulas', '.math-display']];
  function shape(tag, attributes, parent) {
    const node = document.createElementNS(SVG, tag);
    for (const [key, value] of Object.entries(attributes || {})) node.setAttribute(key, String(value));
    if (parent) parent.append(node);
    return node;
  }
  function lettering(text, attributes, parent) {
    const node = shape('text', attributes, parent);
    node.textContent = text;
    return node;
  }
  function widthOf(node, size) {
    if (typeof node.getComputedTextLength === 'function') {
      try { const measured = node.getComputedTextLength(); if (measured > 0) return measured; } catch (_) { /* not laid out */ }
    }
    let width = 0;
    for (const character of node.textContent) width += character.codePointAt(0) > 0x2e7f ? size : size * 0.56;
    return width;
  }
  /* The forms a name can take, longest first: whole, then cut at a word, then, for a name written without spaces, at a
     character. A single word in an alphabet is never cut inside.
     fit(label, room) is the longest form no wider than the room; fit.forms(label) lists them all with their widths. */
  function fitter(svg, className, size) {
    const probe = lettering('', { class: className, visibility: 'hidden' }, svg);
    const forms = label => {
      const texts = [label], words = label.split(' ');
      for (let count = words.length - 1; count >= 1; count--) texts.push(words.slice(0, count).join(' ') + '…');
      const letters = [...label];
      if (words.length === 1 && letters.some(letter => letter.codePointAt(0) > 0x2e7f)) {
        for (let count = Math.min(letters.length - 1, 18); count >= 3; count--) texts.push(letters.slice(0, count).join('') + '…');
      }
      const measured = texts.map(text => { probe.textContent = text; return { text, width: widthOf(probe, size) }; });
      probe.textContent = '';
      return measured;
    };
    const fit = (label, room) => forms(label).find(form => form.width <= room) || null;
    fit.forms = forms;
    return fit;
  }
  function triangle(x, y, size) {
    return `M${round(x)} ${round(y - size)} L${round(x + size * 0.92)} ${round(y + size * 0.62)} L${round(x - size * 0.92)} ${round(y + size * 0.62)} Z`;
  }
  function polar(cx, cy, radius, turn) {
    const angle = (turn - 0.25) * Math.PI * 2;
    return [round(cx + radius * Math.cos(angle)), round(cy + radius * Math.sin(angle))];
  }
  function wedge(cx, cy, inner, outer, from, to) {
    const span = Math.max(0.004, Math.min(0.9999, to - from)), end = from + span, large = span > 0.5 ? 1 : 0;
    const a = polar(cx, cy, outer, from), b = polar(cx, cy, outer, end), c = polar(cx, cy, inner, end), d = polar(cx, cy, inner, from);
    return `M${a[0]} ${a[1]} A${outer} ${outer} 0 ${large} 1 ${b[0]} ${b[1]} L${c[0]} ${c[1]} A${inner} ${inner} 0 ${large} 0 ${d[0]} ${d[1]} Z`;
  }

  /* The rose: the whole text as one turn, each fix a sector, the reader a bearing. */
  function drawRose(parent, cx, cy, radius) {
    const group = shape('g', { class: 'ch-g-rose' }, parent);
    const inner = radius * 0.36, band = radius * 0.84;
    shape('circle', { cx, cy, r: radius, class: 'ch-rose-disc' }, group);
    const sector = shape('path', { class: 'ch-rose-wedge', d: '' }, group);
    shape('circle', { cx, cy, r: radius, class: 'ch-rose-bold' }, group);
    shape('circle', { cx, cy, r: band, class: 'ch-rose' }, group);
    shape('circle', { cx, cy, r: inner, class: 'ch-rose' }, group);
    for (let step = 0; step < 36; step++) {
      const a = polar(cx, cy, radius, step / 36), b = polar(cx, cy, radius - (step % 3 ? 2.2 : 4.4), step / 36);
      shape('path', { d: `M${a[0]} ${a[1]} L${b[0]} ${b[1]}`, class: 'ch-rose' }, group);
    }
    fixes.forEach(fix => {
      const a = polar(cx, cy, inner, fix.start / total), b = polar(cx, cy, band, fix.start / total);
      shape('path', { d: `M${a[0]} ${a[1]} L${b[0]} ${b[1]}`, class: 'ch-rose' }, group);
    });
    const hexagon = [0, 1, 2, 3, 4, 5].map(corner => polar(cx, cy, inner * 0.56, corner / 6).join(' '));
    shape('path', { d: `M${hexagon.join(' L')} Z`, class: 'ch-rose-bold' }, group);
    shape('circle', { cx, cy, r: Math.max(1.4, radius * 0.05), class: 'ch-rose-core' }, group);
    const needle = shape('path', { class: 'ch-rose-needle', d: '' }, group);
    return {
      point(units, current) {
        const from = current ? current.start / total : 0, to = current ? current.end / total : units / total;
        sector.setAttribute('d', to > from ? wedge(cx, cy, inner, band, from, to) : '');
        const a = polar(cx, cy, inner, units / total), b = polar(cx, cy, radius + 2.5, units / total);
        needle.setAttribute('d', `M${a[0]} ${a[1]} L${b[0]} ${b[1]}`);
      }
    };
  }

  /* The key names every mark the drawing uses, and wraps where the plate is narrow. */
  function drawKey(svg, left, right, top, present, forced) {
    const key = shape('g', { class: 'ch-g-key' }, svg);
    const frame = shape('rect', { class: 'ch-key only-screen' }, key), printed = shape('rect', { class: 'ch-key only-print' }, key);
    let x = left + 11, row = 0, widest = 0;
    const entry = (draw, text, name) => {
      const group = shape('g', name ? { class: name } : {}, key);
      const label = lettering(text, { class: 'ch-note' }, group);
      const width = 17 + widthOf(label, 11.5);
      if (x + width > right - 8 && x > left + 11) { row++; x = left + 11; }
      const middle = top + 12.5 + row * 20;
      draw(x + 6, middle, group);
      label.setAttribute('x', round(x + 17)); label.setAttribute('y', round(middle + 4));
      x += width + 16; widest = Math.max(widest, x);
    };
    if (fixes.length) entry((at, middle, group) => shape('path', { d: triangle(at, middle + 0.5, 5.5), class: 'ch-fix' }, group), T.key.fix);
    if (subsections.length) entry((at, middle, group) => shape('path', { d: `M${at} ${middle - 4.5} v9`, class: 'ch-tick' }, group), T.key.sub);
    for (const kind of ['tables', 'figures', 'formulas']) {
      if (present[kind]) entry((at, middle, group) => shape('path', { d: HELD[kind], transform: `translate(${at} ${middle})`, class: 'ch-held' }, group), T.key[kind]);
    }
    const fixed = [widest, row];
    if (!forced) entry((at, middle, group) => shape('path', { d: `M${at - 6} ${middle} h12`, class: 'ch-flown' }, group), T.key.flown, 'ch-key-flown');
    for (const [box, width, rows] of [[frame, widest, row], [printed, fixed[0], fixed[1]]]) {
      box.setAttribute('x', left + 0.5); box.setAttribute('y', top + 0.5);
      box.setAttribute('width', round(Math.max(10, width - left - 5))); box.setAttribute('height', 25 + rows * 20);
    }
    return top + 25 + row * 20;
  }

  const tracks = { plate: null, strip: null };
  let plateWidth = -1, stripWidth = -1, introduced = false;
  let position = { units: 0, minutes: 0 }, currentFix = null, hovered = null, pointed = null;
  function newTrack(vertical, start, length, axis, scale, hit) {
    return {
      vertical, start, length, axis, scale, hit, place: units => start + units / total * length,
      flown: null, plane: null, found: null, rose: null, marks: [], count: -1, here: null
    };
  }
  /* A track is a ruler: pointing at it reads a place, pressing it goes there. */
  function ruler(svg, track, box, hairAt) {
    const hair = shape('path', { d: '', class: 'ch-hair' }, svg);
    const pad = shape('rect', { ...box, class: 'ch-hit ch-ruler' }, svg);
    const under = event => {
      const frame = svg.getBoundingClientRect();
      const at = track.vertical ? event.clientY - frame.top : event.clientX - frame.left;
      return Math.min(total, Math.max(0, (at - track.start) / track.length * total));
    };
    const release = () => { pointed = null; hair.setAttribute('d', ''); readout(); };
    pad.addEventListener('pointermove', event => {
      if (event.pointerType === 'touch') return;
      pointed = under(event); hair.setAttribute('d', hairAt(round(track.place(pointed)))); readout();
    });
    pad.addEventListener('pointerleave', release);
    pad.addEventListener('click', event => { const units = under(event); release(); seek(units); });
  }
  /* Every fix is a way in: pressing it flies there. */
  function links(svg, track, boxOf) {
    track.marks.forEach((mark, index) => {
      const link = shape('a', { href: `#${mark.fix.id}`, tabindex: '-1' }, svg);
      shape('rect', { ...boxOf(mark, index), class: 'ch-hit' }, link);
      link.addEventListener('click', event => {
        event.preventDefault();
        mark.fix.element.scrollIntoView({ block: 'start', behavior: still() ? 'auto' : 'smooth' });
        try { history.replaceState(null, '', `#${mark.fix.id}`); } catch (_) { /* a file reader may refuse */ }
        arrive({ hash: `#${mark.fix.id}` });
        hovered = null; readout();
      });
      link.addEventListener('pointerenter', event => { if (event.pointerType !== 'touch') { hovered = mark.fix; readout(); } });
      link.addEventListener('pointerleave', () => { hovered = null; readout(); });
    });
  }
  function presentKinds() {
    const present = {};
    heldKinds.forEach(([kind, selector]) => {
      present[kind] = [...article.querySelectorAll(selector)].filter(element => !element.closest('[data-reader-chrome]'));
    });
    return present;
  }

  /* Where the marks of what the legs hold stand along a track, in reading order and clear of one another. A mark that
     would land on the one before it takes the next lane where the track has lanes, and otherwise moves along by less
     than its own width. */
  function heldPlaces(view, present, line, lanes) {
    const places = heldKinds.flatMap(([kind]) => present[kind].map(element =>
      ({ kind, at: line.place(measureAt(view, element.getBoundingClientRect().top).units), lane: 0 })));
    places.sort((a, b) => a.at - b.at);
    const last = [];
    for (const item of places) {
      if (lanes) while (last[item.lane] !== undefined && item.at - last[item.lane] < 12) item.lane++;
      else if (last[0] !== undefined && item.at - last[0] < 12) item.at = last[0] + 12;
      last[item.lane] = item.at;
    }
    return places;
  }

  /* Wide plate: the track runs left to right, names above, designators below, the rose beyond the runway. */
  function plateWide(width, forced) {
    const height = 204, y = 116, withRose = !forced && width >= 780, roseRadius = 46;
    const roseX = width - 28 - roseRadius, x0 = 44, runway = 36;
    const x1 = (withRose ? roseX - roseRadius - 26 : width - 30) - runway;
    const line = newTrack(false, x0, x1 - x0, y, 0.74, [3, 14]);
    const svg = shape('svg', { width, height, viewBox: `0 0 ${width} ${height}`, focusable: 'false' });
    chartBox.replaceChildren(svg);
    const view = survey(), present = presentKinds();

    /* scale: distance along the text */
    const step = [100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000].find(value => total / value <= 10) || 500000;
    const grade = english ? (total >= 2000 ? 1 : 0) : total >= 20000 ? 2 : total >= 2000 ? 1 : 0;
    const divisor = [1, 1000, 10000][grade];
    const scale = shape('g', { class: 'ch-g-scale' }, svg);
    shape('path', { d: `M${x0} ${height - 30} H${round(x1)}`, class: 'ch-scale' }, scale);
    const gap = (step / total) * (x1 - x0), every = gap >= 36 ? 1 : gap >= 18 ? 2 : 5;
    for (let mark = 0, count = 0; mark <= total; mark += step, count++) {
      const x = round(line.place(mark));
      shape('path', { d: `M${x} ${height - 30} v${count % every ? 3 : 6}`, class: 'ch-scale' }, scale);
      if (count % every === 0) lettering(String(Math.round(mark / divisor * 10) / 10), { x, y: height - 11, 'text-anchor': 'middle', class: 'ch-note' }, scale);
    }
    lettering(T.scale[grade], { x: round(x1 + 10), y: height - 11, class: 'ch-note' }, scale);

    /* lead-in, track, runway and what the legs hold */
    for (let dot = 0; dot < 3; dot++) shape('circle', { cx: x0 - 12 - dot * 9, cy: y, r: 1.9, class: 'ch-lead' }, svg);
    shape('path', { d: `M${x0} ${y} H${round(x1)}`, class: 'ch-track' }, svg);
    const end = shape('g', { class: 'ch-g-end' }, svg);
    shape('rect', { x: round(x1), y: y - 5, width: runway, height: 10, class: 'ch-runway' }, end);
    subsections.forEach(item => shape('path', { d: `M${round(line.place(item.start))} ${y + 4} v6`, class: 'ch-tick' }, svg));
    if (view.tall) {
      heldPlaces(view, present, line, false).forEach(item => shape('path', { d: HELD[item.kind], transform: `translate(${round(item.at)} ${y + 42})`, class: 'ch-held' }, svg));
    }
    line.found = shape('g', { class: 'ch-g-found' }, svg);
    line.flown = shape('path', { d: '', class: 'ch-flown' }, svg);
    ruler(svg, line, { x: x0, y: y - 30, width: round(x1 - x0), height: 62 }, at => `M${at} ${y - 26} V${y + 12}`);

    /* fixes: names above, designators below; the longest legs are lettered first */
    const limit = withRose ? roseX - roseRadius - 10 : width - 12;
    const rows = { near: [], far: [], code: [] };
    const free = (row, from, to) => rows[row].every(([a, b]) => to < a || from > b);
    /* Where a name of this width may stand for a fix at x, or null. Beside the track a name is centred on its fix,
       moved only by the ends of the chart itself; on a leader it may slide, but never off the fix it names. */
    const stand = (row, x, half) => {
      let left = 12, right = limit;
      for (const [a, b] of rows[row]) {
        if (x >= a && x <= b) return null;
        if (b < x) left = Math.max(left, b); else right = Math.min(right, a);
      }
      const lowest = left + 7 + half, highest = right - 7 - half;
      if (lowest > highest) return null;
      const centre = row === 'near' ? Math.min(limit - 7 - half, Math.max(19 + half, x)) : Math.min(highest, Math.max(lowest, x));
      return centre >= lowest - 0.5 && centre <= highest + 0.5 && Math.abs(centre - x) <= Math.max(0, half - 8) ? centre : null;
    };
    const fit = fitter(svg, 'ch-name', 12.5);
    shape('circle', { cx: x0, cy: y, r: 4.5, class: 'ch-entry' }, svg);
    const startName = lettering(T.opening, { x: x0 - 5, y: y - 18, class: 'ch-name' }, svg);
    rows.near.push([x0 - 8, x0 - 5 + widthOf(startName, 12.5) + 10]);
    const endName = lettering(T.end, { x: round(x1 + runway / 2), y: y + 27, 'text-anchor': 'middle', class: 'ch-name' }, end);
    const endWidth = widthOf(endName, 12.5);
    rows.code.push([x1 + runway / 2 - endWidth / 2 - 8, x1 + runway / 2 + endWidth / 2 + 8]);
    line.marks = fixes.map((fix, index) => {
      const x = line.place(fix.start);
      const node = shape('path', { d: triangle(x, y, 8.5), class: 'ch-fix' }, svg);
      node.style?.setProperty('--order', String(index + 1));
      return { fix, x, node, name: null, code: null };
    });
    [...line.marks].sort((a, b) => b.fix.span - a.fix.span).forEach(mark => {
      /* the whole name beside the track, else whole on a leader, else cut; a name with no place is left to the rack */
      const forms = mark.fix.label ? fit.forms(mark.fix.label).filter(form => form.width <= 200) : [];
      const whole = forms.length && forms[0].text === mark.fix.label ? forms.slice(0, 1) : [];
      let placed = null;
      for (const choice of [whole, forms.slice(whole.length)]) {
        for (const row of ['near', 'far']) {
          if (placed || (row === 'far' && !free('near', mark.x - 5, mark.x + 5))) continue;
          for (const form of choice) {
            const centre = stand(row, mark.x, form.width / 2);
            if (centre !== null) { placed = { row, form, centre }; break; }
          }
        }
      }
      if (placed) {
        const { row, form, centre } = placed, half = form.width / 2;
        rows[row].push([centre - half - 7, centre + half + 7]);
        mark.name = lettering(form.text, { x: round(centre), y: row === 'near' ? y - 18 : y - 42, 'text-anchor': 'middle', class: 'ch-name' }, svg);
        if (row === 'far') { shape('path', { d: `M${round(mark.x)} ${y - 12} V${y - 37}`, class: 'ch-leader' }, svg); rows.near.push([mark.x - 5, mark.x + 5]); }
      }
      if (mark.fix.code) {
        const code = lettering(mark.fix.code, { x: round(mark.x), y: y + 27, 'text-anchor': 'middle', class: 'ch-code' }, svg);
        const half = widthOf(code, 13) / 2;
        if (free('code', mark.x - half - 4, mark.x + half + 4)) { rows.code.push([mark.x - half - 4, mark.x + half + 4]); mark.code = code; } else code.remove();
      }
    });

    drawKey(svg, 13, limit, 11, Object.fromEntries(heldKinds.map(([kind]) => [kind, present[kind].length > 0])), forced);
    line.rose = withRose ? drawRose(svg, roseX, 92, roseRadius) : null;
    line.plane = shape('path', { d: PLANE, class: 'ch-plane' }, svg);
    links(svg, line, (mark, index) => {
      const before = index ? (line.marks[index - 1].x + mark.x) / 2 : mark.x - 26;
      const after = index + 1 < line.marks.length ? (line.marks[index + 1].x + mark.x) / 2 : mark.x + 26;
      const left = Math.max(before, mark.x - 26), right = Math.min(after, mark.x + 26);
      return { x: round(left), y: y - 52, width: round(Math.max(8, right - left)), height: 86 };
    });
    return line;
  }

  /* Narrow plate: the track runs down the sheet, the way the text does; names stand beside their fixes. */
  function platePortrait(width, forced) {
    const x = 66, nameX = 86, heldX = width - 17;
    const svg = shape('svg', { width, height: 10, focusable: 'false' });
    chartBox.replaceChildren(svg);
    const view = survey(), present = presentKinds();
    const keyBottom = drawKey(svg, 12, width - 12, 12, Object.fromEntries(heldKinds.map(([kind]) => [kind, present[kind].length > 0])), forced);
    const y0 = keyBottom + 36, length = Math.max(150, Math.min(320, fixes.length * 22 + 20)), y1 = y0 + length, runway = 26;
    const height = y1 + runway + 12;
    svg.setAttribute('height', height); svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    const line = newTrack(true, y0, length, x, 0.7, [14, 3]);

    for (let dot = 0; dot < 3; dot++) shape('circle', { cx: x, cy: y0 - 12 - dot * 8, r: 1.9, class: 'ch-lead' }, svg);
    shape('path', { d: `M${x} ${y0} V${y1}`, class: 'ch-track' }, svg);
    const end = shape('g', { class: 'ch-g-end' }, svg);
    shape('rect', { x: x - 5, y: y1, width: 10, height: runway, class: 'ch-runway' }, end);
    subsections.forEach(item => shape('path', { d: `M${x + 5} ${round(line.place(item.start))} h6`, class: 'ch-tick' }, svg));
    const held = view.tall ? heldPlaces(view, present, line, true) : [];
    held.forEach(item => shape('path', { d: HELD[item.kind], transform: `translate(${heldX - item.lane * 13} ${round(item.at)})`, class: 'ch-held' }, svg));
    const nameRoom = heldX - 14 - 13 * Math.max(0, ...held.map(item => item.lane)) - nameX;
    line.found = shape('g', { class: 'ch-g-found' }, svg);
    line.flown = shape('path', { d: '', class: 'ch-flown' }, svg);
    ruler(svg, line, { x: x - 24, y: y0, width: 48, height: length }, at => `M${x - 20} ${at} H${x + 20}`);

    const taken = { name: [], code: [] };
    const free = (column, from, to) => taken[column].every(([a, b]) => to < a || from > b);
    const fit = fitter(svg, 'ch-name', 12.5);
    shape('circle', { cx: x, cy: y0, r: 4.5, class: 'ch-entry' }, svg);
    /* the opening is named beside its mark, or above it where the first fix follows at once */
    const openingAt = line.place(fixes[0].start) - y0 >= 20 ? y0 : y0 - 17;
    lettering(T.opening, { x: nameX, y: round(openingAt + 4.5), class: 'ch-name' }, svg);
    taken.name.push([openingAt - 9, openingAt + 9]);
    lettering(T.end, { x: nameX, y: round(y1 + runway - 0.5), class: 'ch-name' }, end);
    taken.name.push([y1 + runway - 14, y1 + runway + 4]);
    line.marks = fixes.map((fix, index) => {
      const y = line.place(fix.start);
      const node = shape('path', { d: triangle(x, y, 8), class: 'ch-fix' }, svg);
      node.style?.setProperty('--order', String(index + 1));
      return { fix, x: y, node, name: null, code: null };
    });
    [...line.marks].sort((a, b) => b.fix.span - a.fix.span).forEach(mark => {
      const fitted = mark.fix.label && free('name', mark.x - 9, mark.x + 9) ? fit(mark.fix.label, nameRoom) : null;
      if (fitted) {
        taken.name.push([mark.x - 9, mark.x + 9]);
        mark.name = lettering(fitted.text, { x: nameX, y: round(mark.x + 4.5), class: 'ch-name' }, svg);
      }
      if (mark.fix.code && free('code', mark.x - 8, mark.x + 8)) {
        taken.code.push([mark.x - 8, mark.x + 8]);
        mark.code = lettering(mark.fix.code, { x: x - 16, y: round(mark.x + 4.5), 'text-anchor': 'end', class: 'ch-code' }, svg);
      }
    });
    line.plane = shape('path', { d: PLANE, class: 'ch-plane' }, svg);
    links(svg, line, (mark, index) => {
      /* the outer fixes take the free sheet beyond the track, so a short first or last leg still leaves a full target */
      const before = index ? (line.marks[index - 1].x + mark.x) / 2 : mark.x - 24;
      const after = index + 1 < line.marks.length ? (line.marks[index + 1].x + mark.x) / 2 : mark.x + 24;
      const top = Math.max(before, mark.x - (index ? 16 : 24)), bottom = Math.min(after, mark.x + (index + 1 < line.marks.length ? 16 : 24));
      return { x: 0, y: round(top), width, height: round(Math.max(8, bottom - top)) };
    });
    return line;
  }

  function drawPlate(forced) {
    if (!plate || !chartBox || !hasTrack) return;
    const width = Math.floor(forced || plate.clientWidth || 960);
    if (!forced && width === plateWidth && tracks.plate) return;
    plateWidth = forced ? -1 : width;
    chartBox.hidden = false;
    tracks.plate = width >= 560 ? plateWide(width, forced) : platePortrait(width, forced);
    if (!introduced && !forced && !still() && window.scrollY < 120 && survey().tall) {
      chartBox.style.setProperty('--track', String(Math.ceil(tracks.plate.length)));
      chartBox.classList.add('is-intro');
      setTimeout(() => chartBox.classList.remove('is-intro'), 1900);
    }
    introduced = true;
    fly(true);
    showFound();
  }

  /* The strip under the bar: the same track at a glance, in view for as long as the text is read. */
  function drawStrip() {
    if (!strip || !stripTrack || !hasTrack) return;
    strip.hidden = false;
    const width = Math.floor(stripTrack.clientWidth || 320);
    if (width === stripWidth && tracks.strip) return;
    stripWidth = width;
    const y = STRIP / 2, x0 = 9, runway = 14, x1 = Math.max(x0 + 40, width - 8 - runway);
    const line = newTrack(false, x0, x1 - x0, y, 0.5, [3, 10]);
    const svg = shape('svg', { width, height: STRIP, viewBox: `0 0 ${width} ${STRIP}`, focusable: 'false' });
    stripTrack.replaceChildren(svg);
    shape('path', { d: `M${x0} ${y} H${round(x1)}`, class: 'ch-track ch-thin' }, svg);
    shape('rect', { x: round(x1), y: y - 3.5, width: runway, height: 7, class: 'ch-runway' }, svg);
    subsections.forEach(item => shape('path', { d: `M${round(line.place(item.start))} ${y + 3} v4`, class: 'ch-tick' }, svg));
    line.found = shape('g', { class: 'ch-g-found' }, svg);
    line.flown = shape('path', { d: '', class: 'ch-flown ch-thin' }, svg);
    ruler(svg, line, { x: x0, y: 0, width: round(x1 - x0), height: STRIP }, at => `M${at} 6 V${STRIP - 6}`);
    shape('circle', { cx: x0, cy: y, r: 3.2, class: 'ch-entry' }, svg);
    line.marks = fixes.map(fix => {
      const x = line.place(fix.start);
      return { fix, x, node: shape('path', { d: triangle(x, y, 5.5), class: 'ch-fix' }, svg), name: null, code: null };
    });
    line.plane = shape('path', { d: PLANE, class: 'ch-plane' }, svg);
    links(svg, line, (mark, index) => {
      const before = index ? (line.marks[index - 1].x + mark.x) / 2 : mark.x - 9;
      const after = index + 1 < line.marks.length ? (line.marks[index + 1].x + mark.x) / 2 : mark.x + 9;
      const left = Math.max(before, mark.x - 12), right = Math.min(after, mark.x + 12);
      return { x: round(left), y: 0, width: round(Math.max(6, right - left)), height: STRIP };
    });
    tracks.strip = line;
    fly(true);
    showFound();
  }

  /* Move the aircraft to the reading position on every drawing of the track and fill what lies behind it. */
  function fly(redrawn) {
    const units = position.units;
    for (const line of [tracks.plate, tracks.strip]) {
      if (!line) continue;
      const at = round(line.place(units));
      line.flown.setAttribute('d', units > 0 ? (line.vertical ? `M${line.axis} ${line.start} V${at}` : `M${line.start} ${line.axis} H${at}`) : '');
      line.plane.setAttribute('transform', line.vertical
        ? `translate(${line.axis} ${at}) rotate(180) scale(${line.scale})`
        : `translate(${at} ${line.axis}) rotate(90) scale(${line.scale})`);
      const count = line.marks.filter(mark => mark.fix.start <= units && units > 0).length;
      if (redrawn || count !== line.count || line.here !== currentFix) {
        line.count = count; line.here = currentFix;
        line.marks.forEach(mark => {
          mark.node.classList.toggle('is-flown', mark.fix.start <= units && units > 0);
          mark.name?.classList.toggle('is-here', mark.fix === currentFix);
          mark.code?.classList.toggle('is-here', mark.fix === currentFix);
        });
      }
      line.rose?.point(units, currentFix);
    }
  }

  /* The dock under the plate and the strip under the bar say the same position in words. */
  function readout() {
    const under = pointed === null ? null : fixes.filter(fix => fix.start <= pointed).at(-1) || null;
    const shown = hovered || (pointed === null ? currentFix : under);
    const chip = shown ? shown.code : '', name = shown ? shown.label : T.opening;
    const done = position.units >= total, percent = Math.round(position.units / total * 100);
    const minutesLeft = Math.max(1, Math.round(totalMinutes - position.minutes));
    const brief = done ? [{ n: '100%' }] : [{ n: `${percent}%` }, ' · ', ...T.barLeft(minutesLeft)];
    let aside = null;
    if (hovered) {
      const holds = ['tables', 'figures', 'formulas', 'notes'].filter(key => hovered.holds[key]).flatMap(key => [' · ' + T.held[key] + ' ', { n: String(hovered.holds[key]) }]);
      aside = [...T.span(amount(hovered.span), Math.max(1, Math.round(hovered.time))), ...holds];
    } else if (pointed !== null) aside = T.at(amount(pointed));
    if (!hasTrack) { write(barReadout, brief); return; }
    if (dock) {
      dock.hidden = false;
      if (dockChip) dockChip.textContent = chip;
      if (dockTitle) dockTitle.textContent = name;
      write(dockRead, aside ? [] : T.read(percent));
      write(dockLeft, aside || (done ? [T.finished] : T.left(amount(total - position.units), minutesLeft)));
    }
    if (stripChip) stripChip.textContent = chip;
    if (stripName) stripName.textContent = name;
    write(stripGo, aside || brief);
  }

  /* Search hits are printed on the track and counted on the rack, whose last column then counts hits. */
  const rackUnit = document.getElementById('rack-unit');
  const lengthUnit = rackUnit ? rackUnit.textContent : '';
  function showFound() {
    document.querySelectorAll('.toc-found').forEach(chip => chip.remove());
    for (const line of [tracks.plate, tracks.strip]) line?.found?.replaceChildren();
    rack?.classList.toggle('is-searching', matches.length > 0);
    if (rackUnit) rackUnit.textContent = matches.length ? T.hits : lengthUnit;
    if (!matches.length) return;
    const view = survey();
    if (!view.tall) return;
    const counts = new Map(), places = [], seen = new Set();
    article.querySelectorAll('mark[data-match], [data-math-match]').forEach(element => {
      const ids = element.dataset.match !== undefined ? [element.dataset.match] : element.dataset.mathMatch.split(' ');
      const fresh = ids.filter(id => !seen.has(id));
      if (!fresh.length) return;
      fresh.forEach(id => seen.add(id));
      const at = measureAt(view, element.getBoundingClientRect().top).units;
      const owner = fixes.filter(fix => fix.start <= at).at(-1);
      const bay = owner ? owner.bay : entryBay;
      if (bay) counts.set(bay, (counts.get(bay) || 0) + fresh.length);
      places.push(at);
    });
    for (const line of [tracks.plate, tracks.strip]) {
      if (!line?.found) continue;
      const [across, along] = line.hit;
      new Set(places.map(at => Math.round(line.place(at) / 3) * 3)).forEach(at => {
        shape('rect', line.vertical
          ? { x: line.axis - across / 2, y: at - along / 2, width: across, height: along, class: 'ch-found' }
          : { x: at - across / 2, y: line.axis - along / 2, width: across, height: along, class: 'ch-found' }, line.found);
      });
    }
    counts.forEach((count, bay) => {
      const chip = document.createElement('span');
      chip.className = 'toc-found'; chip.setAttribute('aria-hidden', 'true'); chip.textContent = String(count);
      bay.append(chip);
    });
  }

  /* The rack unfolds the bay being read; the fold button opens them all. One holder travels to the strip being read. */
  const autoFold = rack && rack.querySelectorAll('.rack-sub li').length > 12;
  const holder = rack && hasTrack ? document.createElement('li') : null;
  if (holder) {
    holder.className = 'rack-holder'; holder.setAttribute('aria-hidden', 'true'); holder.hidden = true;
    rack.append(holder); rack.classList.add('has-holder');
  }
  function placeHolder() {
    if (!holder) return;
    const bay = rack.querySelector('.rack-bay.is-here');
    holder.hidden = !bay;
    if (!bay) return;
    holder.style.transform = `translateY(${bay.offsetTop}px)`;
    holder.style.height = `${bay.offsetHeight}px`;
  }
  function fold(all) {
    if (!rack) return;
    if (all) rack.removeAttribute('data-fold'); else rack.setAttribute('data-fold', 'auto');
    rackFold?.setAttribute('aria-pressed', String(all));
    placeHolder();
  }
  if (rack) fold(saved('fold') ? saved('fold') === 'open' : !autoFold);
  rackFold?.addEventListener('click', () => {
    const all = rack.hasAttribute('data-fold');
    fold(all); saved('fold', all ? 'open' : 'auto');
  });

  /* Code blocks can be copied; figures can be enlarged. */
  const drawing = paths => {
    const node = shape('svg', { class: 'icon', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '1.8', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'aria-hidden': 'true', focusable: 'false' });
    paths.forEach(d => shape('path', { d }, node));
    return node;
  };
  const COPY = ['M10 8h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-8a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2Z', 'M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2'];
  if (navigator.clipboard?.writeText) {
    article.querySelectorAll('pre').forEach(block => {
      if (block.closest('[data-reader-chrome], .footnote-preview')) return;
      let frame = block.parentElement;
      if (!frame.matches('figure.code-block, figure.diagram-source')) {
        frame = document.createElement('div'); frame.className = 'code-frame';
        block.replaceWith(frame); frame.append(block);
      }
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'icon-button copy-code';
      button.setAttribute('aria-label', T.copyCode); button.title = T.copyCode;
      button.append(drawing(COPY));
      button.addEventListener('click', async () => {
        try {
          await navigator.clipboard.writeText(block.textContent);
          button.replaceChildren(drawing(['m5 12 5 5L20 7'])); button.classList.add('is-done');
          setTimeout(() => { button.replaceChildren(drawing(COPY)); button.classList.remove('is-done'); }, 1600);
        } catch (_) { /* the block can still be selected by hand */ }
      });
      frame.append(button);
    });
  }
  let lightbox = null, zoomed = null;
  function closeZoom() {
    if (!lightbox) return;
    lightbox.remove(); lightbox = null;
    zoomed?.focus({ preventScroll: true }); zoomed = null;
  }
  function openZoom(image) {
    closeZoom();
    lightbox = document.createElement('button');
    lightbox.type = 'button'; lightbox.className = 'lightbox'; lightbox.setAttribute('aria-label', T.closeZoom);
    const copy = image.cloneNode(false);
    copy.removeAttribute('tabindex'); copy.removeAttribute('role'); copy.removeAttribute('loading');
    lightbox.append(copy);
    lightbox.addEventListener('click', closeZoom);
    document.body.append(lightbox);
    zoomed = image; lightbox.focus({ preventScroll: true });
  }
  article.querySelectorAll('.figure-image img').forEach(image => {
    image.tabIndex = 0; image.setAttribute('role', 'button'); image.title = T.zoom;
    image.addEventListener('click', () => openZoom(image));
    image.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); openZoom(image); } });
  });

  /* Current section, progress and the place on the track follow the scroll. */
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
  let scrollPending = false, currentId = '', storeTimer, settled = false;
  function updateCurrent() {
    scrollPending = false;
    const view = survey();
    let activeIndex = headings.length ? 0 : -1;
    view.tops.forEach((top, index) => { if (top <= view.line) activeIndex = index; });
    /* a text that fits the screen is all in view: there is no place in it to report */
    const fits = document.documentElement.scrollHeight <= window.innerHeight + 8;
    document.body.classList.toggle('fits-screen', fits);
    const reachedEnd = !fits && window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 8;
    if (reachedEnd && headings.length) activeIndex = headings.length - 1;
    const activeHeading = headings[activeIndex];
    const reached = view.tall && activeHeading && (reachedEnd || view.tops[activeIndex] <= view.line) ? activeIndex : -1;
    headingLinks.forEach(link => link.removeAttribute('aria-current'));
    /* before the first heading is reached the reader is in the opening */
    const current = (reached < 0 && view.tall && headingLinks.get('document')) || (activeHeading && headingLinks.get(activeHeading.id));
    if (current) {
      current.setAttribute('aria-current', 'location');
      const id = current.hash.slice(1);
      if (id !== currentId) { currentId = id; keepVisible(current); }
    }
    toolbar.classList.toggle('show-heading', titleHeading ? titleHeading.getBoundingClientRect().bottom < toolbar.getBoundingClientRect().height : window.scrollY > 120);

    position = reachedEnd ? { units: total, minutes: totalMinutes } : view.tall && window.scrollY > 0 ? measureAt(view, view.line) : { units: 0, minutes: 0 };
    const fixNow = fixes.filter(fix => fix.order <= reached).at(-1) || null;
    const finished = position.units >= total;
    if (fixNow !== currentFix || !settled) {
      settled = true;
      currentFix = fixNow;
      const order = fixes.indexOf(fixNow);
      fixes.forEach((fix, index) => {
        fix.bay?.classList.toggle('is-here', fix === fixNow);
        fix.bay?.classList.toggle('is-open', fix === fixNow);
        fix.bay?.classList.toggle('is-flown', index < order);
      });
      entryBay?.classList.toggle('is-here', !fixNow);
      entryBay?.classList.toggle('is-flown', Boolean(fixNow));
      placeHolder();
    }
    rack?.classList.toggle('is-finished', finished);
    progressBar.style.width = `${(position.units / total * 100).toFixed(2)}%`;

    /* once the plate has left the screen the strip under the bar carries the track */
    const docked = hasTrack && Boolean(plate) && plate.getBoundingClientRect().bottom < toolbar.getBoundingClientRect().height + 2;
    strip?.classList.toggle('is-docked', docked);
    fly(false);
    readout();

    if (resume && !resume.hidden && window.scrollY > window.innerHeight) resume.hidden = true;
    clearTimeout(storeTimer);
    if (activeHeading && window.scrollY > window.innerHeight * 0.6) {
      storeTimer = setTimeout(() => {
        const top = view.tops[activeIndex], after = activeIndex + 1 < view.tops.length ? view.tops[activeIndex + 1] : view.bottom;
        const part = after > top ? Math.min(1, Math.max(0, (view.line - top) / (after - top))) : 0;
        saved('place-' + root.dataset.doc, JSON.stringify({ id: activeHeading.id, part: Math.round(part * 1000) / 1000 }));
      }, 700);
    }
  }
  function refresh() {
    updateToolbarHeight();
    drawPlate();
    drawStrip();
    placeHolder();
    updateCurrent();
  }
  window.addEventListener('scroll', () => {
    hidePreview();
    if (!scrollPending) { scrollPending = true; frameLater(updateCurrent); }
  }, { passive: true });
  window.addEventListener('resize', () => frameLater(refresh), { passive: true });
  window.addEventListener('load', refresh);
  window.addEventListener('beforeprint', () => drawPlate(640));
  window.addEventListener('afterprint', () => drawPlate());
  if (window.ResizeObserver) {
    new ResizeObserver(updateToolbarHeight).observe(toolbar);
    if (plate) new ResizeObserver(() => frameLater(refresh)).observe(plate);
    if (stripTrack) new ResizeObserver(() => frameLater(drawStrip)).observe(stripTrack);
  }

  /* Return to the place last read in this file. */
  if (resume && root.dataset.doc && !window.location.hash) {
    let place = null;
    try { place = JSON.parse(saved('place-' + root.dataset.doc) || 'null'); } catch (_) { place = null; }
    const target = place && typeof place.id === 'string' ? document.getElementById(place.id) : null;
    if (target && sections.includes(target)) {
      resume.hidden = false;
      resume.title = T.lastRead(target.dataset.sectionTitle || '');
      resume.addEventListener('click', () => {
        const index = sections.indexOf(target);
        const top = target.getBoundingClientRect().top + window.scrollY;
        const after = index + 1 < sections.length ? sections[index + 1].getBoundingClientRect().top + window.scrollY : article.getBoundingClientRect().bottom + window.scrollY;
        window.scrollTo({ top: Math.max(0, top + (Number(place.part) || 0) * (after - top) - survey().line), behavior: still() ? 'auto' : 'smooth' });
        resume.hidden = true;
        target.focus({ preventScroll: true });
      });
    }
  }

  function step(direction) {
    const list = fixes.length ? fixes.map(fix => fix.element) : sections;
    if (!list.length) return;
    const line = survey().line + 4;
    const behind = list.filter(element => element.getBoundingClientRect().top <= line);
    const index = direction > 0 ? behind.length : behind.length - 2;
    const target = list[Math.max(0, Math.min(list.length - 1, index))];
    if (index < 0) { window.scrollTo({ top: 0, behavior: 'auto' }); return; }
    target.scrollIntoView({ block: 'start', behavior: 'auto' });
    target.focus({ preventScroll: true });
  }
  document.addEventListener('keydown', event => {
    const typing = ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName) || document.activeElement.isContentEditable;
    if (event.key === 'Escape') {
      if (lightbox) { closeZoom(); return; }
      if (!preview.hidden) { hidePreview(); return; }
      if (toolbar.classList.contains('tools-open')) { setTools(false); toolsToggle?.focus(); return; }
      if (bubble && !bubble.hidden) { hideBubble(); return; }
      if (!questionPanel.hidden && questionPanel.contains(document.activeElement)) { closeQuestion(); return; }
      if (document.body.classList.contains('nav-open')) { nav(false); navToggle.focus(); }
    }
    if (typing || event.ctrlKey || event.metaKey || event.altKey) return;
    if (event.key === '/') {
      event.preventDefault();
      if (searchToggle && getComputedStyle(searchToggle).display !== 'none') setSearching(true);
      search.focus();
    }
    if (event.key === '[' || event.key === ']') { event.preventDefault(); step(event.key === ']' ? 1 : -1); }
  });

  drawPlate();
  drawStrip();
  updateCurrent();
})();
