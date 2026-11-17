/* Run after the handbook build: node tests/test_handbook_controls.cjs [playwright-core path] [optional preview URL]. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium } = require(process.argv[2] || path.join(__dirname, 'dom/node_modules/playwright-core'));
const built = path.resolve(__dirname, '../docs/handbook');
const prefix = '/xi-kari-skill/handbook/';
const mime = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.json': 'application/json', '.css': 'text/css', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.png': 'image/png' };
const server = http.createServer((request, response) => {
  let pathname;
  try { pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname); }
  catch { response.writeHead(400).end(); return; }
  if (!pathname.startsWith(prefix)) { response.writeHead(404).end(); return; }
  let file = path.resolve(built, pathname.slice(prefix.length));
  if (file !== built && !file.startsWith(built + path.sep)) { response.writeHead(403).end(); return; }
  if (pathname.endsWith('/')) file = path.join(file, 'index.html');
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) { response.writeHead(404).end(); return; }
  response.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(response);
});

async function checkTextFits(locator) {
  const clipped = await locator.evaluateAll(elements => elements.flatMap(element => {
    const box = element.getBoundingClientRect();
    const cell = element.parentElement.getBoundingClientRect();
    const isButton = element.tagName === 'BUTTON';
    const limit = isButton ? box : cell;
    const outside = (rect, bounds) => rect.left < bounds.left - 1 || rect.right > bounds.right + 1 || rect.top < bounds.top - 1 || rect.bottom > bounds.bottom + 1;
    if (isButton && outside(box, cell)) return [element.textContent];
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      if (!walker.currentNode.textContent.trim()) continue;
      const range = document.createRange();
      range.selectNodeContents(walker.currentNode);
      if ([...range.getClientRects()].some(rect => outside(rect, limit))) return [element.textContent];
    }
    return [];
  }));
  assert.deepEqual(clipped, [], 'Complete labels must fit their visible control or information cell.');
}

async function checkRadioSelection(radios, selected) {
  const state = await radios.evaluateAll(elements => elements.map(element => ({
    checked: element.getAttribute('aria-checked'), tabIndex: element.tabIndex, focused: document.activeElement === element
  })));
  state.forEach((item, index) => {
    assert.equal(item.checked, String(index === selected));
    assert.equal(item.tabIndex, index === selected ? 0 : -1, 'Each radio group has one tab stop.');
  });
  assert.equal(state[selected].focused, true, 'Arrow navigation moves focus with selection.');
}

(async () => {
  let browser;
  try {
    let base = process.argv[3];
    if (!base) {
      assert.ok(fs.existsSync(path.join(built, 'en/concepts/feedback.html')), 'Build the bilingual handbook before this check.');
      await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
      base = `http://127.0.0.1:${server.address().port}${prefix}`;
    }
    base = base.replace(/\/?$/, '/');
    const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || (fs.existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
    browser = await chromium.launch({ ...(executablePath ? { executablePath } : { channel: 'chrome' }), headless: true });
    for (const width of [320, 390]) for (const locale of ['', 'en/']) {
      const page = await browser.newPage({ viewport: { width, height: 900 }, hasTouch: true, colorScheme: width === 320 ? 'dark' : 'light', reducedMotion: 'reduce' });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      async function visit(route) {
        const response = await page.goto(base + locale + route, { waitUntil: 'networkidle' });
        assert.equal(response.status(), 200);
        await page.evaluate(() => document.fonts.ready);
      }

      await visit('concepts/feedback.html');
      const feedback = page.locator('.xk-fb');
      const tabs = feedback.getByRole('tab');
      await checkTextFits(tabs);
      await tabs.nth(1).tap();
      assert.equal(await tabs.nth(1).getAttribute('aria-selected'), 'true');
      await tabs.nth(1).focus();
      for (const [key, selected] of [['ArrowRight', 2], ['Home', 0], ['End', 2], ['ArrowLeft', 1]]) {
        await page.keyboard.press(key);
        assert.equal(await tabs.nth(selected).getAttribute('aria-selected'), 'true');
        assert.equal(await tabs.nth(selected).evaluate(element => document.activeElement === element), true);
        const panel = feedback.getByRole('tabpanel');
        assert.equal(await panel.getAttribute('aria-labelledby'), await tabs.nth(selected).getAttribute('id'));
      }
      await checkTextFits(tabs);

      await visit('concepts/joint-feasibility.html');
      const joint = page.locator('.xk-jf');
      const groups = joint.getByRole('radiogroup');
      const deadline = groups.nth(0).getByRole('radio');
      const capacity = groups.nth(1).getByRole('radio');
      await checkTextFits(joint.getByRole('radio'));
      assert.equal(await joint.locator('.xk-jf__result .is-yes').count(), 0);
      await deadline.nth(1).tap();
      assert.equal(await joint.locator('.xk-jf__result .is-yes').count(), 1);
      await capacity.nth(0).tap();
      assert.equal(await joint.locator('.xk-jf__result .is-yes').count(), 0);
      await capacity.nth(0).focus();
      for (const [key, selected] of [['ArrowRight', 1], ['ArrowDown', 2], ['ArrowRight', 0], ['ArrowLeft', 2], ['Home', 0], ['End', 2], ['ArrowUp', 1]]) {
        await page.keyboard.press(key);
        await checkRadioSelection(capacity, selected);
        assert.equal(await joint.locator('.xk-jf__result .is-yes').count(), selected > 0 ? 1 : 0);
      }
      await deadline.nth(0).focus();
      await page.keyboard.press('Space');
      assert.equal(await joint.locator('.xk-jf__result .is-yes').count(), 0);
      await page.keyboard.press('End');
      await checkRadioSelection(deadline, 1);
      assert.equal(await joint.locator('.xk-jf__result .is-yes').count(), 1);
      await page.keyboard.press('Home');
      await checkRadioSelection(deadline, 0);
      await deadline.nth(1).focus();
      await page.keyboard.press('Enter');
      assert.equal(await joint.locator('.xk-jf__result .is-yes').count(), 1);

      await visit('concepts/prediction.html');
      const prediction = page.locator('.xk-pr');
      const slider = prediction.getByRole('slider');
      const bars = prediction.locator('.xk-pr__bar');
      assert.equal(await bars.nth(1).locator('output').innerText(), '0.450');
      await slider.focus();
      for (const [key, value, output] of [['Home', '0', '0.100'], ['End', '100', '0.800'], ['ArrowLeft', '99', '0.793']]) {
        await page.keyboard.press(key);
        assert.equal(await slider.inputValue(), value);
        assert.equal(await bars.nth(1).locator('output').innerText(), output);
        assert.equal(await bars.nth(0).locator('output').innerText(), '0.200');
        assert.equal(await prediction.locator('.xk-pr__calc strong').innerText(), output);
      }

      await visit('theory/part-03.html');
      await checkTextFits(page.locator('.xk-tb__value'));
      assert.deepEqual(errors, [], `No browser errors for ${locale || 'zh/'} at ${width}px.`);
      console.log(`Handbook controls passed: ${locale || 'zh/'} at ${width}px; complete labels, radio/tab keys, slider feedback and page information.`);
      await page.close();
    }
  } finally {
    if (browser) await browser.close();
    if (server.listening) await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
