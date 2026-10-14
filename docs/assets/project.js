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
      button.setAttribute('aria-label', '复制使用指令');
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

async function requestJson(url) {
  const response = await fetch(url, { cache: 'no-store', signal: AbortSignal.timeout(10000) });
  if (!response.ok) throw new Error(String(response.status));
  return response.json();
}

function validDelivery(data) {
  const d = data?.delivery;
  const integer = (n) => Number.isSafeInteger(n) && n >= 0;
  if (data?.schemaVersion !== 1 || !d || !Array.isArray(d.groups) || !Array.isArray(d.pendingItems)) return false;
  if (![d.total, d.delivered, d.pending, d.forwardDelivered, d.reverseDelivered, d.overlap].every(integer) || d.total === 0) return false;
  if (d.delivered + d.pending !== d.total || d.forwardDelivered + d.reverseDelivered - d.overlap !== d.delivered) return false;
  if (!d.groups.every((g) => typeof g.id === 'string' && typeof g.title === 'string' && integer(g.total) && integer(g.delivered) && g.total > 0 && g.delivered <= g.total)) return false;
  if (new Set(d.groups.map((g) => g.id)).size !== d.groups.length) return false;
  if (d.groups.reduce((n, g) => n + g.total, 0) !== d.total || d.groups.reduce((n, g) => n + g.delivered, 0) !== d.delivered) return false;
  if (d.pendingItems.length !== d.pending || new Set(d.pendingItems.map((item) => item.id)).size !== d.pending) return false;
  if (!d.pendingItems.every((item) => [item.id, item.title, item.detail].every((v) => typeof v === 'string' && v))) return false;
  return /^\d{4}-\d{2}-\d{2}$/.test(d.snapshotDate) && /^\d{4}-\d{2}-\d{2}$/.test(data.updatedAt);
}

async function setupResearchSnapshot() {
  const root = $('[data-delivery-snapshot]');
  if (!root) return;
  const status = $('[data-snapshot-status]');
  try {
    const data = await requestJson('./data/research-status.json');
    if (!validDelivery(data)) throw new Error('invalid_snapshot');
    const d = data.delivery;
    const groups = document.createDocumentFragment();
    for (const group of d.groups) {
      const row = element('tr');
      row.dataset.deliveryGroup = group.id;
      const label = element('th', '', group.title);
      label.scope = 'row';
      const cell = element('td');
      const bar = element('progress');
      bar.max = group.total;
      bar.value = group.delivered;
      bar.textContent = `${group.delivered} / ${group.total}`;
      bar.setAttribute('aria-label', `${group.title}：${group.delivered} / ${group.total} 项已交付`);
      cell.append(bar);
      row.append(label, element('td', '', `${group.delivered} / ${group.total}`), element('td', '', String(group.total - group.delivered)), cell);
      groups.append(row);
    }
    const pending = document.createDocumentFragment();
    for (const item of d.pendingItems) {
      const row = element('li');
      row.dataset.pendingId = item.id;
      const description = element('div');
      description.append(element('strong', '', item.title), element('p', '', item.detail));
      row.append(element('span', 'pending-id', item.id), description);
      pending.append(row);
    }
    $('[data-delivery-groups]').replaceChildren(groups);
    $('[data-pending-items]').replaceChildren(pending);
    $('[data-delivery-total]').replaceChildren(element('strong', '', `${d.delivered} / ${d.total}`), document.createTextNode(' 项已有交付，'), element('strong', '', String(d.pending)), document.createTextNode(' 项待正式交付。'));
    $('#delivery-title').textContent = `${d.total} 项任务的交付进度`;
    $('#pending-title').textContent = `仍待正式交付的 ${d.pending} 项`;
    const meter = $('[data-delivery-meter]');
    meter.setAttribute('aria-valuemax', String(d.total));
    meter.setAttribute('aria-valuenow', String(d.delivered));
    meter.setAttribute('aria-valuetext', `${d.delivered} 项已交付，${d.pending} 项待正式交付，共 ${d.total} 项`);
    $('[data-delivery-fill]').style.width = `${100 * d.delivered / d.total}%`;
    $('[data-delivery-union]').textContent = `正序 ${d.forwardDelivered} 项 + 倒序 ${d.reverseDelivered} 项 − 重复 ${d.overlap} 项 = ${d.delivered} 项。以下按任务类别统计，同一任务只计一次。`;
    for (const [selector, value] of [['[data-snapshot-date]', d.snapshotDate], ['[data-page-date]', data.updatedAt]]) {
      const date = $(selector);
      date.dateTime = value;
      date.textContent = value.replaceAll('-', '.');
    }
    root.dataset.loaded = 'true';
    status.textContent = '维护者发布的静态快照；研究统计日期与页面更新日期分别列示。';
  } catch {
    status.textContent = '公开数据文件暂未读取，当前显示随页面发布的快照。可重新加载页面，或查看公开快照文件。';
    status.classList.add('is-error');
  }
}

