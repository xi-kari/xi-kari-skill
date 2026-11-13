'use strict';
/*
 * Photograph the figures the two READMEs show, the project page's social card and its
 * screenshots of the generated pages.
 *
 *   node .github/readme/src/capture.cjs <path to playwright-core> [--project <url>] [--handbook <url>] [--only <name>]
 *
 * hero        hero-*.png: the project page's briefing strip and plan view, served at --project
 * hero-en     hero-en-*.png: the same view with its words set in English, for README.en.md
 * handbook    handbook-*.png: the station band of the handbook's home page, served at --handbook
 * routes      routes-*.png and routes-en-*.png: routes.html in this folder, in Chinese and English
 * outputs     outputs-*.png here and in docs/assets: the three generated pages, built by the
 *             packaged tools into a temporary folder and framed by outputs.html
 * card        docs/assets/social-card.png: the hero's view at 1200 by 630
 *
 * Figures come in a day and a night printing (the card in day only). The hero, handbook and
 * routes figures are taken in a 1280 CSS pixel window at twice the density; the outputs frame is
 * laid out at 1920 by 870 and the card cut at 1200 by 630 from a 1440 window, both at one device
 * pixel per CSS pixel. The pages inside the outputs frame are photographed at twice the density. Every file carries an origin note in a PNG text chunk, and the hashes in
 * docs/assets/provenance.json are updated. Files are written only after every requested capture
 * has succeeded. docs/MAINTAINING.md says how to serve the two sites, which browser and fonts the
 * figures need, and when to retake.
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const { pathToFileURL } = require('url');

const NAMES = ['hero', 'hero-en', 'handbook', 'routes', 'outputs', 'card'];
const args = process.argv.slice(2);
const usage = `usage: node capture.cjs <path to playwright-core> [--project <url>] [--handbook <url>] [--only ${NAMES.join('|')}]`;
function fail(message) {
  console.error(`${message}\n${usage}`);
  process.exit(2);
}
// the playwright-core path, then flag and value pairs; anything else stops the run before it starts
if (!args[0] || args[0].startsWith('--')) fail('the first argument is the path to playwright-core');
const options = { project: 'http://localhost:4321/', handbook: 'http://localhost:4173/xi-kari-skill/handbook/', only: '' };
const given = new Set();
for (let index = 1; index < args.length; index += 2) {
  const flag = args[index];
  const value = args[index + 1];
  const name = flag.startsWith('--') ? flag.slice(2) : '';
  if (!Object.hasOwn(options, name)) fail(`unknown argument "${flag}"`);
  if (given.has(name)) fail(`--${name} is given twice`);
  if (value === undefined || value.startsWith('--')) fail(`--${name} needs a value`);
  given.add(name);
  options[name] = value;
}
const { project, handbook, only } = options;
if (only && !NAMES.includes(only)) fail(`unknown figure "${only}"`);
const wanted = (name) => !only || only === name;
const { chromium } = require(path.resolve(args[0]));

const ROOT = path.resolve(__dirname, '../../..');
const README = path.resolve(__dirname, '..');
const ASSETS = path.join(ROOT, 'docs', 'assets');
const PROVENANCE = path.join(ASSETS, 'provenance.json');
const page = (name) => pathToFileURL(path.join(__dirname, name)).href;

/* The hero keeps what stays true between releases: the download signs, the version number and
   the baseline date are left out, so the figure does not go stale with each release. The
   question dock and the legs readout answer clicks, so they are left out of a still picture
   and the plan's own frame closes under the chart. */
const HERO_CSS = `
  .plan-title .actions, .plan > .ask, .plan > .legs { display: none !important; }
  .strip > div:first-child .num { display: none !important; }
  .strip > div:has([data-baseline-date]) { display: none !important; }
  .strip { grid-template-columns: 1fr 2.1fr 1fr 1fr .7fr !important; }
`;
const HIDDEN = 'the download signs, the version number, the baseline date, the question dock and the legs readout are hidden';

