const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const motion = matchMedia('(prefers-reduced-motion: reduce)');

function setupAppearance() {
  const toggle = $('[data-theme-toggle]');
  const sync = () => toggle?.setAttribute('aria-pressed', String(document.documentElement.dataset.theme === 'night'));
  toggle?.addEventListener('click', () => {
    const theme = document.documentElement.dataset.theme === 'night' ? 'lace' : 'night';
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem('xi-kari-project-theme', theme); } catch {}
    sync();
  });
  sync();
  const nav = $('.site-nav');
  const back = $('[data-back-top]');
  const onScroll = () => {
    nav?.classList.toggle('is-scrolled', scrollY > 24);
    if (back) back.hidden = scrollY < 600;
  };
  document.addEventListener('scroll', onScroll, { passive: true });
  document.addEventListener('pointermove', (event) => {
    if (event.clientY < 28) nav?.classList.add('is-peek');
    else if (event.clientY > 90 && !nav?.matches(':hover, :focus-within')) nav?.classList.remove('is-peek');
  }, { passive: true });
  nav?.addEventListener('pointerleave', () => nav.classList.remove('is-peek'));
  back?.addEventListener('click', () => scrollTo({ top: 0, behavior: motion.matches ? 'instant' : 'smooth' }));
  onScroll();
}

function setupMotion() {
  const hero = $('[data-home-cover]');
  const signature = $('#project-signature');
  signature?.addEventListener('signature:complete', () => { signature.dataset.signatureReady = 'true'; });
  if (signature && motion.matches) signature.dataset.signatureReady = 'true';
  let visible = true;
  const syncHero = () => { if (hero) hero.dataset.homeMotion = visible && !motion.matches && document.visibilityState === 'visible' ? 'running' : 'paused'; };
  if (hero) {
    const observer = new IntersectionObserver((entries) => { visible = entries.some((entry) => entry.isIntersecting); syncHero(); });
    observer.observe(hero);
  }
  document.addEventListener('visibilitychange', syncHero);
  motion.addEventListener('change', syncHero);
  syncHero();
  const reveal = new IntersectionObserver((entries) => entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    reveal.unobserve(entry.target);
    if (motion.matches) return;
    entry.target.animate([
      { clipPath: 'inset(0 22% 0 0)', opacity: .65, transform: 'translateX(-14px)' },
      { clipPath: 'inset(0 0% 0 0)', opacity: 1, transform: 'none' },
    ], { duration: 660, easing: 'cubic-bezier(.16,1,.3,1)' });
  }), { threshold: .12 });
  $$('[data-reveal]').forEach((element) => reveal.observe(element));
}

function setupArtwork() {
  const dialog = $('[data-art-dialog]');
  const trigger = $('[data-art-open]');
  trigger?.addEventListener('click', () => {
    if (!dialog) return;
    const img = $('img', dialog);
    if (!img.getAttribute('src')) img.src = './assets/hero-landscape.jpg';
    dialog.showModal();
    document.documentElement.style.overflow = 'hidden';
  });
  $('[data-art-close]')?.addEventListener('click', () => dialog.close());
  dialog?.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
  dialog?.addEventListener('close', () => { document.documentElement.style.overflow = ''; trigger?.focus({ preventScroll: true }); });
}

