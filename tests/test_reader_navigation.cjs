/* Run with node tests/test_reader_navigation.cjs [playwright-core module path] [python]. */
'use strict';
const assert = require('node:assert/strict');
const http = require('node:http');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { chromium } = require(process.argv[2] || path.join(__dirname, 'dom/node_modules/playwright-core'));
const python = process.argv[3] || 'python';
const root = path.resolve(__dirname, '..');
const paragraph = '这一段提供连续正文高度，检查目录导航与当前章节是否一致。\n\n';
const source = '# 阅读器导航\n\n' + ['A', 'B', 'C', 'D'].map(name => `## ${name} 节\n\n${name === 'B' ? '脚注入口[^a]。\n\n' : ''}${paragraph.repeat(18)}`).join('') + `\n[^a]: ${'脚注证据说明。'.repeat(1200)}\n`;
const render = spawnSync(python, ['-c', 'import importlib.util,sys; from pathlib import Path; s=importlib.util.spec_from_file_location("reader",sys.argv[1]); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); sys.stdout.reconfigure(encoding="utf-8"); print(m.render_document(sys.stdin.buffer.read().decode("utf-8")))', path.join(root, 'scripts/render_answer.py')], { input: source, encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 });
assert.equal(render.status, 0, render.stderr);
const server = http.createServer((request, response) => {
  response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  response.end(render.stdout);
});

(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const url = `http://127.0.0.1:${server.address().port}/reader.html`;
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
      const page = await browser.newPage({ viewport });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(url);
      async function settled() {
        await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      }
      async function checkCurrent(name, trigger) {
        await settled();
        const state = await page.evaluate(() => {
          let target = document.getElementById(location.hash.slice(1));
          if (target?.classList.contains('legacy-anchor')) target = target.nextElementSibling;
          return {
            target: target?.textContent,
            current: document.querySelector('#contents a[aria-current="location"]')?.textContent,
            targetTop: target?.getBoundingClientRect().top,
            toolbarHeight: document.querySelector('.reader-toolbar').getBoundingClientRect().height,
          };
        });
        assert.equal(state.current, `${name} 节`, `${viewport.width}px ${trigger}: ${JSON.stringify(state)}`);
        assert.ok(state.targetTop > state.toolbarHeight, 'The destination must remain below the sticky toolbar.');
        return state;
      }
      const snapshots = [];
      for (const name of ['B', 'C', 'A']) {
        if (await page.locator('#nav-toggle').isVisible()) await page.locator('#nav-toggle').click();
        await page.locator('#contents nav').getByRole('link', { name: `${name} 节`, exact: true }).click();
        snapshots.push(await checkCurrent(name, 'directory click'));
      }
      const destination = await page.locator('#contents nav').getByRole('link', { name: 'C 节', exact: true, includeHidden: true }).getAttribute('href');
      await page.goto(url + destination);
      snapshots.push(await checkCurrent('C', 'direct hash'));
      await page.goto(url + '#section-3');
      snapshots.push(await checkCurrent('B', 'legacy hash'));
      await page.reload();
      snapshots.push(await checkCurrent('B', 'legacy hash reload'));
      await page.locator('.footnote-ref a').click();
      await settled();
      const note = await page.evaluate(() => ({
        current: document.querySelector('#contents a[aria-current="location"]')?.textContent,
        top: document.getElementById(location.hash.slice(1)).getBoundingClientRect().top,
        padding: Number.parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop),
      }));
      assert.equal(note.current, '脚注');
      assert.ok(Math.abs(note.top - note.padding) < 1, `Footnote offset must apply once: ${JSON.stringify(note)}`);
      await page.locator('.footnote-backref').click();
      await settled();
      assert.equal(await page.locator('#contents a[aria-current="location"]').textContent(), 'B 节');
      const back = await page.evaluate(() => ({
        top: document.getElementById(location.hash.slice(1)).getBoundingClientRect().top,
        padding: Number.parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop),
      }));
      assert.ok(Math.abs(back.top - back.padding) < 1, `Footnote return offset must apply once: ${JSON.stringify(back)}`);
      await page.evaluate(() => {
        const heading = [...document.querySelectorAll('[data-reader-section]')].find(item => item.textContent === 'B 节');
        const toolbar = document.querySelector('.reader-toolbar').getBoundingClientRect().height;
        window.scrollTo(0, window.scrollY + heading.getBoundingClientRect().top - toolbar - 28);
      });
      await settled();
      assert.equal(await page.locator('#contents a[aria-current="location"]').textContent(), 'B 节', 'Manual scrolling must update the chapter independently of the URL hash.');
      if (viewport.width === 390) {
        await page.setViewportSize({ width: 700, height: 844 });
        await settled();
        await page.locator('#nav-toggle').click();
        await page.locator('#contents nav').getByRole('link', { name: 'C 节', exact: true }).click();
        snapshots.push(await checkCurrent('C', 'resized toolbar'));
      }
      assert.deepEqual(errors, []);
      console.log(JSON.stringify({ viewport, snapshots, footnote: note, footnoteReturn: back, manualScrollCurrent: 'B 节' }));
      await page.close();
    }
  } finally {
    await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
  console.log('Reader navigation passed: desktop/mobile directory clicks, direct/legacy hashes, footnotes, manual scrolling, and toolbar resizing.');
})().catch(error => { server.close(); console.error(error.stack); process.exitCode = 1; });