/* English words for the hero of README.en.md. Module and route names are the short chart forms of
   the names in references/english.md (as the Chinese chart labels shorten the module names);
   the notes on the chart follow the English reference edition. Text that is replaced whole is
   checked against the Chinese it replaces, so a changed page stops the run instead of keeping
   an outdated translation. */
const ENGLISH = {
  chart: {
    '复飞等待': 'Go-around hold',
    '新材料、反例或目标改变': 'New material, a counterexample or a new goal',
    '问题合同': 'Problem contract',
    '材料证据': 'Materials, evidence',
    '对象状态': 'Objects, states',
    '三类变换': 'Transformations',
    '机制解释': 'Mechanisms',
    '推演': 'Projection',
    '条件前瞻': 'Conditional foresight',
    '有限选择': 'Bounded choice',
    '反方': 'Counterarguments',
    'M9 成文': 'M9 Composition',
    '原文 XK': 'Source XK',
    '条件结构与转化论': 'the whole book',
    '16 部分 · 附录 A–D': '16 parts · App. A–D',
    'R7 全读进场': 'R7 after full reading',
    'R1 直接回答': 'R1 answers directly',
    'R2 R3 R4 R6 进场': 'R2 R3 R4 R6 inbound',
    '收到意见 ≠ 有效反馈': 'Comments received ≠ effective feedback',
    '系统筛选 ≠ 主体选择': 'Selection ≠ choice',
    '存续 ≠ 正当': 'Persistence ≠ justification',
    'R5 承接 R3、R4 的结果': 'R5 from R3 or R4',
    '示意图，不按比例': 'Schematic, not to scale',
  },
  labels: { '技能': 'Skill', '理论来源': 'Theory source', '验证范围': 'Verified on', '启用方式': 'Starts', '许可': 'License' },
  values: { '仅在点名时': 'Only when named' },
  whole: [
    ['.strip > div:nth-child(2) dd', '《Xikari-条件结构与转化论》Xikari 著', '<i>Xikari: On Conditions, Structure, and Transformation</i>'],
    ['.plan-title h1', 'Xikari Skill：读完全书，再下判断。', '<span class="vh">Xikari Skill: </span>Read the whole book,<br>then judge.'],
    ['.plan-title .lede', 'Xikari Skill 是一个智能体技能。它先完整学习《Xikari-条件结构与转化论》，再按你问的是哪一类问题组合模块，交出一份写明依据、条件和改判理由的判断。',
      'Xikari Skill is an agent skill. It first studies Xikari’s <i>On Conditions, Structure, and Transformation</i> in full, then combines modules by the kind of question you ask, and delivers a judgment that states its grounds, its conditions and what would change it.'],
    ['.plan-key .key li:nth-child(1)', '必经航段', null, 'Required leg'],
    ['.plan-key .key li:nth-child(2)', '需要时才飞', null, 'Flown when needed'],
    ['.plan-key .key li:nth-child(3)', '复飞', null, 'Go-around'],
    ['.plan-key .key li:nth-child(4)', '当前航线', null, 'Current route'],
    ['.plan-key .key-scope', '阅读范围默认全读；分层须明确授权', '<strong>Reading</strong>full by default; layered only if explicitly authorized'],
  ],
};
const ENGLISH_CSS = `
  .plan-title h1 { font-size: 50px !important; line-height: 1.08 !important; }
  .plan-title .lede { max-width: 23em; font-size: 17px !important; }
  .strip { grid-template-columns: .8fr 2.8fr .9fr 1fr .6fr !important; }
`;

async function settle(tab) {
  await tab.evaluate(() => document.fonts.ready);
  await tab.waitForTimeout(1200);
}