function setupCopy() {
  $$('[data-copy]').forEach((button) => button.addEventListener('click', async () => {
    const text = $(button.dataset.copy)?.textContent ?? '';
    try {
      await navigator.clipboard.writeText(text);
      button.setAttribute('aria-label', '已复制');
      $('[data-copy-status]').textContent = '已复制使用指令。';
    } catch {
      $('[data-copy-status]').textContent = '无法自动复制，请选中指令复制。';
    }
  }));
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function setupResearch() {
  const root = $('[data-research-board]');
  if (!root) return;
  const results = $('[data-research-results]');
  const status = $('[data-save-status]');
  const editor = $('[data-editor-toggle]');
  const search = $('[data-research-search]');
  const domainSelect = $('[data-domain-select]');
  const retry = $('[data-research-retry]');
  let progress;
  let token = null;
  let editMode = false;
  let saving = false;
  let activeStatus = 'all';
  let searchOpened = new Map();
  let searchActive = false;
  let modules;
  const topicNodes = new Map();
  const domainNodes = new Map();
  const navNodes = new Map();

  const message = (text, isError = false) => { status.textContent = text; status.classList.toggle('is-error', isError); };
  const requestJson = async (url, options = {}) => {
    const response = await fetch(url, { cache: 'no-store', signal: AbortSignal.timeout(10000), ...options });
    if (!response.ok) throw new Error(String(response.status));
    return response.json();
  };
  const isProgress = (value) => value?.schemaVersion === 1 && value.completed && typeof value.completed === 'object' && !Array.isArray(value.completed);
  const update = () => {
    let complete = 0;
    for (const [id, { row, check, date }] of topicNodes) {
      const stamp = progress.completed[id];
      const done = typeof stamp === 'string';
      if (done) complete++;
      check.checked = done;
      check.disabled = !editMode || saving;
      row.dataset.editable = String(editMode);
      row.classList.toggle('is-complete', done);
      date.hidden = !done;
      date.textContent = done ? `完成于 ${stamp.slice(0, 10).replaceAll('-', '.')}` : '';
    }
    for (const domain of modules) {
      const done = domain.topics.filter((topic) => typeof progress.completed[topic.id] === 'string').length;
      $('[data-domain-count]', domainNodes.get(domain.id)).textContent = `${done} / ${domain.topics.length}`;
      $('.nav-domain-count', navNodes.get(domain.id)).textContent = `${done}/${domain.topics.length}`;
    }
    $('[data-completion]').textContent = `${complete} / ${topicNodes.size} 项已完成`;
    const bar = $('[data-progress-bar]');
    bar.style.transform = `scaleX(${complete / topicNodes.size})`;
    $('[data-progress-meter]').setAttribute('aria-valuenow', String(complete));
    $('[data-progress-meter]').setAttribute('aria-valuemax', String(topicNodes.size));
    $('[data-updated]').textContent = progress.updatedAt ? `更新于 ${progress.updatedAt.slice(0, 10).replaceAll('-', '.')}` : '专题研究待逐项推进';
    editor.disabled = saving;
    editor.setAttribute('aria-pressed', String(editMode));
    editor.textContent = editMode ? '结束编辑' : '维护进度';
  };
  const filter = () => {
    const terms = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    const filtering = terms.length > 0 || activeStatus !== 'all';
    if (filtering && !searchActive) searchOpened = new Map([...domainNodes].map(([id, node]) => [id, node.open]));
    let count = 0;
    for (const domain of modules) {
      let visible = 0;
      for (const topic of domain.topics) {
        const done = typeof progress.completed[topic.id] === 'string';
        const text = `${domain.id} ${domain.title} ${topic.id} ${topic.title} ${topic.question}`.toLocaleLowerCase();
        const matches = terms.every((term) => text.includes(term)) && (activeStatus === 'all' || (activeStatus === 'done' ? done : !done));
        topicNodes.get(topic.id).row.hidden = !matches;
        if (matches) visible++;
      }
      const node = domainNodes.get(domain.id);
      node.hidden = !visible;
      navNodes.get(domain.id).hidden = !visible;
      if (filtering && visible) node.open = true;
      else if (!filtering && searchActive) node.open = searchOpened.get(domain.id) ?? false;
      count += visible;
    }
    searchActive = filtering;
    $('[data-empty]').hidden = count !== 0;
    $('[data-result-count]').textContent = filtering ? `找到 ${count} 项` : `${modules.length} 个领域 · ${topicNodes.size} 个研究问题`;
  };
  const jump = (id) => {
    if (!domainNodes.has(id)) return;
    if (domainNodes.get(id).hidden) { search.value = ''; activeStatus = 'all'; syncFilters(); filter(); }
    const domain = domainNodes.get(id);
    domain.open = true;
    domain.scrollIntoView({ behavior: motion.matches ? 'instant' : 'smooth', block: 'start' });
    $('summary', domain).focus({ preventScroll: true });
    for (const [other, link] of navNodes) link.setAttribute('aria-current', String(id === other));
    domainSelect.value = id;
    history.replaceState(null, '', `#research-${id}`);
  };
  const syncFilters = () => $$('[data-status-filter]').forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.statusFilter === activeStatus)));
  const save = async (id, completed, check) => {
    if (!editMode || !token || saving) { update(); return; }
    saving = true;
    update();
    message('正在保存项目进度…');
    try {
      const next = await requestJson('./api/research-progress', {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Project-Token': token },
        body: JSON.stringify({ id, completed }),
      });
      if (!isProgress(next)) throw new Error('invalid_progress');
      progress = next;
      message('已保存到项目进度文件。发布后，所有访客看到同一份进度。');
    } catch {
      message('保存失败，页面已恢复原进度。请确认本地维护服务仍在运行后重试。', true);
    } finally {
      saving = false;
      update();
      filter();
      if (!topicNodes.get(id).row.hidden) check.focus({ preventScroll: true });
    }
  };

  try {
    const [data, initial] = await Promise.all([requestJson('./data/research-topics.json'), requestJson('./data/research-progress.json')]);
    if (data.schemaVersion !== 1 || !Array.isArray(data.modules) || !isProgress(initial)) throw new Error('invalid_data');
    modules = data.modules;
    progress = initial;
    results.replaceChildren();
    const nav = $('[data-domain-nav]');
    for (const domain of modules) {
      const section = element('details', 'research-domain');
      section.id = `research-${domain.id}`;
      section.dataset.domain = domain.id;
      section.open = domain.id === modules[0].id;
      const summary = element('summary');
      summary.append(element('span', 'domain-number', domain.id), element('h3', '', domain.title));
      const count = element('span', 'domain-count');
      count.dataset.domainCount = '';
      summary.append(count);
      const chevron = $('#chevron-template').content.cloneNode(true);
      summary.append(chevron);
      section.append(summary);
      const list = element('ul', 'topic-list');
      for (const topic of domain.topics) {
        if (topicNodes.has(topic.id)) throw new Error('duplicate_id');
        const row = element('li', 'topic-row');
        const check = element('input', 'topic-check');
        check.type = 'checkbox';
        check.id = `topic-${topic.id}`;
        check.disabled = true;
        check.dataset.topic = topic.id;
        check.setAttribute('aria-describedby', `question-${topic.id}`);
        const label = element('label', 'topic-label');
        label.htmlFor = check.id;
        label.append(element('span', 'topic-id', topic.id), document.createTextNode(topic.title));
        const content = element('div');
        content.append(label);
        const question = element('p', 'topic-question', topic.question);
        question.id = `question-${topic.id}`;
        const date = element('span', 'completed-date');
        date.hidden = true;
        row.append(check, content, question, date);
        list.append(row);
        topicNodes.set(topic.id, { row, check, date });
        check.addEventListener('change', () => save(topic.id, check.checked, check));
      }
      section.append(list);
      results.append(section);
      domainNodes.set(domain.id, section);
      const link = element('a');
      link.href = `#research-${domain.id}`;
      link.append(element('span', '', domain.title), element('span', 'nav-domain-count'));
      link.addEventListener('click', (event) => { event.preventDefault(); jump(domain.id); });
      nav.append(link);
      navNodes.set(domain.id, link);
      const option = element('option', '', `${domain.id} ${domain.title}`);
      option.value = domain.id;
      domainSelect.append(option);
    }
    update();
    filter();
    retry.hidden = true;
    root.dataset.loaded = 'true';
    message('正式进度由项目维护者统一更新。勾选表示本轮专题研究已完成。');
    search.disabled = false;
    $$('[data-status-filter], [data-expand], [data-collapse]').forEach((button) => { button.disabled = false; });
    domainSelect.disabled = false;
    search.addEventListener('input', filter);
    $$('[data-status-filter]').forEach((button) => button.addEventListener('click', () => { activeStatus = button.dataset.statusFilter; syncFilters(); filter(); }));
    $('[data-expand]').addEventListener('click', () => { for (const node of domainNodes.values()) if (!node.hidden) node.open = true; });
    $('[data-collapse]').addEventListener('click', () => { for (const node of domainNodes.values()) node.open = false; });
    domainSelect.addEventListener('change', () => jump(domainSelect.value));
    const hash = location.hash.match(/^#research-(\d+)$/);
    if (hash) jump(hash[1]);
    if (['localhost', '127.0.0.1', '[::1]'].includes(location.hostname)) {
      try {
        const session = await requestJson('./api/project-editor');
        if (session.editable === true && typeof session.token === 'string' && isProgress(session.progress)) {
          token = session.token;
          progress = session.progress;
          editor.hidden = false;
          update();
          editor.addEventListener('click', () => {
            editMode = !editMode;
            update();
            message(editMode ? '维护模式已开启。勾选后会直接保存项目正式进度。' : '已结束编辑。进度保存在项目文件中，发布后统一展示。');
          });
        }
      } catch {}
    }
    const refresh = async () => {
      if (saving || document.visibilityState !== 'visible') return;
      try {
        const next = await requestJson('./data/research-progress.json');
        if (isProgress(next)) { progress = next; update(); filter(); }
      } catch {}
    };
    window.addEventListener('focus', refresh);
  } catch {
    results.replaceChildren(element('p', 'empty-state', '研究清单暂时未能读取，项目介绍仍可正常浏览。'));
    message('请重试加载，或下载完整研究目录。', true);
    retry.hidden = false;
    retry.onclick = () => location.reload();
  }
}

setupAppearance();
setupMotion();
setupArtwork();
setupCopy();
setupResearch();
