/* Run after the handbook build: node tests/test_handbook_locale.cjs [playwright-core path] [optional preview URL]. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium } = require(process.argv[2] || path.join(__dirname, 'dom/node_modules/playwright-core'));
const built = path.resolve(__dirname, '../docs/handbook');
const englishLessons = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../website/content/en/section-lessons.json'), 'utf8')).lessons;
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
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) {
    const fallback = path.join(built, '404.html');
    if (!path.extname(file) || path.extname(file) === '.html') {
      response.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8' });
      fs.createReadStream(fallback).pipe(response);
    } else response.writeHead(404).end();
    return;
  }
  response.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(response);
});
(async () => {
  let base = process.argv[3];
  if (!base) {
    assert.ok(fs.existsSync(path.join(built, 'en/theory/part-03.html')), 'Build the bilingual handbook before this check.');
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    base = `http://127.0.0.1:${server.address().port}${prefix}`;
  }
  base = base.replace(/\/?$/, '/');
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || (fs.existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
  const browser = await chromium.launch({ ...(executablePath ? { executablePath } : { channel: 'chrome' }), headless: true });
  try {
    for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
      const page = await browser.newPage({ viewport });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      async function switchLanguage() {
        const toolbarLink = page.locator('.xk-tool--language');
        if (await toolbarLink.isVisible()) {
          await toolbarLink.click();
          return;
        }
        await page.locator('.xk-topbar__menu').click();
        const drawerLink = page.locator('#xk-nav .xk-nav-language');
        await drawerLink.waitFor({ state: 'visible' });
        assert.equal(await drawerLink.getAttribute('href'), await toolbarLink.getAttribute('href'),
          'The phone language entry must preserve the same source section or lesson.');
        await drawerLink.focus();
        await page.keyboard.press('Enter');
      }
      async function checkHomeLayout() {
        await page.evaluate(() => document.fonts.ready);
        const geometry = await page.locator('.xk-idstrip').evaluate(strip => ({
          tops: [...strip.children].map(cell => cell.getBoundingClientRect().top),
          nextId: strip.nextElementSibling?.id
        }));
        assert.equal(geometry.nextId, 'map', 'The book map must follow the identity strip.');
        if (viewport.width >= 1024) {
          assert.ok(geometry.tops.every(top => Math.abs(top - geometry.tops[0]) < 1),
            'Desktop identity cells must stay together in one row.');
        }
      }
      async function checkHeaderLayout() {
        const geometry = await page.locator('.xk-topbar__inner').evaluate(header => {
          const rect = element => { const box = element.getBoundingClientRect(); return { x: box.x, right: box.right }; };
          const brand = header.querySelector('.xk-brand');
          return {
            controls: [...header.querySelectorAll(':scope > button, :scope > a, .xk-topbar__tools > a, .xk-topbar__tools > button')]
              .filter(element => element.getClientRects().length).map(element => ({ label: element.getAttribute('aria-label') || element.textContent, ...rect(element) })),
            brand: rect(brand), title: rect(brand.querySelector('.xk-brand__name'))
          };
        });
        for (let i = 1; i < geometry.controls.length; i++)
          assert.ok(geometry.controls[i - 1].right <= geometry.controls[i].x + 0.5,
            `Top-bar controls must not overlap at ${viewport.width}px: ${JSON.stringify(geometry.controls)}`);
        assert.ok(geometry.title.right <= geometry.brand.right + 0.5,
          `The visible brand title must stay inside its link instead of overlapping the language button at ${viewport.width}px.`);
      }
      await page.goto(base);
      await page.locator('.xk-station').waitFor({ state: 'visible' });
      await checkHeaderLayout();
      await checkHomeLayout();
      await page.goto(base + 'en/');
      await page.locator('.xk-station--en').waitFor({ state: 'visible' });
      await checkHeaderLayout();
      await checkHomeLayout();
      const titleOverlapsRose = await page.locator('.xk-station--en').evaluate(station => {
        const rose = station.querySelector('.xk-station__rose svg').getBoundingClientRect();
        return [...station.querySelectorAll('.xk-station__title, .xk-station__sub')].some(element => {
          const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
          while (walker.nextNode()) {
            if (!walker.currentNode.textContent.trim()) continue;
            const range = document.createRange();
            range.selectNodeContents(walker.currentNode);
            if ([...range.getClientRects()].some(box =>
              Math.min(box.right, rose.right) - Math.max(box.left, rose.left) > 1 &&
              Math.min(box.bottom, rose.bottom) - Math.max(box.top, rose.top) > 1)) return true;
          }
          return false;
        });
      });
      assert.equal(titleOverlapsRose, false, 'English title text must not cross the book rose.');
      const directory = page.locator('#xk-lesson-directory');
      assert.equal(await directory.locator('.xk-lessons > a').count(), Object.keys(englishLessons).length);
      assert.equal(await directory.locator('.xk-lesson-group[open]').count(), 1, 'The complete directory opens one group by default.');
      await page.getByRole('button', { name: 'Expand all', exact: true }).click();
      assert.equal(await directory.locator('.xk-lesson-group[open]').count(), await directory.locator('.xk-lesson-group').count());
      await page.getByRole('button', { name: 'Collapse all', exact: true }).click();
      assert.equal(await directory.locator('.xk-lesson-group[open]').count(), 0);
      await page.locator('#xk-find-lesson').fill('14.9.1');
      await directory.locator('a[href$="#lesson-14-9-1"]').waitFor({ state: 'visible' });
      assert.equal(await directory.locator('.xk-lessons > a').count(), 1);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2), false, 'The English lesson directory must fit the viewport.');
      await page.getByRole('button', { name: 'Clear', exact: true }).click();
      assert.equal(await directory.locator('.xk-lessons > a').count(), Object.keys(englishLessons).length);
      await page.goto(base + 'en/theory/part-03.html#section-3-3');
      await page.waitForFunction(() => document.querySelector('.xk-tool--language')?.getAttribute('href')?.endsWith('#section-3-3'));
      assert.equal(await page.locator('html').getAttribute('lang'), 'en');
      await checkHeaderLayout();
      assert.match(await page.locator('#section-3-3').textContent(), /Effective Feedback/);
      assert.equal(await page.locator('.xk-search-btn').getAttribute('aria-label'), 'Search the book');
      await switchLanguage();
      await page.waitForURL(/\/theory\/part-03\.html#section-3-3$/);
      await page.waitForFunction(() => document.documentElement.lang === 'zh-CN');
      assert.match(await page.locator('#section-3-3').textContent(), /有效反馈/);
      await page.getByRole('button', { name: '搜索全书', exact: true }).click();
      await page.locator('#localsearch-input').fill('分组增益');
      await page.locator('#localsearch-list a.result').first().waitFor({ state: 'visible', timeout: 30000 });
      const chineseLinks = await page.locator('#localsearch-list a.result').evaluateAll(nodes => nodes.map(node => node.getAttribute('href')));
      assert.ok(chineseLinks.length && chineseLinks.every(href => !href.includes('/en/')), 'Chinese searches must return Chinese pages.');
      await page.keyboard.press('Escape');
      await page.waitForFunction(() => !document.getElementById('localsearch-input'));
      await page.waitForFunction(() => document.activeElement?.classList.contains('xk-search-btn'));
      for (const [button, drawer, state, breakpoint] of [
        ['.xk-topbar__menu', '#xk-nav', 'nav-open', 1024],
        ['.xk-tool--aside', '#xk-aside', 'aside-open', 1280],
      ]) {
        if (viewport.width >= breakpoint) continue;
        await page.locator(button).click();
        await page.waitForFunction(selector => !!document.activeElement?.closest(selector), drawer);
        await page.keyboard.press('Control+k');
        await page.waitForFunction(() => document.activeElement?.id === 'localsearch-input');
        await page.keyboard.press('Escape');
        await page.waitForFunction(() => !document.getElementById('localsearch-input'));
        await page.waitForFunction(() => document.activeElement?.classList.contains('xk-search-btn'));
        assert.equal(await page.locator('.xk-app').evaluate((el, state) => el.classList.contains(state), state), false,
          'Closing search opened from a drawer must return to a visible control.');
      }
      await switchLanguage();
      await page.waitForURL(/\/en\/theory\/part-03\.html#section-3-3$/);
      await page.waitForFunction(() => document.documentElement.lang === 'en');

      // A route change must refresh both the page outline and the locale switch destination.
      if (viewport.width < 1024) {
        await page.getByRole('button', { name: 'Book contents', exact: true }).click();
        const drawer = page.locator('#xk-nav');
        await drawer.waitFor({ state: 'visible' });
        assert.equal(await drawer.getAttribute('role'), 'dialog');
        await page.keyboard.press('Escape');
        await page.waitForFunction(() => !document.querySelector('.xk-app')?.classList.contains('nav-open'));
        await page.getByRole('button', { name: 'Book contents', exact: true }).click();
      }
      const partFour = page.locator('#xk-nav a[href$="/en/theory/part-04.html"]');
      await partFour.click();
      await page.waitForURL(/\/en\/theory\/part-04\.html$/);
      await page.waitForFunction(() => document.querySelector('.xk-tool--language')?.getAttribute('href')?.endsWith('/theory/part-04.html'));
      assert.equal(await page.locator('.xk-app').evaluate(el => el.classList.contains('nav-open')), false);
      assert.match(await page.locator('h1').textContent(), /Empirical Questions/);

      if (viewport.width < 1280) await page.getByRole('button', { name: 'Page outline and reading settings', exact: true }).click();
      const settings = page.locator('#xk-aside');
      const sourceOnly = settings.getByRole('switch', { name: 'Source text only', exact: true });
      const gists = page.locator('.xk-prose .xk-gist');
      assert.ok(await gists.count() > 10, 'Numbered sections with a lesson carry a one-sentence strip under the heading.');
      assert.equal(await gists.first().isVisible(), true);
      await sourceOnly.click();
      assert.equal(await sourceOnly.getAttribute('aria-checked'), 'true');
      assert.equal(await gists.first().isVisible(), false, 'Source-only reading hides the one-sentence strips with the lessons.');
      await sourceOnly.click();
      assert.equal(await sourceOnly.getAttribute('aria-checked'), 'false');
      assert.equal(await gists.first().isVisible(), true);
      await settings.getByRole('button', { name: 'L', exact: true }).click();
      assert.equal(await settings.getByRole('button', { name: 'L', exact: true }).getAttribute('aria-pressed'), 'true');
      if (viewport.width < 1280) await settings.getByRole('button', { name: 'Close', exact: true }).click();

      await page.getByRole('button', { name: 'Search the book', exact: true }).click();
      await page.locator('#localsearch-input').fill('Effective Feedback');
      await page.locator('#localsearch-list a.result').first().waitFor({ state: 'visible', timeout: 30000 });
      const links = await page.locator('#localsearch-list a.result').evaluateAll(nodes => nodes.map(node => node.getAttribute('href')));
      assert.ok(links.length && links.every(href => href.includes('/en/')), 'English searches must return English pages.');
      await page.locator('#localsearch-list a.result').first().click();
      await page.waitForFunction(() => !document.getElementById('localsearch-input'));
      assert.ok(page.url().includes('/en/'), 'Opening a search result must remain in English.');

      // A full translated lesson must retain the parts that a short guide could omit.
      await page.goto(base + 'en/theory/part-01.html#lesson-1-1');
      const complete = englishLessons['1.1'];
      const lesson = page.locator('.xk-lesson[data-section="1.1"]');
      await lesson.waitFor({ state: 'visible' });
      assert.equal(await lesson.locator('.xk-lesson__topic').textContent(), complete.title);
      assert.equal(await lesson.locator('.xk-steps > li').count(), complete.argumentSteps.length);
      assert.equal(await lesson.locator('.xk-split').count(), complete.distinctions.length);
      assert.equal(await lesson.locator('.xk-scenario').count(), complete.teachingExamples.length);
      assert.equal(await lesson.locator('.xk-counterexample').count(), complete.counterexamples.length);
      assert.equal(await lesson.locator('.xk-answer').count(), complete.questionAnswers.length);
      assert.equal(await lesson.locator('.xk-source-entry').count(), complete.sources.length);
      assert.ok(await lesson.locator('.xk-figure-description[open]').count(), 'Original Chinese figures need a visible English description.');
      const answer = lesson.locator('.xk-answer').first();
      await answer.locator('summary').click();
      await answer.locator('.xk-answer__body').waitFor({ state: 'visible' });
      assert.ok((await answer.locator('.xk-answer__body').textContent()).trim().length > 60, 'The full answer must be available.');
      const materials = lesson.locator('.xk-lesson-materials');
      await materials.locator(':scope > summary').click();
      await materials.getByRole('link', { name: 'Complete lesson manuscript (Chinese)', exact: true }).waitFor({ state: 'visible' });
      await switchLanguage();
      await page.waitForURL(/\/theory\/part-01\.html#lesson-1-1$/);
      await page.waitForFunction(() => document.documentElement.lang === 'zh-CN');
      await switchLanguage();
      await page.waitForURL(/\/en\/theory\/part-01\.html#lesson-1-1$/);
      await page.waitForFunction(() => document.documentElement.lang === 'en');

      // Field names and translation notes survive the Markdown/Vue rendering pipeline.
      await page.goto(base + 'en/theory/part-16.html');
      const code = await page.locator('.theory-source code').allTextContents();
      assert.ok(code.some(text => text.includes('_')), 'The source must retain underscored field names.');
      assert.ok(code.every(text => !text.includes('&#95;') && !text.includes('\\_')), 'Code must not display escaped underscore markup.');
      await page.goto(base + 'en/theory/part-03.html');
      const footnote = page.locator('a.footnote-ref, .footnote-ref a').first();
      await footnote.waitFor({ state: 'attached' });
      assert.ok(await footnote.count(), 'The English source must render its translation notes as footnotes.');
      {
        const target = await footnote.getAttribute('href');
        assert.ok(target && target.startsWith('#'));
        await footnote.click();
        assert.ok(await page.locator(`[id="${target.slice(1)}"]`).count(), 'A translation note must have an in-page destination.');
        await switchLanguage();
        await page.waitForFunction(() => document.documentElement.lang === 'zh-CN');
        assert.equal(await page.evaluate(() => !location.hash || !!document.getElementById(decodeURIComponent(location.hash.slice(1)))), true,
          'A translated footnote must return to a real Chinese section, never a dangling footnote anchor.');
      }
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2);
      assert.equal(overflow, false, `The ${viewport.width}px page must not overflow horizontally.`);
      await page.goto(base + 'en/theory/references.html#copyright-license');
      await switchLanguage();
      await page.waitForFunction(() => document.documentElement.lang === 'zh-CN');
      assert.equal(await page.evaluate(() => !location.hash || !!document.getElementById(decodeURIComponent(location.hash.slice(1)))), true,
        'An English-only license anchor must not become a broken Chinese anchor.');
      await page.goto(base + 'en/missing-page.html');
      await page.waitForFunction(() => document.documentElement.lang === 'en');
      await page.getByRole('heading', { name: 'This page is not in the book', exact: true }).waitFor({ state: 'visible' });
      assert.equal(await page.locator('.xk-brand').getAttribute('href'), prefix + 'en/');
      assert.equal(await page.locator('.xk-tool--language').textContent(), '中文');
      await page.getByRole('link', { name: 'Start reading', exact: true }).click();
      await page.waitForURL(/\/en\/theory\/$/);
      await page.goto(base);
      await page.locator('.xk-station .xk-sign--go').click();
      await page.waitForURL(/\/primer\/$/);
      await page.locator('.xk-prose h1', { hasText: '十句话入门' }).waitFor({ state: 'visible' });
      assert.equal(await page.locator('.xk-prose h2').count(), 12, 'The primer states ten sentences, their limits and where to go next.');
      await switchLanguage();
      await page.waitForFunction(() => document.documentElement.lang === 'en');
      await page.locator('.xk-prose h1', { hasText: 'Ten sentences to start with' }).waitFor({ state: 'visible' });
      assert.match(page.url(), /\/en\/primer\/$/, 'The primer keeps its place across languages.');
      assert.equal(await page.locator('.xk-prose h2').count(), 12);
      assert.deepEqual(errors, [], `No client errors at ${viewport.width}px`);
      console.log(`Handbook locale passed at ${viewport.width}px: language/section continuity, navigation, controls, English search, source fields, footnotes.`);
      await page.close();
    }
  } finally {
    await browser.close();
    if (server.listening) await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { if (server.listening) server.close(); console.error(error.stack); process.exitCode = 1; });
