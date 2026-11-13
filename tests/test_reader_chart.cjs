/* Run with node tests/test_reader_chart.cjs [playwright-core module path] [python]. */
'use strict';
const assert = require('node:assert/strict');
const http = require('node:http');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { chromium } = require(process.argv[2] || path.join(__dirname, 'dom/node_modules/playwright-core'));
const python = process.argv[3] || 'python';
const root = path.resolve(__dirname, '..');
const paragraph = '这一段提供连续正文高度，用来检查航迹上的位置。\n\n';
const names = ['甲', '乙', '丙', '丁'];
const source = '# 航迹图：一篇用于检查的文章\n\n开头一句是判断。后面是说明。\n\n' + names.map((name, index) =>
  `## ${index + 1}. ${name}部分\n\n${paragraph.repeat(10 + index * 8)}${index === 1 ? '| 列 | 值 |\n| --- | --- |\n| a | 1 |\n\n### 2.1 细目\n\n' + '细目正文在这里。\n\n'.repeat(8) : ''}`).join('');
/* Two crowded tracks: sections of uneven length whose names are too long to stand side by side. */
const crowded = ['四类输出与八层责任', '全书的阅读路径', '框架与领域知识', '解释 诊断 规范选择与干涉', '按任务与风险选择入口', '强判断十问', '保护底板',
  '从一个事件进入分析', '能力边界', '共同语法与多种理解路径', '连接判断的条件', '理论骨架与论证责任'];
const lengths = [12, 8, 5, 9, 12, 4, 2, 12, 3, 12, 10, 10];
const dense = '# 密集航迹\n\n开头一段。\n\n' + crowded.map((name, index) => `## 1.${index + 1} ${name}\n\n${paragraph.repeat(lengths[index])}`).join('');
const words = ['Question and object', 'Material and evidence', 'Three explanations compared', 'Paths and objections', 'Adjustments', 'Scope', 'Counterexamples', 'Closing remarks on what remains open'];
const denseEnglish = '# Crowded track\n\nAn opening paragraph.\n\n' + words.map((name, index) =>
  `## ${index + 1}. ${name}\n\n${'A sentence of body text that gives this section some length. '.repeat([14, 3, 9, 12, 2, 2, 3, 8][index])}\n\n`).join('');
const program = 'import importlib.util,sys; s=importlib.util.spec_from_file_location("reader",sys.argv[1]); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); sys.stdout.reconfigure(encoding="utf-8"); print(m.render_document(sys.stdin.buffer.read().decode("utf-8"), lang=sys.argv[2]))';
const pages = {};
for (const [name, text, lang] of [['reader', source, 'zh'], ['dense', dense, 'zh'], ['dense-en', denseEnglish, 'en']]) {
  const made = spawnSync(python, ['-c', program, path.join(root, 'scripts/render_answer.py'), lang], { input: text, encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 });
  assert.equal(made.status, 0, made.stderr);
  pages[`/${name}.html`] = made.stdout;
}
const server = http.createServer((request, response) => {
  response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  response.end(pages[request.url] || pages['/reader.html']);
});

