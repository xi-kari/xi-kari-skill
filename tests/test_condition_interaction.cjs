/* Run after exporting a teaching model: node this-file <jsdom module path> <HTML>. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { JSDOM, VirtualConsole } = require(process.argv[2] || 'jsdom');
const source = fs.readFileSync(process.argv[3], 'utf8');
const failures = [];
const virtualConsole = new VirtualConsole();
virtualConsole.on('jsdomError', error => failures.push(error.message.slice(0, 200)));
const dom = new JSDOM(source, { runScripts: 'dangerously', url: 'https://example.invalid/condition-test', virtualConsole, beforeParse(window) {
  window.fetch = () => { throw new Error('Unexpected network call'); };
}});
try {
  const window = dom.window, document = window.document;
  assert.equal(failures.length, 0, failures.join('\n'));
  const data = JSON.parse(document.getElementById('condition-data').textContent);
  assert.equal(data.case_count, 27);
  assert.ok(document.getElementById('scope').textContent.includes('虚构'));
  const scenario = document.getElementById('scenario'), combination = document.getElementById('combination'), plan = document.getElementById('plan');
  assert.equal(scenario.options.length, 3); assert.equal(combination.options.length, 3); assert.equal(plan.options.length, 3);
  const messages = { satisfies_model_constraints: '满足所列模型约束', violates_model_constraints: '不满足所列模型约束', undetermined: '尚不能确定' };
  for (const testCase of data.cases) {
    scenario.value = testCase.scenario; combination.value = String(testCase.explore_index); plan.value = testCase.plan;
    plan.dispatchEvent(new window.Event('change'));
    assert.ok(document.getElementById('current-state').textContent.includes(testCase.plan_label));
    assert.ok(document.getElementById('current-state').textContent.includes(messages[testCase.state]));
    assert.equal(document.querySelectorAll('#comparison tbody tr').length, 3);
    const values = document.getElementById('derived').textContent;
    for (const computed of testCase.derived) {
      if (computed.state === 'known') assert.ok(values.includes(String(computed.value)));
    }
    assert.ok(document.getElementById('inputs').textContent.includes('假设或方案设定'));
  }
  const gridButton = document.querySelectorAll('#overview button')[2];
  const selectedLabel = gridButton.getAttribute('aria-label');
  gridButton.focus();
  gridButton.click();
  const selectedButton = document.querySelector('#overview button[aria-pressed="true"]');
  assert.equal(selectedButton.getAttribute('aria-label'), selectedLabel);
  assert.equal(document.activeElement, selectedButton, 'Activating a focused combination must preserve focus after rebuilding the grid.');
  combination.focus();
  combination.value = '0';
  combination.dispatchEvent(new window.Event('change'));
  assert.equal(document.activeElement, combination, 'Changing a selector must keep focus on that selector.');
  const downloadable = document.querySelector('a[download="condition-results.json"]');
  assert.ok(downloadable);
  assert.deepEqual(JSON.parse(Buffer.from(downloadable.href.split(',')[1], 'base64').toString('utf8')), data);
  assert.equal(document.querySelectorAll('script[src],link[rel="stylesheet"]').length, 0);
  assert.ok(document.querySelector('meta[http-equiv="Content-Security-Policy"]').content.includes("connect-src 'none'"));
  assert.equal(failures.length, 0, failures.join('\n'));
  console.log('Condition DOM checks passed: all 27 selections, grid focus, selector focus, peer-plan comparison, input identity, complete offline JSON download.');
} finally { dom.window.close(); }