async function toEnglish(tab) {
  const problems = await tab.evaluate((words) => {
    const problems = [];
    const flat = (text) => text.replace(/\s+/g, '');
    document.documentElement.lang = 'en';
    for (const [selector, chinese, html, text] of words.whole) {
      const node = document.querySelector(selector);
      if (!node) { problems.push(`missing ${selector}`); continue; }
      if (flat(node.textContent) !== flat(chinese)) { problems.push(`changed ${selector}: ${node.textContent.trim()}`); continue; }
      if (html !== null) node.innerHTML = html;
      else node.lastChild.textContent = text;
    }
    for (const cell of document.querySelectorAll('.strip > div')) {
      const label = cell.querySelector('dt');
      const value = cell.querySelector('dd');
      if (words.values[value.textContent.trim()]) value.textContent = words.values[value.textContent.trim()];
      if (words.labels[label.textContent.trim()]) label.textContent = words.labels[label.textContent.trim()];
    }
    const texts = () => [...document.querySelectorAll('.plan-chart svg text')];
    for (const node of texts()) {
      const text = node.textContent.trim();
      if (words.chart[text]) node.textContent = words.chart[text];
    }
    // Longer English labels are fitted to the wide drawing, whose stacked labels put the code at
    // fix + 27 and the name 16 below it (project.js, tag()):
    const label = (code) => { const all = texts(); const node = all.find((item) => item.textContent.trim() === code); return node ? [node, all[all.indexOf(node) + 1]] : []; };
    const shift = (node, dy) => node.setAttribute('y', parseFloat(node.getAttribute('y')) + dy);
    // M4's name breaks over two lines, clear of the go-around hold to its right;
    const [, m4] = label('M4');
    if (m4 && m4.textContent === 'Transformations') {
      m4.textContent = 'Transfor-';
      const rest = m4.cloneNode(false);
      rest.textContent = 'mations';
      shift(rest, 16);
      m4.after(rest);
    } else problems.push('M4 label not found');
    // M5's name would run into the M6 leg below the trunk, so both lines move above it;
    const [m5code, m5] = label('M5');
    if (m5 && m5.textContent === 'Projection') {
      const fix = parseFloat(m5code.getAttribute('y')) - 27;
      m5code.setAttribute('y', fix - 30);
      m5.setAttribute('y', fix - 13);
    } else problems.push('M5 label not found');
    // M8's name sits a little higher, clear of the aircraft at the threshold.
    const [m8code, m8] = label('M8');
    if (m8 && m8.textContent === 'Counterarguments') { shift(m8code, -6); shift(m8, -6); } else problems.push('M8 label not found');
    // anything still in Chinese means the page gained words this table does not know
    const visible = (node) => node.getClientRects().length && getComputedStyle(node).visibility !== 'hidden';
    for (const selector of ['.strip', '.plan-title', '.plan-chart svg', '.plan-key']) {
      for (const node of document.querySelectorAll(`${selector} *`)) {
        const own = [...node.childNodes].filter((child) => child.nodeType === 3).map((child) => child.textContent).join('').trim();
        if (own && visible(node) && /[㐀-鿿]/.test(own)) problems.push(`no English for: ${own}`);
      }
    }
    return problems;
  }, ENGLISH);
  if (problems.length) throw new Error(`English hero: ${problems.join(' | ')}`);
}

/* Fonts the figures are set in. routes.html and the labels of outputs.html rely on an installed
   Noto Sans SC; the project page's body text and the generated pages use their own stacks, so
   their fonts are reported, not required. */
async function fontsOf(tab, selector) {
  const session = await tab.context().newCDPSession(tab);
  await session.send('DOM.enable');
  await session.send('CSS.enable');
  const { root } = await session.send('DOM.getDocument', { depth: -1 });
  const { nodeId } = await session.send('DOM.querySelector', { nodeId: root.nodeId, selector });
  const { fonts } = nodeId ? await session.send('CSS.getPlatformFontsForNode', { nodeId }) : { fonts: [] };
  await session.detach();
  return fonts.map((font) => font.familyName);
}
async function requireFont(tab, selector, family) {
  const used = await fontsOf(tab, selector);
  if (!used.includes(family)) throw new Error(`${selector} is set in ${used.join(', ') || 'no font'}; install ${family} (SIL OFL, github.com/notofonts/noto-cjk) before retaking`);
}

