(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const query = (text) => (typeof matchMedia === 'function' ? matchMedia(text) : { matches: false });
  const stillness = query('(prefers-reduced-motion: reduce)');
  const canAnimate = () => !stillness.matches && typeof requestAnimationFrame === 'function';
  const COMPACT = 880;
  const ARC_ORDER = ['M4', 'M3', 'M5', 'M6', 'M7'];
  const FIX_ORDER = ['M0', 'M1', 'M2', 'M4', 'M3', 'M5', 'M6', 'M7', 'M8', 'M9'];
  const PLANE = 'M0 -11 L3 -4 L12 3 L12 6 L3 3 L2.2 9 L5 11.5 L5 13 L0 11.6 L-5 13 L-5 11.5 L-2.2 9 L-3 3 L-12 6 L-12 3 L-3 -4 Z';

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function shape(tag, attributes, parent) {
    const node = document.createElementNS(SVG_NS, tag);
    for (const [name, value] of Object.entries(attributes || {})) node.setAttribute(name, String(value));
    if (parent) parent.append(node);
    return node;
  }

  function label(parent, x, y, text, className, anchor) {
    const node = shape('text', { x: round(x), y: round(y), class: className, 'text-anchor': anchor || 'middle' }, parent);
    node.textContent = text;
    return node;
  }

  const round = (value) => Math.round(value * 10) / 10;
  const point = (p) => `${round(p.x)} ${round(p.y)}`;
  const radians = (degrees) => degrees * Math.PI / 180;

  function boxOf(node, fallbackWidth, fallbackHeight) {
    const rect = node.getBoundingClientRect();
    return { width: rect.width || fallbackWidth, height: rect.height || fallbackHeight };
  }

  function watchSize(node, redraw) {
    if (typeof ResizeObserver !== 'function') return;
    let width = 0;
    let height = 0;
    let timer = 0;
    new ResizeObserver((entries) => {
      const rect = entries[0].contentRect;
      if (Math.abs(rect.width - width) < 1 && Math.abs(rect.height - height) < 1) return;
      const first = width === 0;
      width = rect.width;
      height = rect.height;
      if (first) return;
      clearTimeout(timer);
      timer = setTimeout(redraw, 120);
    }).observe(node);
  }

  /* Published route and module data, read from the page itself */

  function readModules() {
    const modules = new Map();
    $$('[data-modules] > li').forEach((node) => {
      modules.set(node.dataset.module, {
        id: node.dataset.module,
        name: $('h3', node).textContent.trim(),
        short: node.dataset.short,
        file: node.dataset.file || '',
        must: node.dataset.must === 'true',
        node,
      });
    });
    return modules;
  }

  function readRoutes() {
    const routes = new Map();
    $$('[data-route-table] tbody tr').forEach((row) => {
      const tokens = (row.dataset.legs || '').split(/\s+/).filter(Boolean);
      const list = (value) => (value || '').split(/\s+/).filter(Boolean);
      routes.set(row.dataset.route, {
        id: row.dataset.route,
        name: row.dataset.name,
        base: tokens.filter((token) => !token.endsWith('?')),
        full: tokens.map((token) => token.replace('?', '')),
        supplement: list(row.dataset.supplement),
        from: list(row.dataset.from),
        switchLabel: row.dataset.switch || '',
        note: row.dataset.note || '',
        noteOn: row.dataset.noteOn || '',
        deliver: row.cells[2].textContent.trim(),
        row,
      });
    });
    return routes;
  }

  function planFor(route, on) {
    const plan = { id: route.id, fixes: route.base.slice(), maybe: [], lead: null };
    if (route.id === 'R2' && on) plan.fixes = route.full.slice();
    if (route.id === 'R6' && on) plan.maybe = route.supplement.slice();
    if (route.id === 'R5') { plan.lead = 'result'; plan.maybe = ['M5', 'M6']; }
    if (route.id === 'R7') plan.lead = 'full';
    if (route.id === 'R1') plan.lead = 'source';
    return plan;
  }

  /* Plan view */

  function createChart(container, modules) {
    let geometry = null;
    let layers = null;
    let frame = 0;
    let current = null;
    let onFix = () => {};

    function measure() {
      const { width, height } = boxOf(container, 1200, 600);
      const declared = typeof getComputedStyle === 'function' ? getComputedStyle(container).getPropertyValue('--plan-mode').trim() : '';
      const mode = declared || (width < 700 ? 'portrait' : 'overlay');
      const portrait = mode === 'portrait';
      const flat = mode === 'flat';
      const g = { width, height, portrait, flat, fix: {} };
      if (portrait) {
        g.a = { x: 0, y: 1 };
        g.b = { x: -1, y: 0 };
        g.center = { x: width / 2, y: height - 74 };
        g.radius = Math.min((width / 2 - 46) / Math.sin(radians(38)), g.center.y - Math.max(180, Math.min(250, height * 0.42)));
        g.angles = { M4: 38, M3: 17, M5: 0, M6: -17, M7: -38 };
        g.threshold = 90;
        g.runway = 40;
        g.rose = 30;
        const top = 46;
        const arcTop = g.center.y - g.radius;
        g.trunk = [top, top + (arcTop - top) * 0.36, top + (arcTop - top) * 0.72].map((y) => ({ x: width / 2, y }));
        g.inbound = { x: width / 2, y: 6 };
      } else if (flat) {
        g.a = { x: 1, y: 0 };
        g.b = { x: 0, y: -1 };
        const axis = height * 0.53;
        const compact = width < COMPACT;
        g.rose = compact ? 42 : 50;
        g.runway = compact ? 50 : 60;
        g.center = { x: width - Math.max(g.rose + 80, width * 0.12), y: axis };
        g.radius = Math.min(g.center.x - width * 0.46, (height - axis - 44) / Math.sin(radians(27)), (axis - 56) / Math.sin(radians(36)));
        g.angles = { M4: 36, M3: 19, M5: 0, M6: -14, M7: -27 };
        g.threshold = Math.max(g.rose + g.runway + 14, Math.min(150, g.radius * 0.36));
        const left = Math.max(64, width * 0.07);
        const edge = g.center.x - g.radius;
        g.trunk = [left, left + (edge - left) * 0.36, left + (edge - left) * 0.72].map((x) => ({ x, y: axis }));
        g.inbound = { x: 12, y: axis };
      } else {
        g.a = { x: 1, y: 0 };
        g.b = { x: 0, y: -1 };
        const axis = height * 0.6;
        g.center = { x: width - Math.max(150, width * 0.11), y: axis };
        g.radius = Math.min(g.center.x - width * 0.54, (height - axis - 44) / Math.sin(radians(27)), (axis - 56) / Math.sin(radians(36)));
        g.angles = { M4: 36, M3: 19, M5: 0, M6: -14, M7: -27 };
        g.threshold = Math.max(128, Math.min(150, g.radius * 0.33));
        g.runway = 64;
        g.rose = 52;
        const low = height - 62;
        const left = Math.max(104, width * 0.085);
        const edge = g.center.x - g.radius;
        g.trunk = [{ x: left, y: low }, { x: left + (edge - left) * 0.44, y: low }, { x: edge - Math.max(96, width * 0.078), y: axis }];
        g.inbound = { x: 14, y: low };
      }
      const along = (distance) => ({ x: g.center.x - g.a.x * distance, y: g.center.y - g.a.y * distance });
      const onArc = (degrees) => {
        const t = radians(degrees);
        return {
          x: g.center.x - g.radius * Math.cos(t) * g.a.x + g.radius * Math.sin(t) * g.b.x,
          y: g.center.y - g.radius * Math.cos(t) * g.a.y + g.radius * Math.sin(t) * g.b.y,
        };
      };
      g.along = along;
      ['M0', 'M1', 'M2'].forEach((id, index) => { g.fix[id] = g.trunk[index]; });
      for (const id of ARC_ORDER) g.fix[id] = onArc(g.angles[id]);
      g.fix.M8 = along(g.threshold + (g.radius - g.threshold) * 0.44);
      g.fix.M9 = along(g.threshold);
      g.runwayEnd = along(g.threshold - g.runway);
      g.touchdown = along(g.threshold - g.runway * 0.55);
      if (portrait) {
        g.full = { x: g.fix.M3.x - 10, y: g.fix.M3.y - 96 };
        g.direct = { x: g.center.x - 92, y: g.center.y + 6 };
        g.hold = { x: Math.min(width - 40, g.center.x + g.radius * 0.72), y: g.fix.M8.y + 66, half: 30, r: 14, vertical: true };
      } else {
        g.full = { x: g.fix.M3.x - 74, y: Math.max(40, g.fix.M4.y - 86) };
        g.direct = { x: g.center.x, y: height - 26 };
        const tight = flat && width < COMPACT;
        const half = tight ? 40 : 58;
        const r = tight ? 17 : 21;
        /* the hold keeps clear of M4's label, which sits just outside the arc */
        const clear = g.fix.M4.x + 90 + half + r;
        g.hold = { x: Math.max(g.center.x - g.radius * (flat ? 0.22 : 0.36), clear), y: axisOf(g) - g.radius * (flat ? 0.56 : 0.5), half, r, vertical: false };
      }
      return g;
    }

    function axisOf(g) { return g.center.y; }

    function arcTo(g, from, to) {
      const cross = (from.x - g.center.x) * (to.y - g.center.y) - (from.y - g.center.y) * (to.x - g.center.x);
      return `A${round(g.radius)} ${round(g.radius)} 0 0 ${cross > 0 ? 1 : 0} ${point(to)}`;
    }

    /* The optional detour to M4 leaves M2 on a curve that bows away from the direct leg to M3,
       and returns to M3 on a chord inside the arc, so both stay readable beside the base tracks. */
    function detour(g) {
      const from = g.fix.M2;
      const to = g.fix.M4;
      const other = g.fix.M3;
      const length = Math.hypot(to.x - from.x, to.y - from.y) || 1;
      let nx = -(to.y - from.y) / length;
      let ny = (to.x - from.x) / length;
      if (nx * (other.x - from.x) + ny * (other.y - from.y) > 0) { nx = -nx; ny = -ny; }
      const bow = length * 0.22;
      return `Q${round((from.x + to.x) / 2 + nx * bow)} ${round((from.y + to.y) / 2 + ny * bow)} ${point(to)}`;
    }

    function join(g, fromId, toId) {
      if (fromId === 'M2' && toId === 'M4') return detour(g);
      if (fromId === 'M4' && toId === 'M3') return `L${point(g.fix.M3)}`;
      const onArc = ARC_ORDER.includes(fromId) && ARC_ORDER.includes(toId);
      return onArc ? arcTo(g, g.fix[fromId], g.fix[toId]) : `L${point(g.fix[toId])}`;
    }

    function triangle(p, size) {
      return `M${round(p.x)} ${round(p.y - size)} L${round(p.x + size * 0.92)} ${round(p.y + size * 0.62)} L${round(p.x - size * 0.92)} ${round(p.y + size * 0.62)} Z`;
    }

    function cross(p, size) {
      const s = size;
      const t = size * 0.36;
      return `M${round(p.x - t)} ${round(p.y - s)} L${round(p.x + t)} ${round(p.y - s)} L${round(p.x + t * 0.5)} ${round(p.y - t * 0.5)}`
        + ` L${round(p.x + s)} ${round(p.y - t)} L${round(p.x + s)} ${round(p.y + t)} L${round(p.x + t * 0.5)} ${round(p.y + t * 0.5)}`
        + ` L${round(p.x + t)} ${round(p.y + s)} L${round(p.x - t)} ${round(p.y + s)} L${round(p.x - t * 0.5)} ${round(p.y + t * 0.5)}`
        + ` L${round(p.x - s)} ${round(p.y + t)} L${round(p.x - s)} ${round(p.y - t)} L${round(p.x - t * 0.5)} ${round(p.y - t * 0.5)} Z`;
    }

    function arrowHead(parent, tip, from, className, size) {
      const angle = Math.atan2(tip.y - from.y, tip.x - from.x);
      const s = size || 9;
      const left = { x: tip.x - s * Math.cos(angle - 0.42), y: tip.y - s * Math.sin(angle - 0.42) };
      const right = { x: tip.x - s * Math.cos(angle + 0.42), y: tip.y - s * Math.sin(angle + 0.42) };
      shape('path', { d: `M${point(tip)} L${point(left)} L${point(right)} Z`, class: className || 'ch-arrow' }, parent);
    }

    function racetrack(hold) {
      const { x, y, half, r } = hold;
      if (hold.vertical) {
        return `M${round(x - r)} ${round(y + half)} L${round(x - r)} ${round(y - half)} A${r} ${r} 0 0 1 ${round(x + r)} ${round(y - half)}`
          + ` L${round(x + r)} ${round(y + half)} A${r} ${r} 0 0 1 ${round(x - r)} ${round(y + half)} Z`;
      }
      return `M${round(x + half)} ${round(y - r)} L${round(x - half)} ${round(y - r)} A${r} ${r} 0 0 0 ${round(x - half)} ${round(y + r)}`
        + ` L${round(x + half)} ${round(y + r)} A${r} ${r} 0 0 0 ${round(x + half)} ${round(y - r)} Z`;
    }

    function drawBase(intro) {
      const g = geometry = measure();
      container.replaceChildren();
      const svg = shape('svg', { viewBox: `0 0 ${round(g.width)} ${round(g.height)}`, focusable: 'false' }, container);
      if (intro) svg.setAttribute('class', 'is-intro');
      const field = shape('g', { class: 'ch-g-field' }, svg);
      field.style.transformOrigin = `${round(g.center.x)}px ${round(g.center.y)}px`;
      shape('circle', { cx: round(g.center.x), cy: round(g.center.y), r: round(g.radius), class: 'ch-disc' }, field);
      shape('circle', { cx: round(g.center.x), cy: round(g.center.y), r: round(g.radius * 0.56), class: 'ch-ring' }, field);
      shape('circle', { cx: round(g.center.x), cy: round(g.center.y), r: round(g.radius), class: 'ch-arc' }, field);

      const tracks = shape('g', { class: 'ch-g-tracks' }, svg);
      const line = (d, className) => shape('path', { d, class: className || 'ch-track' }, tracks);
      line(`M${point(g.inbound)} L${point(g.fix.M0)} L${point(g.fix.M1)} L${point(g.fix.M2)}`);
      arrowHead(tracks, { x: (g.inbound.x + g.fix.M0.x) / 2 + g.a.x * 6, y: (g.inbound.y + g.fix.M0.y) / 2 + g.a.y * 6 }, g.inbound);
      line(`M${point(g.fix.M2)} L${point(g.fix.M3)}`);
      line(`M${point(g.fix.M2)} L${point(g.fix.M5)}`);
      line(`M${point(g.fix.M2)} ${detour(g)}`, 'ch-track ch-track--dash');
      line(`M${point(g.fix.M4)} L${point(g.fix.M3)}`, 'ch-track ch-track--dash');
      line(`M${point(g.fix.M3)} ${arcTo(g, g.fix.M3, g.fix.M7)}`);
      for (const id of ['M3', 'M5', 'M6', 'M7']) line(`M${point(g.fix[id])} L${point(g.fix.M8)}`);
      line(`M${point(g.fix.M8)} L${point(g.fix.M9)}`);
      line(`M${point(g.full)} L${point(g.fix.M3)}`, 'ch-track ch-track--feeder');
      line(`M${point(g.direct)} L${point(g.center)}`, 'ch-track ch-track--feeder');

      const hold = shape('g', { class: 'ch-g-missed' }, svg);
      const away = g.along(-(g.rose + (g.portrait ? 4 : 18)));
      if (g.portrait) {
        shape('path', { d: `M${point(g.runwayEnd)} L${point(g.along(-g.rose * 0.2))} Q${round(g.hold.x)} ${round(g.center.y)} ${round(g.hold.x + g.hold.r)} ${round(g.hold.y + g.hold.half)}`, class: 'ch-missed' }, hold);
      } else {
        const top = g.hold.y - g.hold.r;
        const turn = away.x + 40;
        shape('path', {
          d: `M${point(g.runwayEnd)} L${point(away)} Q${round(turn)} ${round(away.y)} ${round(turn)} ${round(away.y - 44)}`
            + ` L${round(turn)} ${round(top + 44)} Q${round(turn)} ${round(top)} ${round(turn - 44)} ${round(top)} L${round(g.hold.x + g.hold.half)} ${round(top)}`,
          class: 'ch-missed',
        }, hold);
      }
      shape('path', { d: racetrack(g.hold), class: 'ch-missed' }, hold);
      if (g.portrait) {
        label(hold, g.hold.x - g.hold.r - 8, g.hold.y + 4, '复飞', 'ch-note ch-note--ink', 'end');
      } else {
        label(hold, g.hold.x, g.hold.y + 4.5, '复飞等待', 'ch-note ch-note--ink');
        if (!(g.flat && g.width < COMPACT)) label(hold, g.hold.x, g.hold.y + g.hold.r + 20, '新材料、反例或目标改变', 'ch-note');
      }

      const field2 = shape('g', { class: 'ch-g-navaid' }, svg);
      for (let index = 0; index < 32; index += 1) {
        const t = radians(index * 11.25);
        const inner = g.rose - (index % 8 === 0 ? 13 : index % 2 === 0 ? 8 : 4);
        shape('line', {
          x1: round(g.center.x + Math.sin(t) * inner), y1: round(g.center.y - Math.cos(t) * inner),
          x2: round(g.center.x + Math.sin(t) * g.rose), y2: round(g.center.y - Math.cos(t) * g.rose),
          class: index % 8 === 0 ? 'ch-rose ch-rose--bold' : 'ch-rose',
        }, field2);
      }
      shape('circle', { cx: round(g.center.x), cy: round(g.center.y), r: g.rose, class: 'ch-rose' }, field2);
      const hex = [];
      for (let index = 0; index < 6; index += 1) {
        const t = radians(index * 60);
        hex.push(`${round(g.center.x + Math.sin(t) * 11)} ${round(g.center.y - Math.cos(t) * 11)}`);
      }
      shape('path', { d: `M${hex.join(' L')} Z`, class: 'ch-rose ch-rose--bold' }, field2);
      shape('circle', { cx: round(g.center.x), cy: round(g.center.y), r: 2.6, class: 'ch-rose-core' }, field2);

      const wide = g.portrait ? 9 : 11;
      const start = g.fix.M9;
      const end = g.runwayEnd;
      const nx = g.b.x * wide / 2;
      const ny = g.b.y * wide / 2;
      shape('path', {
        d: `M${round(start.x + nx)} ${round(start.y + ny)} L${round(end.x + nx)} ${round(end.y + ny)} L${round(end.x - nx)} ${round(end.y - ny)} L${round(start.x - nx)} ${round(start.y - ny)} Z`,
        class: 'ch-runway',
      }, field2);
      for (let index = 1; index <= 5; index += 1) {
        const p = g.along(g.threshold + index * (g.portrait ? 9 : 13));
        shape('circle', { cx: round(p.x), cy: round(p.y), r: 2.2, class: 'ch-light' }, field2);
      }

      const fixes = shape('g', { class: 'ch-g-fixes' }, svg);
      const nodes = {};
      FIX_ORDER.forEach((id, index) => {
        if (id === 'M9') return;
        const p = g.fix[id];
        const node = shape('path', { d: id === 'M8' ? cross(p, 10.5) : triangle(p, 9.5), class: 'ch-fix' }, fixes);
        node.style.animationDelay = `${360 + index * 55}ms`;
        nodes[id] = node;
      });

      const names = shape('g', { class: 'ch-g-labels' }, svg);
      const text = {};
      const tag = (id, x, y, anchor, stacked) => {
        const module = modules.get(id);
        const code = label(names, x, y, id, 'ch-code', anchor);
        const name = stacked
          ? label(names, x, y + 16, module ? module.short : '', 'ch-name', anchor)
          : label(names, x + (anchor === 'end' ? -30 : 30), y - 0.5, module ? module.short : '', 'ch-name', anchor);
        text[id] = [code, name];
      };
      if (g.portrait) {
        for (const id of ['M0', 'M1', 'M2']) tag(id, g.fix[id].x + 18, g.fix[id].y + 5, 'start', false);
        const bare = (id, x, y, anchor) => { text[id] = [label(names, x, y, id, 'ch-code', anchor), label(names, x, y, '', 'ch-name', anchor)]; };
        bare('M4', g.fix.M4.x - 14, g.fix.M4.y + 5, 'end');
        bare('M3', g.fix.M3.x - 3, g.fix.M3.y + 28, 'middle');
        bare('M5', g.fix.M5.x + 16, g.fix.M5.y - 10, 'start');
        bare('M6', g.fix.M6.x + 16, g.fix.M6.y - 8, 'start');
        bare('M7', g.fix.M7.x + 2, g.fix.M7.y - 16, 'middle');
        tag('M8', g.fix.M8.x - 20, g.fix.M8.y + 5, 'end', false);
        label(names, g.fix.M9.x - 14, g.fix.M9.y + 16, 'RWY 09', 'ch-code', 'end');
        label(names, g.fix.M9.x - 14, g.fix.M9.y + 32, 'M9 成文', 'ch-name', 'end');
        label(names, g.center.x, g.center.y + g.rose + 18, '原文 XK · 16 部分 · 附录 A–D', 'ch-note ch-note--blue', 'middle');
        label(names, g.full.x + 2, g.full.y - 8, 'R7 全读', 'ch-note ch-note--ink', 'middle');
        label(names, g.direct.x - 6, g.direct.y + 4, 'R1', 'ch-note ch-note--ink', 'end');
        label(names, g.fix.M0.x - 16, g.fix.M0.y - 14, 'R2 R3 R4 R6', 'ch-note ch-note--ink', 'end');
        label(names, g.fix.M7.x + 15, g.fix.M7.y + 5, 'R5', 'ch-note ch-note--ink', 'start');
      } else {
        for (const id of ['M0', 'M1']) tag(id, g.fix[id].x, g.fix[id].y + 31, 'middle', true);
        tag('M2', g.fix.M2.x + 4, g.fix.M2.y + 33, 'middle', true);
        tag('M4', g.fix.M4.x + 22, g.fix.M4.y + 2, 'start', true);
        tag('M3', g.fix.M3.x + 24, g.fix.M3.y - 16, 'start', true);
        tag('M5', g.fix.M5.x + 16, g.fix.M5.y + 27, 'start', true);
        tag('M6', g.fix.M6.x - 17, g.fix.M6.y + 2, 'end', true);
        tag('M7', g.fix.M7.x - 17, g.fix.M7.y + 2, 'end', true);
        tag('M8', g.fix.M8.x + 15, g.fix.M8.y - 30, 'start', true);
        const mid = (g.fix.M9.x + g.runwayEnd.x) / 2;
        label(names, mid, g.fix.M9.y + 30, 'RWY 09', 'ch-code', 'middle');
        label(names, mid, g.fix.M9.y + 46, 'M9 成文', 'ch-name', 'middle');
        label(names, g.center.x + 16, g.center.y + g.rose + 22, '原文 XK', 'ch-note ch-note--blue', 'start');
        label(names, g.center.x + 16, g.center.y + g.rose + 38, '条件结构与转化论', 'ch-note', 'start');
        label(names, g.center.x + 16, g.center.y + g.rose + 53, '16 部分 · 附录 A–D', 'ch-note', 'start');
        label(names, g.full.x - 12, g.full.y + 4, 'R7 全读进场', 'ch-note ch-note--ink', 'end');
        label(names, g.direct.x - 12, g.direct.y + 2, 'R1 直接回答', 'ch-note ch-note--ink', 'end');
        label(names, g.inbound.x + 4, g.fix.M0.y - 14, 'R2 R3 R4 R6 进场', 'ch-note ch-note--ink', 'start');
        const lower = g.height - g.center.y;
        const hazards = [
          [g.center.x - g.radius * 0.6, g.center.y - g.radius * 0.31, '收到意见 ≠ 有效反馈'],
          [g.center.x - g.radius * 0.5, g.center.y + lower * 0.62, '系统筛选 ≠ 主体选择'],
          g.flat
            ? [g.trunk[0].x + (g.trunk[2].x - g.trunk[0].x) * 0.3, g.center.y + lower * 0.62, '存续 ≠ 正当']
            : [g.trunk[1].x + (g.fix.M7.x - g.trunk[1].x) * 0.42, g.trunk[1].y - 22, '存续 ≠ 正当'],
        ];
        const roomy = !(g.flat && g.width < COMPACT);
        for (const [x, y, words] of roomy ? hazards : []) {
          shape('path', { d: `M${round(x - 7)} ${round(y + 5)} L${round(x)} ${round(y - 8)} L${round(x + 7)} ${round(y + 5)}`, class: 'ch-obstacle' }, names);
          shape('circle', { cx: round(x), cy: round(y + 1), r: 1.4, class: 'ch-rose-core' }, names);
          label(names, x + 14, y + 4, words, 'ch-note', 'start');
        }
        // far enough right that the first letter clears the edge of the approach disc
        if (roomy) label(names, g.fix.M7.x + 24, g.fix.M7.y + 27, 'R5 承接 R3、R4 的结果', 'ch-note ch-note--ink', 'start');
        label(names, g.width - 14, g.height - 12, '示意图，不按比例', 'ch-note', 'end');
      }

      const active = shape('g', { class: 'ch-g-active' }, svg);
      const faint = shape('path', { class: 'ch-active ch-active--dash', d: '' }, active);
      const path = shape('path', { class: 'ch-active', d: '' }, active);
      const stamp = shape('g', { class: 'ch-g-stamp', visibility: 'hidden' }, active);
      const plane = shape('g', { visibility: 'hidden' }, active);
      shape('path', { d: PLANE, class: 'ch-plane', transform: `scale(${g.portrait ? 0.95 : 1.2})` }, plane);
      layers = { svg, nodes, text, path, faint, plane, stamp };
    }

    function trace(plan) {
      const g = geometry;
      const stops = [];
      let d = '';
      let faint = '';
      const first = plan.fixes[0];
      if (plan.lead === 'source') {
        d = `M${point(g.direct)} L${point(g.center)}`;
        return { d, faint, stops, end: g.center };
      }
      if (plan.lead === 'full') d = `M${point(g.full)} L${point(g.fix[first])}`;
      else if (plan.lead === 'result') {
        faint = `M${point(g.fix.M5)} ${arcTo(g, g.fix.M5, g.fix.M6)}`;
        d = `M${point(g.fix.M6)} ${arcTo(g, g.fix.M6, g.fix[first])}`;
      } else d = `M${point(g.inbound)} L${point(g.fix[first])}`;
      stops.push({ id: first, d });
      for (let index = 1; index < plan.fixes.length; index += 1) {
        const from = plan.fixes[index - 1];
        const to = plan.fixes[index];
        d += ` ${join(g, from, to)}`;
        stops.push({ id: to, d });
      }
      d += ` L${point(g.touchdown)}`;
      return { d, faint, stops, end: g.touchdown };
    }

    function paint(plan, flown) {
      for (const id of Object.keys(layers.nodes)) {
        const on = plan.fixes.includes(id) && flown.has(id);
        const maybe = plan.maybe.includes(id);
        const used = plan.fixes.includes(id) || maybe;
        layers.nodes[id].setAttribute('class', `ch-fix${on ? ' ch-fix--on' : maybe ? ' ch-fix--maybe' : used ? '' : ' ch-fix--dim'}`);
        layers.text[id][0].setAttribute('class', `ch-code${used ? '' : ' ch-code--dim'}`);
        layers.text[id][1].setAttribute('class', `ch-name${used ? '' : ' ch-name--dim'}`);
      }
    }

    function placePlane(at, heading) {
      layers.plane.setAttribute('transform', `translate(${round(at.x)} ${round(at.y)}) rotate(${round(heading)})`);
      layers.plane.setAttribute('visibility', 'visible');
    }

    function stampAt(plan, visible) {
      layers.stamp.replaceChildren();
      const show = visible && plan.id === 'R4';
      layers.stamp.setAttribute('visibility', show ? 'visible' : 'hidden');
      if (!show) return;
      const p = geometry.fix.M6;
      /* above M6 in the narrow drawing; outside the arc, over M6's own label, in the wide ones */
      const out = geometry.portrait ? { x: p.x + 24, y: p.y - 27, anchor: 'start' } : { x: p.x - 17, y: p.y - 22, anchor: 'end' };
      const mark = out.anchor === 'end' ? out.x - 96 : out.x - 12;
      shape('rect', { x: round(mark), y: round(out.y - 9), width: 8, height: 8, class: 'ch-stamp' }, layers.stamp);
      label(layers.stamp, out.anchor === 'end' ? out.x : out.x + 2, out.y - 1, '已登记，只追加', 'ch-stamp-text', out.anchor);
    }

    function show(plan, animate) {
      if (!layers) return;
      cancelAnimationFrameSafe();
      current = plan;
      const route = trace(plan);
      const path = layers.path;
      path.setAttribute('d', route.d);
      layers.faint.setAttribute('d', route.faint);
      path.removeAttribute('stroke-dasharray');
      path.removeAttribute('stroke-dashoffset');
      const measurable = typeof path.getTotalLength === 'function';
      const flown = new Set();
      const finish = () => {
        plan.fixes.forEach((id) => flown.add(id));
        paint(plan, flown);
        stampAt(plan, true);
        onFix(plan.fixes.length);
        if (!measurable) return;
        const total = path.getTotalLength();
        const tip = path.getPointAtLength(total);
        const back = path.getPointAtLength(Math.max(0, total - 6));
        placePlane(tip, Math.atan2(tip.y - back.y, tip.x - back.x) * 180 / Math.PI + 90);
      };
      if (!measurable || !animate || !canAnimate()) { finish(); return; }

      const total = path.getTotalLength();
      const probe = shape('path', { d: '' });
      const marks = route.stops.map((stop) => { probe.setAttribute('d', stop.d); return probe.getTotalLength(); });
      path.setAttribute('stroke-dasharray', `${round(total)} ${round(total)}`);
      path.setAttribute('stroke-dashoffset', round(total));
      paint(plan, flown);
      stampAt(plan, false);
      onFix(0);
      const duration = Math.min(3600, 900 + total * 2);
      let began = 0;
      let passed = 0;
      const step = (now) => {
        if (!began) began = now;
        const t = Math.min(1, (now - began) / duration);
        const eased = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
        const done = total * eased;
        path.setAttribute('stroke-dashoffset', round(total - done));
        const tip = path.getPointAtLength(done);
        const back = path.getPointAtLength(Math.max(0, done - 6));
        placePlane(tip, Math.atan2(tip.y - back.y, tip.x - back.x) * 180 / Math.PI + 90);
        while (passed < marks.length && done >= marks[passed] - 1) {
          flown.add(route.stops[passed].id);
          if (route.stops[passed].id === 'M6') stampAt(plan, true);
          passed += 1;
          paint(plan, flown);
          onFix(passed);
        }
        if (t < 1) frame = requestAnimationFrame(step);
        else { frame = 0; path.removeAttribute('stroke-dasharray'); path.removeAttribute('stroke-dashoffset'); finish(); }
      };
      frame = requestAnimationFrame(step);
    }

    function cancelAnimationFrameSafe() {
      if (frame && typeof cancelAnimationFrame === 'function') cancelAnimationFrame(frame);
      frame = 0;
    }

    drawBase(canAnimate());
    watchSize(container, () => { drawBase(false); if (current) show(current, false); });
    return { show, onFix: (handler) => { onFix = handler; } };
  }

  /* Profile view */

  function createProfile(container, modules) {
    let layers = null;
    let current = null;

    function draw() {
      const { width, height } = boxOf(container, 1100, 330);
      const narrow = width < 620;
      container.replaceChildren();
      const svg = shape('svg', { viewBox: `0 0 ${round(width)} ${round(height)}`, focusable: 'false' }, container);
      const compact = width < 900;
      const left = narrow ? 26 : 62;
      const threshold = width - (narrow ? 58 : 150);
      const runwayEnd = width - (narrow ? 16 : 62);
      const fafX = threshold - (narrow ? 44 : 132);
      const spread = FIX_ORDER.slice(0, 9);
      const labelX = (id) => (id === 'M9' ? (threshold + runwayEnd) / 2 : left + (fafX - left) * spread.indexOf(id) / 8);
      const lowered = new Set();
      let reach = -Infinity;
      if (!narrow) {
        for (const id of FIX_ORDER) {
          const module = modules.get(id);
          if (!module || !module.file) continue;
          const half = module.file.length * 3.55;
          if (labelX(id) - half < reach + 10) lowered.add(id);
          else reach = labelX(id) + half;
        }
      }
      const ground = height - (narrow ? 48 : lowered.size ? 86 : 66);
      const faf = { x: fafX, y: ground - (narrow ? 58 : 74) };
      const top = narrow ? 44 : 50;
      const at = {};
      spread.forEach((id, index) => {
        at[id] = { x: left + (faf.x - left) * index / 8, y: top + (faf.y - top) * index / 8 };
      });
      at.M9 = { x: threshold, y: ground };
      shape('line', { x1: 0, y1: ground, x2: width, y2: ground, class: 'pf-ground' }, svg);
      for (let x = 8; x < width; x += 14) shape('line', { x1: x, y1: ground, x2: x - 7, y2: ground + 8, class: 'pf-hatch' }, svg);
      shape('rect', { x: round(threshold), y: round(ground - 6), width: round(runwayEnd - threshold), height: 6, class: 'ch-runway' }, svg);
      const stepped = (ids) => {
        let d = `M${point(at[ids[0]])}`;
        for (let index = 1; index < ids.length; index += 1) {
          const from = at[ids[index - 1]];
          const to = at[ids[index]];
          if (ids[index] === 'M9') d += ` L${point(to)}`;
          else d += ` L${round(from.x + (to.x - from.x) * 0.52)} ${round(from.y)} L${point(to)}`;
        }
        return d;
      };
      const whole = stepped([...spread, 'M9']);
      shape('path', { d: `${whole} L${round(at.M0.x)} ${round(ground)} Z`, class: 'pf-field' }, svg);
      shape('path', { d: whole, class: 'ch-track ch-track--feeder' }, svg);
      const missed = { x: Math.min(width - 14, runwayEnd + (narrow ? 0 : 40)), y: faf.y - (narrow ? 26 : 34) };
      shape('path', { d: `M${round(threshold + 8)} ${round(ground - 10)} Q${round(threshold + 40)} ${round(ground - 16)} ${point(missed)}`, class: 'ch-missed' }, svg);
      const arrow = shape('g', {}, svg);
      const tipAngle = Math.atan2(missed.y - (ground - 16), missed.x - (threshold + 40));
      const s = 9;
      shape('path', {
        d: `M${point(missed)} L${round(missed.x - s * Math.cos(tipAngle - 0.42))} ${round(missed.y - s * Math.sin(tipAngle - 0.42))} L${round(missed.x - s * Math.cos(tipAngle + 0.42))} ${round(missed.y - s * Math.sin(tipAngle + 0.42))} Z`,
        class: 'ch-arrow ch-arrow--soft',
      }, arrow);
      label(svg, missed.x, missed.y - 10, '复飞', 'ch-note ch-note--ink', 'end');
      const decide = { x: faf.x + (threshold - faf.x) * 0.56, y: faf.y + (ground - faf.y) * 0.56 };
      shape('line', { x1: round(decide.x - 9), y1: round(decide.y - 9), x2: round(decide.x + 9), y2: round(decide.y + 9), class: 'ch-tick' }, svg);
      label(svg, decide.x - 14, decide.y + 20, compact ? '决断点' : '决断点：落地成文，或复飞改判', 'ch-note ch-note--ink', 'end');
      label(svg, narrow ? 12 : 18, 22, '下降剖面 · 示意', 'ch-note', 'start');
      const hint = label(svg, width - (narrow ? 12 : 18), 22, '', 'ch-note ch-note--ink', 'end');

      const active = shape('path', { class: 'ch-active', d: '' }, svg);
      const lead = shape('path', { class: 'ch-active ch-active--dash', d: '' }, svg);
      const nodes = {};
      const text = {};
      const size = narrow ? 6.5 : 8.5;
      FIX_ORDER.forEach((id) => {
        const p = at[id];
        const module = modules.get(id);
        if (id !== 'M9') {
          shape('line', { x1: round(p.x), y1: round(p.y + size), x2: round(p.x), y2: round(ground), class: 'pf-drop' }, svg);
          const d = id === 'M8'
            ? `M${round(p.x - size)} ${round(p.y)} L${round(p.x)} ${round(p.y - size)} L${round(p.x + size)} ${round(p.y)} L${round(p.x)} ${round(p.y + size)} Z`
            : `M${round(p.x)} ${round(p.y - size)} L${round(p.x + size * 0.92)} ${round(p.y + size * 0.62)} L${round(p.x - size * 0.92)} ${round(p.y + size * 0.62)} Z`;
          nodes[id] = shape('path', { d, class: 'ch-fix' }, svg);
        }
        const x = id === 'M9' ? (threshold + runwayEnd) / 2 : p.x;
        const code = label(svg, x, ground + (narrow ? 27 : 22), id, 'ch-code');
        if (narrow) code.setAttribute('font-size', '11.5');
        const pieces = [code];
        if (!narrow) {
          pieces.push(label(svg, x, ground + 38, module && !compact ? module.short : '', 'ch-name'));
          if (module && module.file) {
            const row = ground + (compact ? 41 : 55) + (lowered.has(id) ? 20 : 0);
            const file = label(svg, x, row, module.file, 'pf-file');
            const half = module.file.length * 3.55;
            shape('line', { x1: round(x - half), y1: round(row + 4), x2: round(x + half), y2: round(row + 4), class: module.must ? 'pf-must' : 'pf-optional' }, svg);
            if (module.must) shape('line', { x1: round(x - half), y1: round(row - 10.5), x2: round(x + half), y2: round(row - 10.5), class: 'pf-must' }, svg);
            pieces.push(file);
          }
        }
        text[id] = pieces;
      });
      layers = { at, active, lead, nodes, text, hint, top, stepped };
    }

    function show(plan) {
      current = plan;
      if (!layers) return;
      const { at } = layers;
      let d = '';
      let lead = '';
      if (plan.fixes.length) {
        d = layers.stepped(plan.fixes);
        if (plan.lead === 'full') lead = `M${round(at[plan.fixes[0]].x)} ${round(layers.top - 22)} L${point(at[plan.fixes[0]])}`;
        if (plan.lead === 'result') lead = `M${point(at.M5)} L${point(at.M6)} L${point(at[plan.fixes[0]])}`;
      }
      layers.active.setAttribute('d', d);
      layers.lead.setAttribute('d', lead);
      layers.hint.textContent = plan.lead === 'source' ? 'R1 不经过模块链，读完相关定义后直接回答' : plan.lead === 'full' ? 'R7 全读后从 M3 进入' : plan.lead === 'result' ? 'R5 承接 R3 或 R4 的结果' : '';
      for (const id of FIX_ORDER) {
        const on = plan.fixes.includes(id);
        const maybe = plan.maybe.includes(id);
        if (layers.nodes[id]) layers.nodes[id].setAttribute('class', `ch-fix${on ? ' ch-fix--on' : maybe ? ' ch-fix--maybe' : ' ch-fix--dim'}`);
        const dim = !(on || maybe);
        layers.text[id].forEach((node, index) => {
          if (index === 0) node.setAttribute('class', dim ? 'ch-code ch-code--dim' : 'ch-code');
          else if (index === 1) node.setAttribute('class', dim ? 'ch-name ch-name--dim' : 'ch-name');
        });
      }
    }

    draw();
    watchSize(container, () => { draw(); if (current) show(current); });
    return { show };
  }

  /* Routes: the question row, the legs readout, and everything they light up */

  function setupRoutes() {
    const table = $('[data-route-table]');
    const legs = $('[data-legs]');
    if (!table || !legs) return;
    const modules = readModules();
    const routes = readRoutes();
    const buttons = $$('[data-ask] button');
    const list = $('[data-legs-list]', legs);
    const toggle = $('[data-switch]', legs);
    const input = $('[data-switch-input]', legs);
    const chartNode = $('[data-chart]');
    const profileNode = $('[data-profile]');
    const chart = chartNode ? createChart(chartNode, modules) : null;
    const profile = profileNode ? createProfile(profileNode, modules) : null;
    const state = { route: 'R2', on: false };
    let chips = [];
    if (chart) chart.onFix((count) => chips.forEach((chip, index) => chip.classList.toggle('is-flown', index < count)));

    const chip = (code, name, className) => {
      const item = element('li', className);
      item.append(element('span', 'code', code), document.createTextNode(name));
      return item;
    };

    function render(mode) {
      const route = routes.get(state.route);
      const plan = planFor(route, state.on);
      buttons.forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.route === route.id)));
      $('[data-legs-code]', legs).textContent = route.id;
      $('[data-legs-name]', legs).textContent = route.name;
      $('[data-legs-deliver]', legs).textContent = route.deliver;
      const items = [];
      if (plan.lead === 'source') items.push(chip('XK', '读相关完整定义与依赖，直接回答', 'is-from'));
      if (plan.lead === 'full') items.push(chip('全读', '', 'is-from'));
      if (plan.lead === 'result') items.push(chip(route.from.join(' / '), '的可用结果', 'is-from'));
      chips = plan.fixes.map((id) => chip(id, modules.get(id).name));
      items.push(...chips);
      if (route.id === 'R6' && state.on) plan.maybe.forEach((id) => items.push(chip(id, modules.get(id).name, 'is-optional')));
      list.replaceChildren(...items);
      toggle.hidden = !route.switchLabel;
      $('[data-switch-label]', legs).textContent = route.switchLabel;
      input.checked = state.on;
      $('[data-legs-note]', legs).textContent = state.on && route.noteOn ? route.noteOn : route.note;
      for (const other of routes.values()) other.row.classList.toggle('is-on', other.id === route.id);
      for (const module of modules.values()) module.node.classList.toggle('is-on', plan.fixes.includes(module.id));
      if (profile) profile.show(plan);
      if (!chart) chips.forEach((item) => item.classList.add('is-flown'));
      else if (mode !== 'wait') chart.show(plan, mode === 'fly');
    }

    function choose(id, on) {
      state.route = id;
      state.on = on === undefined ? id === 'R4' : on;
      render('fly');
    }

    buttons.forEach((button) => button.addEventListener('click', () => choose(button.dataset.route)));
    input.addEventListener('change', () => {
      if (state.route === 'R3' && input.checked) choose('R4', true);
      else if (state.route === 'R4' && !input.checked) choose('R3', false);
      else { state.on = input.checked; render('fly'); }
    });

    if (chart && canAnimate()) {
      render('wait');
      setTimeout(() => render('fly'), 1150);
    } else render('still');
  }

  /* The hold in the missed-approach section */

  function setupHold() {
    const node = $('[data-hold]');
    if (!node) return;
    const svg = shape('svg', { viewBox: '0 0 420 200', focusable: 'false' }, node);
    const track = 'M118 44 L302 44 A56 56 0 0 1 302 156 L118 156 A56 56 0 0 1 118 44 Z';
    shape('path', { d: 'M0 156 L52 156', class: 'ch-track' }, svg);
    shape('path', { d: 'M44 151 L55 156 L44 161 Z', class: 'ch-arrow' }, svg);
    shape('path', { d: track, class: 'ch-missed' }, svg);
    shape('path', { d: 'M204 37 L218 44 L204 51 Z', class: 'ch-arrow ch-arrow--soft' }, svg);
    shape('path', { d: 'M216 149 L202 156 L216 163 Z', class: 'ch-arrow ch-arrow--soft' }, svg);
    shape('path', { d: 'M366 100 L410 100', class: 'ch-track' }, svg);
    shape('path', { d: 'M402 95 L413 100 L402 105 Z', class: 'ch-arrow' }, svg);
    label(svg, 210, 96, '保留有效的部分', 'ch-note ch-note--ink');
    label(svg, 210, 116, '从最早受影响的模块重新进入', 'ch-note');
    label(svg, 0, 144, '复飞', 'ch-note ch-note--ink', 'start');
    label(svg, 412, 78, '再进近', 'ch-note ch-note--ink', 'end');
    const plane = shape('g', {}, svg);
    shape('path', { d: PLANE, class: 'ch-plane' }, plane);
    /* One flight: in from the missed approach, once round the hold, out toward the next approach. */
    const flight = 'M52 156 L118 156 A56 56 0 0 1 118 44 L302 44 A56 56 0 0 1 302 156 L118 156 A56 56 0 0 1 118 44'
      + ' L302 44 A56 56 0 0 1 358 100 L386 100';
    const probe = shape('path', { d: flight }, svg);
    probe.setAttribute('fill', 'none');
    const parked = 'translate(386 100) rotate(90)';
    if (typeof probe.getTotalLength !== 'function') { plane.setAttribute('transform', parked); return; }
    const total = probe.getTotalLength();
    const place = (distance) => {
      const tip = probe.getPointAtLength(distance);
      const back = probe.getPointAtLength(Math.max(0, distance - 5));
      const heading = distance < 5 ? 90 : Math.atan2(tip.y - back.y, tip.x - back.x) * 180 / Math.PI + 90;
      plane.setAttribute('transform', `translate(${round(tip.x)} ${round(tip.y)}) rotate(${round(heading)})`);
    };
    if (!canAnimate() || typeof IntersectionObserver !== 'function') { plane.setAttribute('transform', parked); return; }
    place(0);
    const duration = 4800;
    const watcher = new IntersectionObserver((entries) => {
      if (!entries.some((entry) => entry.isIntersecting)) return;
      watcher.disconnect();
      let began = 0;
      const step = (now) => {
        if (!began) began = now;
        const t = Math.min(1, (now - began) / duration);
        const eased = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
        if (t < 1) { place(total * eased); requestAnimationFrame(step); } else plane.setAttribute('transform', parked);
      };
      requestAnimationFrame(step);
    }, { threshold: 0.6 });
    watcher.observe(node);
  }

  /* The page menu on narrow screens */

  function setupMenu() {
    const menu = $('[data-menu]');
    if (!menu) return;
    const close = () => { menu.open = false; };
    $$('a', menu).forEach((link) => link.addEventListener('click', close));
    document.addEventListener('click', (event) => { if (menu.open && !menu.contains(event.target)) close(); });
    document.addEventListener('keydown', (event) => {
      if (event.key !== 'Escape' || !menu.open) return;
      close();
      const summary = $('summary', menu);
      if (summary) summary.focus();
    });
  }

  /* The book as a compass rose: sixteen parts, four appendices */

  function setupRose() {
    const node = $('[data-rose]');
    const links = $$('[data-parts] a');
    if (!node || links.length !== 20) return;
    const svg = shape('svg', { viewBox: '0 0 440 440', focusable: 'false' }, node);
    const c = 220;
    const polar = (r, degrees) => ({ x: c + r * Math.sin(radians(degrees)), y: c - r * Math.cos(radians(degrees)) });
    const spoke = (inner, outer, degrees, className) => {
      const from = polar(inner, degrees);
      const to = polar(outer, degrees);
      shape('line', { x1: round(from.x), y1: round(from.y), x2: round(to.x), y2: round(to.y), class: className }, svg);
    };
    const wedge = (inner, outer, from, to) => `M${point(polar(inner, from))} L${point(polar(outer, from))} A${outer} ${outer} 0 0 1 ${point(polar(outer, to))}`
      + ` L${point(polar(inner, to))} A${inner} ${inner} 0 0 0 ${point(polar(inner, from))} Z`;
    for (const r of [84, 122, 196]) shape('circle', { cx: c, cy: c, r, class: 'rs-ring' }, svg);
    for (let index = 0; index < 32; index += 1) spoke(196, index % 2 ? 204 : 210, index * 11.25, index % 2 ? 'rs-tick rs-tick--minor' : 'rs-tick');
    const mark = (link, d, at, text) => {
      const sector = shape('path', { d, class: 'rs-sector' }, svg);
      const number = label(svg, at.x, at.y + 5.5, text, 'rs-num');
      const light = (on) => {
        sector.setAttribute('class', `rs-sector${on ? ' is-on' : ''}`);
        number.setAttribute('class', `rs-num${on ? ' is-on' : ''}`);
        link.classList.toggle('is-on', on);
      };
      sector.addEventListener('pointerenter', () => light(true));
      sector.addEventListener('pointerleave', () => light(false));
      sector.addEventListener('click', () => { location.href = link.href; });
      link.addEventListener('pointerenter', () => light(true));
      link.addEventListener('pointerleave', () => light(false));
      link.addEventListener('focus', () => light(true));
      link.addEventListener('blur', () => light(false));
    };
    links.slice(0, 16).forEach((link, index) => {
      const from = index * 22.5;
      spoke(122, 196, from, 'rs-tick rs-tick--minor');
      mark(link, wedge(122, 196, from, from + 22.5), polar(159, from + 11.25), String(index + 1));
    });
    links.slice(16).forEach((link, index) => {
      const from = index * 90;
      spoke(84, 122, from, 'rs-tick rs-tick--minor');
      mark(link, wedge(84, 122, from, from + 90), polar(103, from + 45), 'ABCD'[index]);
    });
    const hex = [];
    for (let index = 0; index < 6; index += 1) hex.push(point(polar(30, index * 60)));
    shape('path', { d: `M${hex.join(' L')} Z`, class: 'rs-core' }, svg);
    shape('circle', { cx: c, cy: c, r: 5, class: 'rs-dot' }, svg);
    label(svg, c, c + 56, '原文 XK', 'rs-title');
    label(svg, c, c - 46, '32 个领域', 'rs-sub');
  }

  /* Appearance, navigation, the command block */

  function setupAppearance() {
    const root = document.documentElement;
    const toggle = $('[data-theme-toggle]');
    const system = () => (query('(prefers-color-scheme: dark)').matches ? 'night' : 'day');
    const current = () => (root.dataset.theme === 'night' || root.dataset.theme === 'day' ? root.dataset.theme : system());
    const sync = () => { if (toggle) toggle.setAttribute('aria-pressed', String(current() === 'night')); };
    if (toggle) {
      toggle.addEventListener('click', () => {
        const next = current() === 'night' ? 'day' : 'night';
        root.dataset.theme = next;
        try { localStorage.setItem('xi-kari-project-theme', next); } catch (error) { /* private mode keeps the choice for this visit only */ }
        sync();
      });
    }
    sync();

    const links = $$('.topnav a');
    if (typeof IntersectionObserver !== 'function' || !links.length) return;
    const byTarget = new Map(links.map((link) => [link.getAttribute('href').slice(1), link]));
    const spy = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        const owner = entry.target.id === 'top' ? 'routes' : entry.target.id;
        links.forEach((link) => {
          if (link === byTarget.get(owner)) link.setAttribute('aria-current', 'true');
          else link.removeAttribute('aria-current');
        });
      }
    }, { rootMargin: '-42% 0px -52% 0px' });
    for (const id of ['top', 'modules', 'limits', 'usage', 'source', 'research']) {
      const target = document.getElementById(id);
      if (target) spy.observe(target);
    }
    for (const id of ['continue', 'outputs']) {
      const target = document.getElementById(id);
      if (target) spy.observe(target);
    }
  }

  function setupCommand() {
    const prefix = $('[data-command-prefix]');
    const hosts = $$('[data-host]');
    hosts.forEach((button) => button.addEventListener('click', () => {
      prefix.textContent = button.dataset.host;
      hosts.forEach((other) => other.setAttribute('aria-pressed', String(other === button)));
    }));
    $$('[data-copy]').forEach((button) => button.addEventListener('click', async () => {
      const source = $(button.dataset.copy);
      const status = $('[data-copy-status]');
      try {
        await navigator.clipboard.writeText(source ? source.textContent : '');
        button.setAttribute('aria-label', '已复制');
        status.textContent = '已复制使用指令。';
      } catch (error) {
        button.setAttribute('aria-label', '复制使用指令');
        status.textContent = '无法自动复制，请选中指令复制。';
      }
    }));
  }

  /* Published research status and directory */

  async function requestJson(url) {
    const response = await fetch(url, { cache: 'no-store', signal: AbortSignal.timeout(10000) });
    if (!response.ok) throw new Error(String(response.status));
    return response.json();
  }

  function validDelivery(data) {
    const d = data && data.delivery;
    const integer = (n) => Number.isSafeInteger(n) && n >= 0;
    if (!data || data.schemaVersion !== 1 || !d || !Array.isArray(d.groups) || !Array.isArray(d.pendingItems)) return false;
    if (![d.total, d.delivered, d.pending].every(integer) || d.total === 0) return false;
    if (d.delivered + d.pending !== d.total) return false;
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
        const name = element('th', '', group.title);
        name.scope = 'row';
        const cell = element('td');
        const bar = element('progress');
        bar.max = group.total;
        bar.value = group.delivered;
        bar.textContent = `${group.delivered} / ${group.total}`;
        bar.setAttribute('aria-label', `${group.title}：${group.delivered} / ${group.total} 项已完成`);
        cell.append(bar);
        row.append(name, element('td', '', `${group.delivered} / ${group.total}`), element('td', '', String(group.total - group.delivered)), cell);
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
      const summary = $('[data-delivery-total]');
      summary.replaceChildren(element('strong', '', `${d.delivered} / ${d.total}`), document.createTextNode(' 项研究任务已完成'));
      if (d.pending) summary.append(document.createTextNode('，'), element('strong', '', String(d.pending)), document.createTextNode(' 项待完成。'));
      else summary.append(document.createTextNode('。'));
      $('[data-pending-section]').hidden = d.pending === 0;
      $('#pending-title').textContent = d.pending ? `待完成的 ${d.pending} 项研究任务` : '待完成的研究任务';
      const meter = $('[data-delivery-meter]');
      meter.setAttribute('aria-valuemax', String(d.total));
      meter.setAttribute('aria-valuenow', String(d.delivered));
      meter.setAttribute('aria-valuetext', d.pending ? `${d.delivered} 项已完成，${d.pending} 项待完成，共 ${d.total} 项` : `${d.total} 项研究任务已全部完成`);
      $('[data-delivery-fill]').style.width = `${100 * d.delivered / d.total}%`;
      const dates = [['[data-snapshot-date]', d.snapshotDate], ['[data-page-date]', data.updatedAt]];
      if (data.theory && /^\d{4}-\d{2}-\d{2}$/.test(data.theory.baselineDate || '')) dates.push(['[data-baseline-date]', data.theory.baselineDate]);
      for (const [selector, value] of dates) {
        const date = $(selector);
        if (!date) continue;
        date.dateTime = value;
        date.textContent = value.replaceAll('-', '.');
      }
      root.dataset.loaded = 'true';
      status.textContent = '';
    } catch (error) {
      status.textContent = '公开数据文件暂未读取，当前显示随页面发布的快照。可重新加载页面，或查看公开快照文件。';
      status.classList.add('is-error');
    }
  }

  function createWindrose(node, modules, jump) {
    if (!node) return { mark() {}, filter() {} };
    const svg = shape('svg', { viewBox: '0 0 320 320', focusable: 'false' }, node);
    const c = 160;
    const inner = 48;
    const outer = 146;
    const most = Math.max(...modules.map((domain) => domain.topics.length));
    const unit = (outer - inner) / most;
    const at = (r, degrees) => ({ x: c + r * Math.sin(radians(degrees)), y: c - r * Math.cos(radians(degrees)) });
    const polar = (r, degrees) => point(at(r, degrees));
    for (const count of [4, 8, 12, 16].filter((value) => value <= most)) shape('circle', { cx: c, cy: c, r: round(inner + count * unit), class: 'wr-ring' }, svg);
    const span = 360 / modules.length;
    const bars = new Map();
    modules.forEach((domain, index) => {
      const from = index * span + 0.9;
      const to = (index + 1) * span - 0.9;
      const r = inner + domain.topics.length * unit;
      const bar = shape('path', {
        d: `M${polar(inner, from)} L${polar(r, from)} A${round(r)} ${round(r)} 0 0 1 ${polar(r, to)} L${polar(inner, to)} A${inner} ${inner} 0 0 0 ${polar(inner, from)} Z`,
        class: 'wr-bar',
      }, svg);
      const title = shape('title', {}, bar);
      title.textContent = `${domain.id} ${domain.title}：${domain.topics.length} 个专题`;
      bar.addEventListener('click', () => jump(domain.id));
      bars.set(domain.id, bar);
      if (index % 8 === 0) {
        const spot = at(outer + 9, index * span + span / 2);
        label(svg, spot.x, spot.y + 3.5, domain.id, 'wr-scale');
      }
    });
    label(svg, c, c + 6, String(modules.reduce((n, domain) => n + domain.topics.length, 0)), 'wr-center');
    label(svg, c, c + 23, '个专题', 'wr-sub');
    let current = '';
    const paint = (id, out) => bars.get(id).setAttribute('class', `wr-bar${id === current ? ' is-on' : ''}${out ? ' is-out' : ''}`);
    const hidden = new Set();
    return {
      mark(id) { const before = current; current = id; if (before && bars.has(before)) paint(before, hidden.has(before)); if (bars.has(id)) paint(id, hidden.has(id)); },
      filter(id, out) { if (out) hidden.add(id); else hidden.delete(id); paint(id, out); },
    };
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
    let rose = { mark() {}, filter() {} };
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
          if (matches) visible += 1;
        }
        const node = domainNodes.get(domain.id);
        node.hidden = !visible;
        navNodes.get(domain.id).hidden = !visible;
        rose.filter(domain.id, !visible);
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
      domain.scrollIntoView({ behavior: stillness.matches ? 'instant' : 'smooth', block: 'start' });
      $('summary', domain).focus({ preventScroll: true });
      for (const [other, link] of navNodes) {
        if (id === other) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      }
      rose.mark(id);
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
          const name = element('h4', 'topic-label');
          name.append(element('span', 'topic-id', topic.id), document.createTextNode(topic.title));
          row.append(name, element('p', 'topic-question', topic.question));
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
      rose = createWindrose($('[data-windrose]'), modules, jump);
      filter();
      retry.hidden = true;
      root.dataset.loaded = 'true';
      status.textContent = '专题目录用于定位问题；历史记录与上方研究完成状态分别保留。';
      search.disabled = false;
      $$('[data-expand], [data-collapse]').forEach((button) => { button.disabled = false; });
      domainSelect.disabled = false;
      search.addEventListener('input', filter);
      $('[data-expand]').addEventListener('click', () => { for (const node of domainNodes.values()) if (!node.hidden) node.open = true; });
      $('[data-collapse]').addEventListener('click', () => { for (const node of domainNodes.values()) node.open = false; });
      domainSelect.addEventListener('change', () => jump(domainSelect.value));
      const hash = location.hash.match(/^#research-(\d+)$/);
      if (hash) jump(hash[1]);
    } catch (error) {
      results.replaceChildren(element('p', 'empty', '专题目录暂时未能读取，上方研究进度与项目介绍仍可阅读。'));
      status.textContent = '请重试加载，或下载文字专题目录。';
      status.classList.add('is-error');
      retry.hidden = false;
      retry.onclick = () => location.reload();
    }
  }

  setupAppearance();
  setupMenu();
  setupRoutes();
  setupHold();
  setupRose();
  setupCommand();
  setupResearchSnapshot();
  setupResearch();
})();