async function setupResearch() {
  const root = $('[data-research-board]');
  if (!root) return;
  const results = $('[data-research-results]');
  const status = $('[data-save-status]');
  const search = $('[data-research-search]');
  const domainSelect = $('[data-domain-select]');
  const retry = $('[data-research-retry]');
  let searchOpened = new Map();
  let searchActive = false;
  let modules;
  const topicNodes = new Map();
  const domainNodes = new Map();
  const navNodes = new Map();

  const filter = () => {
    const terms = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    const filtering = terms.length > 0;
    if (filtering && !searchActive) searchOpened = new Map([...domainNodes].map(([id, node]) => [id, node.open]));
    let count = 0;
    for (const domain of modules) {
      let visible = 0;
      for (const topic of domain.topics) {
        const text = `${domain.id} ${domain.title} ${topic.id} ${topic.title} ${topic.question}`.toLocaleLowerCase();
        const matches = terms.every((term) => text.includes(term));
        topicNodes.get(topic.id).hidden = !matches;
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
    if (domainNodes.get(id).hidden) { search.value = ''; filter(); }
    const domain = domainNodes.get(id);
    domain.open = true;
    domain.scrollIntoView({ behavior: motion.matches ? 'instant' : 'smooth', block: 'start' });
    $('summary', domain).focus({ preventScroll: true });
    for (const [other, link] of navNodes) {
      if (id === other) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    }
    domainSelect.value = id;
    history.replaceState(null, '', `#research-${id}`);
  };

  try {
    const data = await requestJson('./data/research-topics.json');
    if (data.schemaVersion !== 1 || !Array.isArray(data.modules) || !data.modules.length) throw new Error('invalid_data');
    modules = data.modules;
    const domainIds = new Set();
    const topicIds = new Set();
    for (const domain of modules) {
      if (typeof domain.title !== 'string' || !/^\d{2}$/.test(domain.id) || domainIds.has(domain.id) || !Array.isArray(domain.topics)) throw new Error('invalid_domain');
      domainIds.add(domain.id);
      for (const topic of domain.topics) {
        if (!/^\d{2}\.\d{2}$/.test(topic.id) || topicIds.has(topic.id) || typeof topic.title !== 'string' || typeof topic.question !== 'string') throw new Error('invalid_topic');
        topicIds.add(topic.id);
      }
    }
    results.replaceChildren();
    const nav = $('[data-domain-nav]');
    nav.replaceChildren();
    for (const domain of modules) {
      const section = element('details', 'research-domain');
      section.id = `research-${domain.id}`;
      section.dataset.domain = domain.id;
      section.open = domain.id === modules[0].id;
      const summary = element('summary');
      summary.append(element('span', 'domain-number', domain.id), element('h3', '', domain.title), element('span', 'domain-count', `${domain.topics.length} 项`));
      summary.append($('#chevron-template').content.cloneNode(true));
      section.append(summary);
      const list = element('ul', 'topic-list');
      for (const topic of domain.topics) {
        const row = element('li', 'topic-row');
        row.id = `topic-${topic.id}`;
        const label = element('h4', 'topic-label');
        label.append(element('span', 'topic-id', topic.id), document.createTextNode(topic.title));
        row.append(label, element('p', 'topic-question', topic.question));
        list.append(row);
        topicNodes.set(topic.id, row);
      }
      section.append(list);
      results.append(section);
      domainNodes.set(domain.id, section);
      const link = element('a');
      link.href = `#research-${domain.id}`;
      link.append(element('span', '', domain.title), element('span', 'nav-domain-count', String(domain.topics.length)));
      link.addEventListener('click', (event) => { event.preventDefault(); jump(domain.id); });
      nav.append(link);
      navNodes.set(domain.id, link);
      const option = element('option', '', `${domain.id} ${domain.title}`);
      option.value = domain.id;
      domainSelect.append(option);
    }
    filter();
    retry.hidden = true;
    root.dataset.loaded = 'true';
    status.textContent = '专题目录用于定位问题；历史完成记录与上方研究交付快照分别保留。';
    search.disabled = false;
    $$('[data-expand], [data-collapse]').forEach((button) => { button.disabled = false; });
    domainSelect.disabled = false;
    search.addEventListener('input', filter);
    $('[data-expand]').addEventListener('click', () => { for (const node of domainNodes.values()) if (!node.hidden) node.open = true; });
    $('[data-collapse]').addEventListener('click', () => { for (const node of domainNodes.values()) node.open = false; });
    domainSelect.addEventListener('change', () => jump(domainSelect.value));
    const hash = location.hash.match(/^#research-(\d+)$/);
    if (hash) jump(hash[1]);
  } catch {
    results.replaceChildren(element('p', 'empty-state', '专题目录暂时未能读取，上方研究进度与项目介绍仍可阅读。'));
    status.textContent = '请重试加载，或下载文字专题目录。';
    status.classList.add('is-error');
    retry.hidden = false;
    retry.onclick = () => location.reload();
  }
}

setupAppearance();
setupMotion();
setupArtwork();
setupCopy();
setupResearchSnapshot();
setupResearch();
