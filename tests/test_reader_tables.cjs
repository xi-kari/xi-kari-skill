/* Run with node tests/test_reader_tables.cjs [playwright-core module path] [python]. */
'use strict';
const assert = require('node:assert/strict');
const http = require('node:http');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { chromium } = require(process.argv[2] || path.join(__dirname, 'dom/node_modules/playwright-core'));
const python = process.argv[3] || 'python';
const root = path.resolve(__dirname, '..');
const row = (cells) => `| ${cells.join(' | ')} |\n`;
const table = (heads, lines) => row(heads) + row(heads.map(() => '---')) + lines.map(row).join('') + '\n';
/* A comparison table of the kind a long study ends with: seven columns, long heads, sentences in the cells. */
const mapping = table(
  ['#', '领域概念或方法（出处）', '理论中用得上的区别（出处）', '身份', '保留了什么', '丢了什么', '何时对应不成立'],
  [1, 2, 3, 4, 5, 6].map((number) => [number, '回购折扣、保证金（Gorton–Metrick 2009，第 12—14 页）', '抵押品市价、可贷额度、实际余额、回收四个数（§10.6.2；D.18）', '部分对应（定义层）',
    '折扣上升等于融资能力下降', '折扣上升的原因（借方还是贷方）', '折扣反映出借方自身紧缩时，因果方向相反']));
const source = '# 表格检查\n\n开头一句是判断。\n\n## 一、三列\n\n'
  + table(['材料', '能支持', '不能支持'], [['登记', '两期各有多少人结业', '学到了多少']])
  + '## 二、四列\n\n'
  + table(['安排', '各轮产出', '累计产出', '期末技能'], [['集中', '2、3、4、5', '14', '(6,0)'], ['交替', '2、0、3、1', '6', '(4,2)']])
  + '## 三、七列\n\n' + mapping + '结尾一段。\n';
const program = 'import importlib.util,sys; s=importlib.util.spec_from_file_location("reader",sys.argv[1]); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); sys.stdout.reconfigure(encoding="utf-8"); print(m.render_document(sys.stdin.buffer.read().decode("utf-8"), lang="zh"))';
const made = spawnSync(python, ['-c', program, path.join(root, 'scripts/render_answer.py')], { input: source, encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 });
assert.equal(made.status, 0, made.stderr);
const server = http.createServer((request, response) => {
  response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  response.end(made.stdout);
});

(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const url = `http://127.0.0.1:${server.address().port}/tables.html`;
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const measure = async (width, height) => {
      const page = await browser.newPage({ viewport: { width, height }, reducedMotion: 'reduce' });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(url);
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      const frames = await page.evaluate(() => [...document.querySelectorAll('article .table-scroll')].map((frame) => {
        const grid = frame.querySelector('table');
        const head = grid.querySelector('th:nth-child(2)');
        return {
          columns: grid.rows[0].cells.length,
          cut: frame.scrollWidth - frame.clientWidth,
          frame: frame.clientWidth,
          font: parseFloat(getComputedStyle(grid).fontSize),
          headWraps: getComputedStyle(head).whiteSpace !== 'nowrap',
          lastColumn: grid.rows[1].cells[grid.rows[1].cells.length - 1].getBoundingClientRect().width,
        };
      }));
      const sideways = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      await page.close();
      assert.deepEqual(errors, []);
      return { frames, sideways };
    };

    for (const [width, height] of [[1280, 900], [1024, 800], [1440, 900]]) {
      const { frames, sideways } = await measure(width, height);
      assert.deepEqual(frames.map(frame => frame.columns), [3, 4, 7]);
      const [three, four, seven] = frames;
      assert.ok(seven.cut <= 1, `${width}px: the seven-column table is cut by ${seven.cut}px`);
      assert.ok(seven.lastColumn >= 70, `${width}px: the last column keeps a readable width (${seven.lastColumn}px)`);
      assert.ok(seven.font < four.font, `${width}px: a dense table is set smaller than an ordinary one`);
      assert.ok(seven.font >= 13, `${width}px: dense table text stays readable (${seven.font}px)`);
      assert.equal(seven.headWraps, true, `${width}px: long heads of a dense table may wrap`);
      assert.equal(four.font, three.font, `${width}px: tables under six columns keep the ordinary size`);
      assert.equal(four.headWraps, false, `${width}px: heads of ordinary tables stay on one line`);
      assert.ok(four.cut <= 1 && three.cut <= 1, `${width}px: ordinary tables are not cut`);
      assert.ok(four.frame > three.frame, `${width}px: four columns or more take the wide column`);
      assert.ok(sideways <= 1, `${width}px: the page does not scroll sideways`);
    }

    /* On a phone a dense table may scroll inside its own frame; the page itself must not. */
    const phone = await measure(390, 800);
    assert.ok(phone.sideways <= 1, 'phone: the page does not scroll sideways');
    assert.ok(phone.frames[2].font >= 13, 'phone: dense table text stays readable');

    /* Print cannot scroll: at the width of the A4 text area (174 mm, about 657 px) no table may stick out of the article. */
    const sheet = await browser.newPage({ viewport: { width: 657, height: 900 } });
    await sheet.emulateMedia({ media: 'print' });
    await sheet.goto(url);
    const printed = await sheet.evaluate(() => {
      const edge = document.querySelector('article').getBoundingClientRect().right;
      return [...document.querySelectorAll('article table')].map(grid => ({
        columns: grid.rows[0].cells.length,
        out: Math.round(grid.getBoundingClientRect().right - edge),
        font: parseFloat(getComputedStyle(grid).fontSize),
      }));
    });
    await sheet.close();
    for (const grid of printed) assert.ok(grid.out <= 1, `print: the ${grid.columns}-column table sticks out by ${grid.out}px`);
    assert.ok(printed[2].font < printed[1].font && printed[2].font >= 10, 'print: a dense table is set smaller, and not below 7.5pt');
  } finally {
    await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
  console.log('Reader tables passed: a seven-column table fits the wide column at desktop widths and the text area in print, ordinary tables keep their size, no sideways page scroll on a phone.');
})().catch(error => { server.close(); console.error(error.stack); process.exitCode = 1; });