/* An origin note in a PNG tEXt chunk, placed after the header chunk. */
const CRC = Array.from({ length: 256 }, (_, n) => {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c >>> 0;
});
function crc32(bytes) {
  let c = 0xffffffff;
  for (const byte of bytes) c = CRC[(c ^ byte) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}
function noted(png, note) {
  if (/[^\x20-\x7e]/.test(note)) throw new Error(`origin notes are printable ASCII: ${note}`);
  const body = Buffer.concat([Buffer.from('impeccable:prompt\0', 'latin1'), Buffer.from(note, 'latin1')]);
  const type = Buffer.from('tEXt', 'latin1');
  const length = Buffer.alloc(4);
  length.writeUInt32BE(body.length);
  const check = Buffer.alloc(4);
  check.writeUInt32BE(crc32(Buffer.concat([type, body])));
  const header = 8 + 8 + 13 + 4;
  return Buffer.concat([png.subarray(0, header), length, type, body, check, png.subarray(header)]);
}

const pending = [];
const keep = (files, png, note) => pending.push({ files: [].concat(files), data: noted(png, note) });

async function hero(tab, english) {
  await tab.goto(project, { waitUntil: 'load' });
  await tab.addStyleTag({ content: HERO_CSS + (english ? ENGLISH_CSS : '') });
  await tab.waitForSelector('.plan-chart svg');
  await settle(tab);
  if (english) await toEnglish(tab);
  console.log(`  hero fonts: lede ${(await fontsOf(tab, '.plan-title .lede')).join(', ')}; chart ${(await fontsOf(tab, '.plan-chart svg text')).join(', ')}`);
  const strip = await tab.locator('.strip').boundingBox();
  const plan = await tab.locator('.plan').boundingBox();
  // whole pixels, so the frame's right and bottom rules are inside the picture
  const x = Math.floor(strip.x);
  const y = Math.floor(strip.y);
  return tab.screenshot({ clip: { x, y, width: Math.ceil(strip.x + strip.width) - x, height: Math.ceil(plan.y + plan.height) - y } });
}

/* The generated pages, built from the current tools: the reading page from Part 1 of the source
   text, the condition page and the comparison table from the bundled teaching examples. */
function buildPages() {
  const work = fs.mkdtempSync(path.join(os.tmpdir(), 'xikari-readme-'));
  try {
      const lines = fs.readFileSync(path.join(ROOT, 'source', 'Xikari-条件结构与转化论.md'), 'utf8').split(/\r?\n/);
      const start = lines.findIndex((line) => line.startsWith('# 第一部分'));
      const end = lines.findIndex((line, index) => index > start && line.startsWith('<a id="part_2">'));
      if (start < 0 || end < 0) throw new Error('Part 1 not found in the source text');
      fs.writeFileSync(path.join(work, 'xi-kari-answer.md'), `${lines.slice(start, end).join('\n').trim()}\n`);
      const python = (script, ...rest) => execFileSync(process.env.PYTHON || 'python', [path.join(ROOT, 'scripts', script), ...rest], { cwd: ROOT, stdio: 'pipe' });
      python('render_answer.py', path.join(work, 'xi-kari-answer.md'), '--output', path.join(work, 'xi-kari-answer.html'));
      python('condition_lab.py', path.join(ROOT, 'assets', 'examples', 'condition-university.json'), '--output', path.join(work, 'condition'));
      python('comparison.py', path.join(ROOT, 'assets', 'examples', 'comparison-example.json'), '--output', path.join(work, 'comparison'), '--format', 'html');
      return work;
    } catch (error) {
      fs.rmSync(work, { recursive: true, force: true });
      throw error;
    }
  }

  async function outputs(browser, work, colorScheme) {
    const shots = {};
    // The large panel is the reading page as it opens. Each small panel is cut to the one object its page is
    // about, at the scale of the large panel: the case field of the condition page and the table of the comparison.
    for (const [key, file, width, height, object, margin] of [
      ['reading', 'xi-kari-answer.html', 1151, 683, null, 0],
      ['condition', path.join('condition', 'condition-results.html'), 720, 900, '.field', 0],
      ['comparison', path.join('comparison', 'comparison-table.html'), 760, 900, '#table-heading', 14],
    ]) {
      const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 2, colorScheme, reducedMotion: 'reduce' });
      const tab = await context.newPage();
      await tab.goto(pathToFileURL(path.join(work, file)).href, { waitUntil: 'load' });
      let clip;
      if (object) {
        const box = await tab.evaluate((selector) => {
          const node = document.querySelector(selector);
          if (!node) return null;
          window.scrollTo(0, node.getBoundingClientRect().top + window.scrollY - 12);
          const rect = node.getBoundingClientRect();
          return { x: rect.left, y: rect.top, width: rect.width };
        }, object);
        if (!box) throw new Error(`${file}: ${object} not found; update the object in capture.cjs`);
        // the panel's picture area is 610 by 290
        const span = Math.ceil(box.width) + margin * 2;
        clip = { x: Math.floor(box.x) - margin, y: Math.floor(box.y) - margin, width: span, height: Math.round(span * 290 / 610) };
      }
      await settle(tab);
      if (key === 'reading') console.log(`  reading page fonts: heading ${(await fontsOf(tab, 'h1')).join(', ')}; text ${(await fontsOf(tab, 'article p')).join(', ')}`);
      shots[key] = (await tab.screenshot(clip ? { clip } : {})).toString('base64');
      await context.close();
    }
    const context = await browser.newContext({ viewport: { width: 1920, height: 870 }, deviceScaleFactor: 1, colorScheme, reducedMotion: 'reduce' });
    const tab = await context.newPage();
    await tab.goto(`${page('outputs.html')}${colorScheme === 'dark' ? '?theme=night' : ''}`, { waitUntil: 'load' });
    await tab.evaluate((pictures) => {
      for (const [key, data] of Object.entries(pictures)) document.querySelector(`[data-shot="${key}"]`).src = `data:image/png;base64,${data}`;
    }, shots);
    await tab.waitForFunction(() => [...document.images].every((image) => image.complete && image.naturalWidth));
    await settle(tab);
    await requireFont(tab, '.panel b', 'Noto Sans SC');
    const png = await tab.locator('#figure').screenshot({ omitBackground: true });
    await context.close();
    return png;
  }

  (async () => {
    // a fixed colour profile and no GPU make repeated runs byte-identical on one machine
    const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--disable-gpu', '--force-color-profile=srgb'] });
    let work = null;
    try {
    work = wanted('outputs') ? buildPages() : null;
    for (const [name, colorScheme] of [['light', 'light'], ['dark', 'dark']]) {
      const theme = colorScheme === 'dark' ? 'night' : 'day';
      const context = await browser.newContext({ viewport: { width: 1280, height: 858 }, deviceScaleFactor: 2, colorScheme, reducedMotion: 'reduce' });
      const tab = await context.newPage();

      if (wanted('hero')) {
        keep(path.join(README, `hero-${name}.png`), await hero(tab, false),
          `Browser capture of the project page's briefing strip and plan view in the ${theme} theme with route R2 selected; ${HIDDEN}. Taken by .github/readme/src/capture.cjs.`);
      }

      if (wanted('hero-en')) {
        keep(path.join(README, `hero-en-${name}.png`), await hero(tab, true),
          `Browser capture of the project page's briefing strip and plan view in the ${theme} theme with route R2 selected; ${HIDDEN}. Its words are set in English for README.en.md; the page itself is in Chinese. Taken by .github/readme/src/capture.cjs.`);
      }

      if (wanted('handbook')) {
        await tab.goto(handbook, { waitUntil: 'load' });
        // the picture links to the handbook as a whole, so the station's own signs are left out
        await tab.addStyleTag({ content: '.xk-station__actions { display: none !important; }' });
        await tab.waitForSelector('.xk-station__rose svg');
        await settle(tab);
        keep(path.join(README, `handbook-${name}.png`), await tab.locator('.xk-station').screenshot(),
          `Browser capture of the station band on the handbook's home page in the ${theme} theme; its two signs are hidden. Taken by .github/readme/src/capture.cjs.`);
      }

      if (wanted('routes')) {
        for (const [suffix, lang, language] of [['', 'zh', 'Chinese'], ['-en', 'en', 'English']]) {
          await tab.goto(`${page('routes.html')}?lang=${lang}${colorScheme === 'dark' ? '&theme=night' : ''}`, { waitUntil: 'load' });
          await tab.waitForSelector('html[data-ready]');
          await settle(tab);
          await requireFont(tab, '.head h1', 'Noto Sans SC');
          await requireFont(tab, '.mod span', 'Noto Sans SC');
          keep(path.join(README, `routes${suffix}-${name}.png`), await tab.locator('#figure').screenshot(),
            `Rendered from .github/readme/src/routes.html in ${language}, ${theme} printing, by .github/readme/src/capture.cjs. Routes, their modules and deliverables follow the route table in SKILL.md; questions and module labels follow docs/index.html; English names follow references/english.md.`);
        }
      }
      await context.close();

      if (wanted('outputs')) {
        keep([path.join(README, `outputs-${name}.png`), path.join(ASSETS, `outputs-${name}.png`)], await outputs(browser, work, colorScheme),
          `Screenshots of pages built by the packaged tools in the ${theme} theme: the reading page from Part 1 of the source text as it opens, and, cut to the object each page is about, the case field of the condition page and the table of the comparison page, both from the bundled, explicitly fictional teaching examples. Framed by .github/readme/src/outputs.html; taken by .github/readme/src/capture.cjs.`);
      }
    }

    if (wanted('card')) {
      // one CSS pixel per device pixel, with the page's column held at 1200, so nothing is rescaled
      const context = await browser.newContext({ viewport: { width: 1440, height: 966 }, deviceScaleFactor: 1, colorScheme: 'light', reducedMotion: 'reduce' });
      const tab = await context.newPage();
      await tab.goto(project, { waitUntil: 'load' });
      await tab.addStyleTag({ content: `${HERO_CSS} .plate > * { max-width: 1200px !important; }` });
      await tab.waitForSelector('.plan-chart svg');
      const strip = await tab.locator('.strip').boundingBox();
      // the plan's row is set so that strip and plan together are exactly 630 tall
      await tab.addStyleTag({ content: `.plan { grid-template-rows: ${630 - strip.height - 1.5}px !important; }` });
      await settle(tab);
      keep(path.join(ASSETS, 'social-card.png'), await tab.screenshot({ clip: { x: strip.x, y: strip.y, width: 1200, height: 630 } }),
        `Browser capture of this page's briefing strip and plan view in the day theme with route R2 selected; ${HIDDEN}. Taken by .github/readme/src/capture.cjs.`);
      await context.close();
    }
  } finally {
    await browser.close();
    if (work) fs.rmSync(work, { recursive: true, force: true });
  }

  // everything was taken: write the files, then the hashes the project page records
  for (const { files, data } of pending) {
    for (const file of files) {
      fs.writeFileSync(file, data);
      console.log(path.relative(ROOT, file));
    }
  }
  const record = JSON.parse(fs.readFileSync(PROVENANCE, 'utf8'));
  const hash = (file) => crypto.createHash('sha256').update(fs.readFileSync(path.join(ASSETS, file))).digest('hex');
  for (const item of record.outputs.files) item.sha256 = hash(item.file);
  record.socialCard.sha256 = hash(record.socialCard.file);
  fs.writeFileSync(PROVENANCE, `${JSON.stringify(record, null, 2)}\n`);
})().catch((error) => { console.error(error.message || error); process.exit(1); });
