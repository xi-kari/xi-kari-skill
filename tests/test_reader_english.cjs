/* Run with node tests/test_reader_english.cjs <jsdom module path> [python]. */
'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { JSDOM, VirtualConsole } = require(process.argv[2] || 'jsdom');
const python = process.argv[3] || 'python';
const root = path.resolve(__dirname, '..');
const source = '# Why Rules Fail\n\n## Mechanism\n\nApproval moved to one level and complaints rose.[^a]\n\n## Options\n\nKeep, adjust, probe or exit.\n\n[^a]: Six months of tickets.\n';
const render = spawnSync(python, ['-c', 'import importlib.util,sys; s=importlib.util.spec_from_file_location("reader",sys.argv[1]); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); sys.stdout.reconfigure(encoding="utf-8"); print(m.render_document(sys.stdin.buffer.read().decode("utf-8"), lang="en"))', path.join(root, 'scripts/render_answer.py')], { input: source, encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 });
assert.equal(render.status, 0, render.stderr);
const errors = [], copied = [];
const virtualConsole = new VirtualConsole();
virtualConsole.on('jsdomError', error => errors.push(error.message.slice(0, 200)));
const dom = new JSDOM(render.stdout, {
  runScripts: 'dangerously', url: 'https://example.invalid/reader-english', pretendToBeVisual: true, virtualConsole,
  beforeParse(window) {
    window.fetch = () => { throw new Error('Network must not be used'); };
    window.HTMLElement.prototype.scrollIntoView = function () {};
    window.ResizeObserver = class { constructor(callback) { this.callback = callback; } observe() { this.callback(); } };
    Object.defineProperty(window.navigator, 'clipboard', { value: { writeText: async text => { copied.push(text); } }, configurable: true });
  }
});

(async () => {
  const window = dom.window, document = window.document;
  assert.equal(errors.length, 0, errors.join('\n'));
  assert.equal(document.documentElement.lang, 'en');
  assert.match(document.getElementById('theme-toggle').title, /^Switch to (night|day) reading$/);
  const paragraph = [...document.querySelectorAll('#document > p')].find(element => element.textContent.includes('Approval moved'));
  const range = document.createRange(); range.selectNodeContents(paragraph);
  window.getSelection().removeAllRanges(); window.getSelection().addRange(range);
  document.dispatchEvent(new window.Event('selectionchange'));
  document.getElementById('quote-question').click();
  const textarea = document.getElementById('question-text');
  assert.equal(document.getElementById('question-panel').hidden, false);
  assert.ok(textarea.value.startsWith('Work: Why Rules Fail\nSection: '), textarea.value);
  assert.ok(textarea.value.includes('My question:\nPlease continue from this passage'), textarea.value);
  assert.doesNotMatch(textarea.value, /[㐀-鿿]/);
  assert.match(document.getElementById('question-status').textContent, /^The passage is in place/);
  document.getElementById('copy-question').click();
  await new Promise(resolve => setTimeout(resolve, 0));
  assert.equal(copied.length, 1);
  assert.equal(document.getElementById('question-status').textContent, 'Copied; paste it into your conversation.');
  console.log('English reader interaction checks passed');
  window.close();
})().catch(error => { console.error(error); process.exit(1); });
