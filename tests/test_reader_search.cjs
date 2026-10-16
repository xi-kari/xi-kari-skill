/* Run with node tests/test_reader_search.cjs [playwright-core module path] [python]. */
'use strict';
const assert = require('node:assert/strict');
const http = require('node:http');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { chromium } = require(process.argv[2] || path.join(__dirname, 'dom/node_modules/playwright-core'));
const python = process.argv[3] || 'python';
const root = path.resolve(__dirname, '..');
const source = '# 长文搜索\n\n## 文本\n\nAlpha\nbeta is continuous visible prose.\n\nGamma   delta is also continuous prose.\n\nVisual **inline** match.\n\nAcross [inline  ](#document)   spaces.\n\nAlpha **beta** returns.\n\nALPHA   BETA appears again.\n\n## 段落边界\n\nBoundary first\n\nsecond boundary\n\n| Left | Right |\n| --- | --- |\n| Edge | Join |\n\n## 原式和代码\n\nBefore \\(math  space\\) after.\n\n```text\ncode  spacing\nsecond row\n```\n';
const render = spawnSync(python, ['-c', 'import importlib.util,sys; s=importlib.util.spec_from_file_location("reader",sys.argv[1]); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); sys.stdout.reconfigure(encoding="utf-8"); print(m.render_document(sys.stdin.buffer.read().decode("utf-8")))', path.join(root, 'scripts/render_answer.py')], { input: source, encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 });
assert.equal(render.status, 0, render.stderr);
const server = http.createServer((request, response) => {
  response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  response.end(render.stdout);
});

(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
      const page = await browser.newPage({ viewport });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(`http://127.0.0.1:${server.address().port}/reader.html`);
      const article = page.locator('#document');
      const original = await article.textContent();
      const formulas = await page.locator('.katex').count();
      const search = page.locator('#reader-search');
      const status = page.locator('#search-status');
      if (await page.locator('#search-toggle').isVisible()) await page.locator('#search-toggle').click();
      async function find(query, expected, message) {
        await search.fill(query);
        await search.press('Enter');
        assert.equal(await status.innerText(), expected, `${viewport.width}px: ${message}`);
        assert.equal(await article.textContent(), original, 'Highlighting must preserve the original text, including whitespace.');
        assert.equal(await page.locator('.katex').count(), formulas, 'Searching must preserve rendered formulas.');
      }
      assert.equal(await page.locator('#document > p').first().innerText(), 'Alpha beta is continuous visible prose.');
      await find('Alpha beta', '1 / 3', 'A visible phrase must match across soft line breaks, inline emphasis, and collapsed spaces.');
      assert.deepEqual(await page.locator('mark.current-match').allTextContents(), ['Alpha\nbeta']);
      await search.press('Enter');
      assert.equal(await status.innerText(), '2 / 3');
      assert.deepEqual(await page.locator('mark.current-match').allTextContents(), ['Alpha ', 'beta']);
      await search.press('Shift+Enter');
      assert.equal(await status.innerText(), '1 / 3');
      await search.press('Shift+Enter');
      assert.equal(await status.innerText(), '3 / 3', 'Previous match must wrap around.');
      assert.deepEqual(await page.locator('mark.current-match').allTextContents(), ['ALPHA   BETA']);
      await page.locator('#next-match').click();
      assert.equal(await status.innerText(), '1 / 3', 'Next match must wrap around.');
      await page.locator('#previous-match').click();
      assert.equal(await status.innerText(), '3 / 3');
      await find('Gamma delta', '1 / 1', 'Repeated prose spaces must match their visible single space.');
      assert.deepEqual(await page.locator('mark.current-match').allTextContents(), ['Gamma   delta']);
      await find('Visual inline match', '1 / 1', 'A phrase must span inline emphasis.');
      await find('Across inline spaces', '1 / 1', 'Whitespace must also collapse across text nodes.');
      assert.deepEqual(await page.locator('mark.current-match').allTextContents(), ['Across ', 'inline  ', '   spaces']);
      await find('first second', '没有匹配', 'Separate paragraphs must not become one phrase.');
      await find('EdgeJoin', '没有匹配', 'Adjacent table cells must not become one word.');
      await find('Edge Join', '没有匹配', 'Adjacent table cells must not become one phrase.');
      await find('code spacing', '没有匹配', 'Code spaces must remain significant.');
      await find('code  spacing', '1 / 1', 'Code must remain searchable with its exact spaces.');
      assert.deepEqual(await page.locator('mark.current-match').allTextContents(), ['code  spacing']);
      await find('spacing second', '没有匹配', 'A code line break must not become a prose space.');
      await find('math space', '没有匹配', 'Formula source spaces must remain significant.');
      await find('math  space', '1 / 1', 'Formula source must remain searchable with its exact spaces.');
      assert.equal(await page.locator('.reader-math.current-match').count(), 1);
      await find('Before \\(math  space\\)', '1 / 1', 'A phrase may include an inline formula without changing its source.');
      assert.equal(await page.locator('.reader-math.current-match').count(), 1);
      await find('Alpha beta', '1 / 3', 'Repeated searches must preserve matches.');
      await search.press('Escape');
      assert.equal(await status.textContent(), '');
      assert.equal(await page.locator('mark[data-match], [data-math-match], .current-match').count(), 0);
      assert.equal(await article.textContent(), original, 'Clearing highlights must restore the original text exactly.');
      assert.equal(await page.locator('#previous-match').isDisabled(), true);
      assert.equal(await page.locator('#next-match').isDisabled(), true);
      assert.deepEqual(errors, []);
      console.log(JSON.stringify({ viewport, phraseMatches: 3, whitespaceAndBlockBoundaries: 'passed', sourcePreservation: 'passed', keyboardNavigation: 'passed' }));
      await page.close();
    }
    console.log('Reader search passed: desktop/mobile soft lines, collapsed spaces, inline emphasis, paragraph/table boundaries, exact code/math, source preservation, and keyboard navigation.');
  } finally {
    await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { server.close(); console.error(error.stack); process.exitCode = 1; });