(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const url = `http://127.0.0.1:${server.address().port}/reader.html`;
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    await page.goto(url);
    const settled = () => page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    await settled();

    /* the track is drawn from the document's own measures */
    const drawn = await page.evaluate(() => {
      const number = value => Number(value);
      const fixes = [...document.querySelectorAll('#reader-chart svg > .ch-fix')].map(node => node.getBBox().x + node.getBBox().width / 2);
      const units = [...document.querySelectorAll('#document [data-fix]')].map(node => {
        let total = number(node.dataset.units), next = node.nextElementSibling;
        while (next && !next.hasAttribute('data-fix')) { if (next.dataset.units) total += number(next.dataset.units); next = next.nextElementSibling; }
        return total;
      });
      return {
        fixes, units,
        codes: [...document.querySelectorAll('#reader-chart .ch-code')].map(node => node.textContent),
        flown: document.querySelectorAll('#reader-chart svg > .ch-fix.is-flown').length,
        dock: document.getElementById('dock-title').textContent,
        progress: document.getElementById('reader-progress-bar').style.width,
        hidden: document.getElementById('reader-chart').closest('[aria-hidden="true"]') !== null,
        rose: document.querySelector('#reader-chart .ch-g-rose') !== null,
        wide: document.getElementById('reader-plate').clientWidth >= 780,
        locator: getComputedStyle(document.querySelector('.toolbar-here')).display !== 'none' && document.querySelector('.toolbar-here').textContent,
        entry: document.querySelector('#contents a[aria-current="location"]').textContent,
        docked: document.getElementById('track-strip').classList.contains('is-docked'),
      };
    });
    assert.equal(drawn.fixes.length, 4, 'One fix for each top-level section.');
    assert.deepEqual([...drawn.codes].sort(), ['1', '2', '3', '4'],'A fix carries the heading\'s own number.');
    assert.ok(drawn.fixes.every((x, index) => index === 0 || x > drawn.fixes[index - 1]), 'Fixes stand in reading order.');
    const legs = [drawn.fixes[1] - drawn.fixes[0], drawn.fixes[2] - drawn.fixes[1], drawn.fixes[3] - drawn.fixes[2]];
    assert.ok(Math.abs(legs[0] / legs[1] - drawn.units[0] / drawn.units[1]) < 0.06, `Leg lengths follow section lengths: ${JSON.stringify({ legs, units: drawn.units })}`);
    assert.ok(Math.abs(legs[1] / legs[2] - drawn.units[1] / drawn.units[2]) < 0.06, 'Leg lengths follow section lengths.');
    assert.equal(drawn.flown, 0);
    assert.equal(drawn.dock, '开篇');
    assert.equal(drawn.locator, '开篇', 'On arrival the bar says where the reader is.');
    assert.equal(drawn.entry, '开篇', 'On arrival the rack marks its opening strip.');
    assert.equal(parseFloat(drawn.progress), 0);
    assert.equal(drawn.hidden, true, 'The drawing is hidden from assistive technology; the rack is its text twin.');
    assert.equal(drawn.rose, drawn.wide, 'The rose is drawn only where the plate has room beside the track.');
    assert.equal(drawn.docked, false, 'While the plate is on screen the strip under the bar stays away.');

    /* reading flies the track, and once the plate has left the screen the strip under the bar carries it */
    await page.evaluate(() => {
      const heading = [...document.querySelectorAll('[data-fix]')][2];
      window.scrollTo(0, window.scrollY + heading.getBoundingClientRect().top - document.querySelector('.reader-toolbar').getBoundingClientRect().height - 60);
    });
    await settled();
    await page.waitForFunction(() => getComputedStyle(document.getElementById('track-strip')).transform === 'none');
    const flying = await page.evaluate(() => {
      const strip = document.getElementById('track-strip'), box = strip.getBoundingClientRect();
      const svg = document.querySelector('#strip-track svg').getBoundingClientRect(), go = document.getElementById('strip-go').getBoundingClientRect();
      return {
        flown: document.querySelectorAll('#reader-chart svg > .ch-fix.is-flown').length,
        here: document.querySelector('.rack-bay.is-here > a').textContent,
        behind: document.querySelectorAll('.toc-level-2.rack-bay.is-flown').length,
        entryBehind: document.querySelector('.rack-entry').classList.contains('is-flown'),
        chip: document.getElementById('dock-chip').textContent,
        plane: Number(/translate\(([\d.]+)/.exec(document.querySelector('#reader-chart .ch-plane').getAttribute('transform'))[1]),
        fixes: [...document.querySelectorAll('#reader-chart svg > .ch-fix')].map(node => node.getBBox().x + node.getBBox().width / 2),
        line: document.querySelector('#reader-chart .ch-flown').getAttribute('d'),
        percent: parseFloat(document.getElementById('reader-progress-bar').style.width),
        docked: strip.classList.contains('is-docked'),
        onScreen: box.top >= 0 && box.bottom <= window.innerHeight && getComputedStyle(strip).visibility === 'visible',
        underBar: Math.abs(box.top - document.querySelector('.reader-toolbar').getBoundingClientRect().bottom) <= 2,
        stripFixes: document.querySelectorAll('#strip-track svg > .ch-fix').length,
        stripFlown: document.querySelectorAll('#strip-track svg > .ch-fix.is-flown').length,
        stripPlane: Number(/translate\(([\d.]+)/.exec(document.querySelector('#strip-track .ch-plane').getAttribute('transform'))[1]),
        stripMarks: [...document.querySelectorAll('#strip-track svg > .ch-fix')].map(node => node.getBBox().x + node.getBBox().width / 2),
        stripChip: document.getElementById('strip-chip').textContent,
        stripName: document.getElementById('strip-name').textContent,
        stripGo: document.getElementById('strip-go').textContent,
        clear: svg.right <= go.left + 1,
        title: getComputedStyle(document.querySelector('.toolbar-doc')).display !== 'none' && document.querySelector('.toolbar-doc').textContent,
      };
    });
    assert.equal(flying.flown, 3);
    assert.equal(flying.here, '3. 丙部分');
    assert.equal(flying.behind, 2);
    assert.equal(flying.entryBehind, true, 'The opening strip is behind the reader once a section is reached.');
    assert.equal(flying.chip, '3');
    assert.ok(flying.plane >= flying.fixes[2] - 1 && flying.plane < flying.fixes[3], `The aircraft is on the third leg: ${JSON.stringify(flying)}`);
    assert.ok(flying.line.startsWith('M'), 'The flown part of the track is drawn behind the aircraft.');
    assert.ok(flying.percent > 30 && flying.percent < 75);
    assert.equal(flying.docked, true, 'The strip docks once the plate has scrolled away.');
    assert.equal(flying.onScreen && flying.underBar, true, 'The docked strip sits on screen directly under the bar.');
    assert.equal(flying.stripFixes, 4);
    assert.equal(flying.stripFlown, 3);
    assert.ok(flying.stripPlane >= flying.stripMarks[2] - 1 && flying.stripPlane < flying.stripMarks[3], `The strip flies the same leg: ${JSON.stringify(flying)}`);
    assert.equal(flying.stripChip, '3');
    assert.equal(flying.stripName, '丙部分');
    assert.match(flying.stripGo, /^\d+% · 余 \d+ 分钟$/);
    assert.equal(flying.clear, true, 'The strip track stops before the readout.');
    assert.equal(flying.title, '航迹图：一篇用于检查的文章', 'Once the title has left the screen the bar carries it.');

    /* a fix is a way in, on the plate and on the strip */
    await page.locator('#strip-track a').nth(3).click();
    await settled();
    assert.equal(await page.locator('#contents a[aria-current="location"]').textContent(), '4. 丁部分');
    await page.locator('#reader-chart a').nth(1).click();
    await settled();
    assert.equal(await page.locator('#contents a[aria-current="location"]').textContent(), '2. 乙部分');
    assert.equal(await page.evaluate(() => document.activeElement.dataset.sectionTitle), '2. 乙部分');

    /* search hits are printed on both tracks and counted on the rack, whose last column then names hits */
    assert.equal(await page.locator('#rack-unit').textContent(), '字');
    await page.locator('#reader-search').fill('细目');
    await page.locator('#reader-search').press('Enter');
    await settled();
    const found = await page.evaluate(() => ({
      marks: document.querySelectorAll('#reader-chart .ch-found').length,
      stripMarks: document.querySelectorAll('#strip-track .ch-found').length,
      chips: [...document.querySelectorAll('.toc-found')].map(node => [node.closest('.rack-bay').querySelector('a').textContent, node.textContent]),
      status: document.getElementById('search-status').textContent,
      unit: document.getElementById('rack-unit').textContent,
      lengths: [...document.querySelectorAll('.rack > .rack-bay > .toc-min')].filter(node => getComputedStyle(node).display !== 'none').length,
    }));
    assert.equal(found.status, '1 / 9');
    assert.ok(found.marks >= 1);
    assert.ok(found.stripMarks >= 1, 'Hits are printed on the strip under the bar as well.');
    assert.deepEqual(found.chips, [['2. 乙部分', '9']]);
    assert.equal(found.unit, '命中', 'While searching the column is headed by what it counts.');
    assert.equal(found.lengths, 0, 'While searching no strip shows a length under the hits heading.');
    await page.locator('#reader-search').press('Escape');
    assert.equal(await page.locator('#reader-chart .ch-found, #strip-track .ch-found, .toc-found').count(), 0);
    assert.equal(await page.locator('#rack-unit').textContent(), '字');

    /* the track is a ruler: pressing it goes to that distance along the text */
    await page.evaluate(() => window.scrollTo(0, 0));
    await settled();
    const ruler = await page.locator('#reader-chart .ch-ruler').boundingBox();
    await page.mouse.move(ruler.x + ruler.width * 0.5, ruler.y + 5);
    assert.match(await page.locator('#dock-left').textContent(), /^约 [\d,.]+ 字处$/, 'Pointing at the track reads the distance under the pointer.');
    await page.mouse.click(ruler.x + ruler.width * 0.5, ruler.y + 5);
    await settled();
    const sought = await page.evaluate(() => parseFloat(document.getElementById('reader-progress-bar').style.width));
    assert.ok(Math.abs(sought - 50) < 4, `Pressing the middle of the track goes to the middle of the text: ${sought}`);

    /* keyboard: ] and [ step between sections */
    await page.evaluate(() => { document.activeElement.blur(); window.scrollTo(0, 0); });
    await settled();
    await page.keyboard.press(']');
    await settled();
    assert.equal(await page.locator('#contents a[aria-current="location"]').textContent(), '1. 甲部分');
    await page.keyboard.press(']');
    await settled();
    assert.equal(await page.locator('#contents a[aria-current="location"]').textContent(), '2. 乙部分');
    await page.keyboard.press('[');
    await settled();
    assert.equal(await page.locator('#contents a[aria-current="location"]').textContent(), '1. 甲部分');

    /* the place last read is kept in this browser and offered on return */
    await page.evaluate(() => {
      const heading = [...document.querySelectorAll('[data-fix]')][3];
      window.scrollTo(0, window.scrollY + heading.getBoundingClientRect().top - 70);
    });
    await page.waitForTimeout(900);
    await page.goto(url);
    await settled();
    assert.equal(await page.locator('#resume-reading').isVisible(), true);
    assert.match(await page.locator('#resume-reading').getAttribute('title'), /丁部分$/);
    await page.locator('#resume-reading').click();
    await settled();
    assert.equal(await page.locator('#contents a[aria-current="location"]').textContent(), '4. 丁部分');
    assert.equal(await page.locator('#resume-reading').isVisible(), false);

    /* print keeps the strip of facts and the track; the stylesheet itself drops everything that says where a reader was */
    await page.emulateMedia({ media: 'print' });
    assert.equal(await page.locator('#reader-dock').isVisible(), false);
    assert.equal(await page.locator('#reader-chart svg').isVisible(), true);
    assert.equal(await page.locator('.reader-toolbar').isVisible(), false);
    assert.equal(await page.locator('#track-strip').isVisible(), false);
    const printed = await page.evaluate(() => {
      const shown = selector => [...document.querySelectorAll(selector)].filter(node => getComputedStyle(node).display !== 'none').length;
      return {
        rose: shown('#reader-chart .ch-g-rose'), flownKey: shown('#reader-chart .ch-key-flown'), plane: shown('#reader-chart .ch-plane'),
        flown: shown('#reader-chart .ch-flown'), fixes: shown('#reader-chart svg > .ch-fix'), frame: shown('#reader-chart .ch-key.only-print'),
      };
    });
    assert.deepEqual(printed, { rose: 0, flownKey: 0, plane: 0, flown: 0, fixes: 4, frame: 1 });
    await page.emulateMedia({ media: 'screen' });
    assert.deepEqual(errors, []);
    await page.close();

    /* on a phone the track runs down the sheet with its names beside it, and the strip under the bar still follows the reading */
    const phone = await browser.newPage({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce', hasTouch: true });
    phone.on('pageerror', error => errors.push(error.message));
    await phone.goto(url);
    const rested = () => phone.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    await rested();
    const narrow = await phone.evaluate(() => {
      const svg = document.querySelector('#reader-chart svg');
      const ys = [...svg.querySelectorAll(':scope > .ch-fix')].map(node => node.getBBox().y + node.getBBox().height / 2);
      const sizes = [...svg.querySelectorAll('.ch-name, .ch-code, .ch-note')].map(node => parseFloat(getComputedStyle(node).fontSize));
      const box = svg.getBoundingClientRect();
      const texts = [...svg.querySelectorAll('text')].map(node => node.getBoundingClientRect());
      return {
        chart: document.getElementById('reader-chart').hidden,
        ys, names: [...svg.querySelectorAll('.ch-name')].map(node => node.textContent).filter(Boolean),
        codes: [...svg.querySelectorAll('.ch-code')].map(node => node.textContent).sort(),
        smallest: Math.min(...sizes),
        inside: texts.every(text => text.left >= box.left - 1 && text.right <= box.right + 1),
        ways: [...svg.querySelectorAll('a .ch-hit')].map(node => node.getBoundingClientRect().height),
        rose: svg.querySelector('.ch-g-rose') !== null,
        height: box.height,
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      };
    });
    assert.equal(narrow.chart, false, 'A phone gets the track, recomposed, not a reduced substitute.');
    assert.equal(narrow.ys.length, 4);
    assert.ok(narrow.ys.every((y, index) => index === 0 || y > narrow.ys[index - 1]), 'On a phone the fixes run down the sheet in reading order.');
    assert.ok(['开篇', '文末', '丙部分', '丁部分'].every(name => narrow.names.includes(name)), `Names stand beside their fixes: ${narrow.names}`);
    assert.ok(narrow.names.every(name => ['开篇', '文末', '甲部分', '乙部分', '丙部分', '丁部分'].includes(name)) && new Set(narrow.names).size === narrow.names.length, `Each name is lettered once: ${narrow.names}`);
    assert.deepEqual(narrow.codes, ['1', '2', '3', '4']);
    assert.ok(narrow.smallest >= 11.5, `Lettering on the phone track stays legible: ${narrow.smallest}`);
    assert.equal(narrow.inside, true, 'No lettering is cut by the edge of the plate.');
    assert.ok(narrow.ways.length === 4 && narrow.ways.every(height => height >= 24), `Every fix can be tapped: ${narrow.ways}`);
    assert.equal(narrow.rose, false);
    assert.ok(narrow.height <= 420, `The phone track leaves the opening sentence within reach: ${narrow.height}`);
    assert.ok(narrow.overflow <= 0, 'The page must not scroll sideways on a phone.');
    await phone.locator('#reader-chart a').nth(2).tap();
    await rested();
    const tapped = await phone.evaluate(() => ({
      current: document.querySelector('#contents a[aria-current="location"]').textContent,
      docked: document.getElementById('track-strip').classList.contains('is-docked'),
      flown: document.querySelectorAll('#strip-track svg > .ch-fix.is-flown').length,
      name: document.getElementById('strip-name').textContent,
      go: document.getElementById('strip-go').textContent,
      fits: document.getElementById('track-strip').scrollWidth <= document.getElementById('track-strip').clientWidth + 1,
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    }));
    assert.equal(tapped.current, '3. 丙部分');
    assert.equal(tapped.docked, true);
    assert.equal(tapped.flown, 3);
    assert.equal(tapped.name, '丙部分');
    assert.match(tapped.go, /^\d+% · 余 \d+ 分钟$/);
    assert.equal(tapped.fits, true, 'The strip under the bar fits a phone.');
    assert.ok(tapped.overflow <= 0);
    assert.deepEqual(errors, []);
    await phone.close();

    /* on a crowded track a name stands over the fix it names: centred beside the track, or on a leader, or left to the rack */
    for (const [file, width, english] of [['dense', 1440, false], ['dense', 1280, false], ['dense', 1040, false], ['dense-en', 1440, true], ['dense-en', 1100, true]]) {
      const crowd = await browser.newPage({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
      crowd.on('pageerror', error => errors.push(error.message));
      await crowd.goto(url.replace('reader.html', `${file}.html`));
      await crowd.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      const lettered = await crowd.evaluate(() => {
        const svg = document.querySelector('#reader-chart svg'), frame = svg.getBoundingClientRect();
        const labels = [...document.querySelectorAll('#document [data-fix]')].map(node => node.dataset.label);
        const fixes = [...svg.querySelectorAll(':scope > .ch-fix')].map((node, index) => {
          const box = node.getBoundingClientRect();
          return { x: box.left + box.width / 2 - frame.left, label: labels[index] };
        });
        const leaders = [...svg.querySelectorAll('.ch-leader')].map(node => node.getBoundingClientRect().left + node.getBoundingClientRect().width / 2 - frame.left);
        const rose = svg.querySelector('.ch-g-rose');
        const ends = [12, rose ? rose.getBoundingClientRect().left - frame.left - 10 : frame.width - 12];
        const ownText = new Set([svg.querySelector('.ch-g-end .ch-name')]);
        const names = [...svg.querySelectorAll('.ch-name')].filter(node => node.textContent && !ownText.has(node)).slice(1).map(node => {
          const box = node.getBoundingClientRect();
          return { text: node.textContent, left: box.left - frame.left, right: box.right - frame.left, top: box.top, bottom: box.bottom };
        });
        return { fixes, leaders, ends, names };
      });
      const context = `${file} at ${width}px`;
      assert.ok(lettered.names.length >= 3, `${context}: a crowded track still letters several names (${lettered.names.length})`);
      for (const name of lettered.names) {
        const centre = (name.left + name.right) / 2, stem = name.text.replace(/…$/, '');
        const centred = lettered.fixes.find(fix => Math.abs(fix.x - centre) <= 1.5);
        const led = lettered.leaders.filter(x => x >= name.left - 1 && x <= name.right + 1).map(x => lettered.fixes.find(fix => Math.abs(fix.x - x) <= 1.5)).find(Boolean);
        const atEnd = lettered.fixes.find(fix => fix.x >= name.left && fix.x <= name.right && (name.left - lettered.ends[0] <= 8 || lettered.ends[1] - name.right <= 8));
        const owner = centred || led || atEnd;
        assert.ok(owner, `${context}: "${name.text}" stands over no fix of its own: ${JSON.stringify({ name, fixes: lettered.fixes.map(fix => Math.round(fix.x)) })}`);
        assert.ok(owner.label.startsWith(stem), `${context}: "${name.text}" stands over the fix named "${owner.label}"`);
        if (name.text !== owner.label) {
          assert.ok(name.text.endsWith('…'), `${context}: a shortened name says so: "${name.text}"`);
          if (english) assert.equal(owner.label[stem.length], ' ', `${context}: "${name.text}" is cut inside a word of "${owner.label}"`);
        }
      }
      const overlaps = lettered.names.flatMap((a, index) => lettered.names.slice(index + 1).filter(b => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom).map(b => [a.text, b.text]));
      assert.deepEqual(overlaps, [], `${context}: no two names are lettered over each other`);
      await crowd.close();
    }
    assert.deepEqual(errors, []);

    /* with motion allowed the theme switch and the arrival animation run without error */
    const moving = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    moving.on('pageerror', error => errors.push(error.message));
    await moving.goto(url);
    await moving.locator('#theme-toggle').click();
    await moving.waitForTimeout(900);
    assert.equal(await moving.evaluate(() => document.documentElement.dataset.theme), 'night');
    assert.equal(await moving.evaluate(() => document.documentElement.classList.contains('theme-flip')), false);
    assert.deepEqual(errors, []);
    await moving.close();
  } finally {
    await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
  console.log('Reader chart passed: proportional track, flight by scrolling, docked strip, names over their own fixes, fixes as links, search hits, keyboard steps, resume, print, phone track, theme switch.');
})().catch(error => { server.close(); console.error(error.stack); process.exitCode = 1; });
