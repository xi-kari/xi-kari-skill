/* Run with node tests/test_condition_precision.cjs [playwright-core module path] [python]. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const http = require('node:http');
const { spawnSync } = require('node:child_process');
const { chromium } = require(process.argv[2] || path.join(__dirname, 'dom/node_modules/playwright-core'));
const python = process.argv[3] || 'python';
const root = path.resolve(__dirname, '..');
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'condition-precision-'));
const generate = String.raw`
import csv, json, pathlib, subprocess, sys
folder, root = map(pathlib.Path, sys.argv[1:])
text = '文字 9007199254740993 -9007199254740993 1.0 -0.0 "引号" \\路径 </script> & <tag>' + chr(0x2028) + chr(0x2029)
def field(label, value, role="condition", unit="个"):
    return {"label": label + " " + text, "value": value, "unit": unit,
            "basis": "unknown" if value is None else "assumed", "role": role, "note": text}
def base(title):
    return {"schema_version": 1, "title": title, "purpose": text, "fictional": True,
            "assumptions": [text], "boundaries": [text], "inputs": {}, "derived": [], "constraints": []}
minimal = base("相邻大整数")
minimal["inputs"] = {"positive": field("正整数", 9007199254740993)}
minimal["explore"] = {"positive": [9007199254740992, 9007199254740993]}
minimal["constraints"] = [{"id": "over", "formula": "positive > 9007199254740992", "description": text}]
large = base("多轴大整数")
large["inputs"] = {
    "positive": field("正整数", 9007199254740993), "negative": field("负整数", -9007199254740993),
    "choice": field("方案数字", 9007199254740993, "decision"), "context": field("情景数字", -9007199254740993),
    "wide": field("长整数", 10 ** 90 + 7), "small": field("小数", 1e-7),
}
large["explore"] = {"positive": [9007199254740992, 9007199254740993], "negative": [-9007199254740992, -9007199254740993]}
large["plans"] = [{"id": "alternate", "label": "方案 " + text, "overrides": {"choice": 9007199254740992}}]
large["scenarios"] = [{"id": "alternate", "label": "情景 " + text, "overrides": {"context": -9007199254740992}}]
large["constraints"] = [
    {"id": "positive_check", "formula": "positive > 9007199254740992", "description": "正值 " + text},
    {"id": "negative_check", "formula": "negative < -9007199254740992", "description": "负值 " + text},
    {"id": "plan_check", "formula": "choice > 9007199254740992", "description": "方案 " + text},
    {"id": "scenario_check", "formula": "context < -9007199254740992", "description": "情景 " + text},
]
scalars = base("词法与特殊标量")
scalars["inputs"] = {
    "lexical": field("整数与浮点", 1.0), "zero": field("零", -0.0), "flag": field("布尔与未知", False, unit=""),
    "choice": field("方案数字", 1.0, "decision"), "context": field("情景数字", -0.0),
}
scalars["explore"] = {"lexical": [1, 1.0], "zero": [0, 0.0, -0.0], "flag": [None, False, True]}
scalars["plans"] = [{"id": "alternate", "label": "方案 " + text, "overrides": {"choice": 1}}]
scalars["scenarios"] = [{"id": "alternate", "label": "情景 " + text, "overrides": {"context": 0.0}}]
scalars["constraints"] = [{"id": "flag_check", "formula": "flag == True", "description": text}]
wide = base("长整数完整展示")
wide["inputs"] = {
    "wide": field("长整数条件", 10 ** 90 + 7),
    "choice": field("长整数决策", 10 ** 90 + 7, "decision"),
    "context": field("长整数情景", -(10 ** 90 + 7)),
}
wide["explore"] = {"wide": [10 ** 90 + 7, 10 ** 90 + 8]}
wide["plans"] = [{"id": "alternate", "label": "长整数方案 " + text, "overrides": {"choice": 10 ** 90 + 8}}]
wide["scenarios"] = [{"id": "alternate", "label": "长整数情景 " + text, "overrides": {"context": -(10 ** 90 + 8)}}]
wide["constraints"] = [{"id": "wide_check", "formula": "wide > choice", "description": text}]
names = {"known": "已计算", "unknown": "未知", "error": "计算错误", "satisfied": "满足", "violated": "不满足",
         "satisfies_model_constraints": "满足所列模型约束", "violates_model_constraints": "不满足所列模型约束",
         "calculation_error": "存在计算错误", "undetermined": "尚不能确定", "no_constraints": "未定义约束"}
short = {**names, "satisfies_model_constraints": "满足", "violates_model_constraints": "不满足", "calculation_error": "计算错误"}
def scalar(value):
    if value is None: return "未知"
    if type(value) is bool: return "是" if value else "否"
    return json.dumps(value, ensure_ascii=False)
fixtures = []
for name, model in [("minimal", minimal), ("large", large), ("scalars", scalars), ("wide", wide)]:
    model["derived"] = [{"id": "copy_" + key, "label": "派生 " + item["label"], "formula": key, "unit": item["unit"], "note": text}
                        for key, item in model["inputs"].items()]
    work = folder / name
    work.mkdir()
    source = work / "model.json"
    source.write_text(json.dumps(model, ensure_ascii=False), encoding="utf-8")
    process = subprocess.run([sys.executable, str(root / "scripts/condition_lab.py"), str(source), "--output", str(work / "output")], capture_output=True, encoding="utf-8")
    if process.returncode: raise RuntimeError(process.stderr)
    paths = json.loads(process.stdout)["outputs"]
    result = json.loads(pathlib.Path(paths["json"]).read_text(encoding="utf-8"))
    compact = json.dumps(result, ensure_ascii=False, allow_nan=False)
    (work / "compact.json").write_text(compact, encoding="utf-8", newline="")
    inputs = model["inputs"]
    def with_unit(key, value):
        return scalar(value) + (" " + inputs[key]["unit"] if inputs[key]["unit"] and value is not None and type(value) is not bool else "")
    def combination(item, separator=": "):
        return "；".join(inputs[key]["label"] + separator + with_unit(key, value) for key, value in item.items())
    def signature(item):
        return tuple((key, json.dumps(value)) for key, value in item.items())
    lookup = {(case["scenario"], case["plan"], signature(case["explore"])): case for case in result["cases"]}
    cases = []
    for case in result["cases"]:
        sensitivity = []
        for key, values in model["explore"].items():
            entries = [lookup[(case["scenario"], case["plan"], signature({**case["explore"], key: value}))] for value in values]
            sensitivity.append({"title": inputs[key]["label"] + ("（" + inputs[key]["unit"] + "）" if inputs[key]["unit"] else ""),
                "values": [with_unit(key, value) for value in values], "states": [short[entry["state"]] for entry in entries],
                "current": [index for index, value in enumerate(values) if json.dumps(value) == json.dumps(case["explore"][key])]})
        cases.append({"id": case["id"], "scenario": case["scenario"], "plan": case["plan"], "combination": str(case["explore_index"]),
            "state": names[case["state"]], "planLabel": "方案：" + case["plan_label"],
            "caveat": case["scenario_label"] + "；" + combination(case["explore"]) + "。该状态不等于现实可实施、最优或成功概率。",
            "overviewLabel": case["plan_label"] + "，" + combination(case["explore"]) + "：" + names[case["state"]],
            "inputLabels": [item["label"] for item in case["inputs"].values()],
            "inputValues": [scalar(item["value"]) for item in case["inputs"].values()],
            "derivedLabels": [item["label"] for item in case["derived"]],
            "derivedValues": [scalar(item["value"]) if item["state"] == "known" else names[item["state"]] for item in case["derived"]],
            "formulas": [item["formula"] for item in case["derived"]],
            "constraints": [names[item["state"]] for item in case["constraints"]], "sensitivity": sensitivity})
    with pathlib.Path(paths["csv"]).open(encoding="utf-8", newline="") as handle:
        rows = {(row["case_id"], row["kind"], row["id"]): row for row in csv.DictReader(handle)}
    for case in result["cases"]:
        for kind, entries in [("input", case["inputs"].items()), ("derived", [(item["id"], item) for item in case["derived"]])]:
            for key, item in entries:
                expected = "" if item["value"] is None else json.dumps(item["value"])
                assert rows[(case["id"], kind, key)]["value"] == expected
    fixtures.append({"name": name, "html": paths["html"], "compact": str(work / "compact.json"), "cases": cases,
        "initial": str(next(index for index, item in enumerate(result["explore_combinations"]) if all(json.dumps(inputs[key]["value"]) == json.dumps(value) for key, value in item.items()))),
        "combinations": [combination(item) for item in result["explore_combinations"]],
        "headings": ["方案"] + [combination(item, " ") for item in result["explore_combinations"]],
        "definitionLabels": [item["label"] for group in ["scenarios", "plans"] for item in result[group]],
        "definitionValues": ["；".join(inputs[key]["label"] + " = " + with_unit(key, value) for key, value in item["overrides"].items()) for group in ["scenarios", "plans"] for item in result[group] if item["overrides"]],
        "literalText": text})
(folder / "oracle.json").write_text(json.dumps(fixtures, ensure_ascii=False), encoding="utf-8")
`;

let fixtures;
const server = http.createServer((request, response) => {
  const fixture = fixtures.find(item => request.url === `/${item.name}.html`);
  response.writeHead(fixture ? 200 : 404, { 'Content-Type': 'text/html; charset=utf-8' });
  response.end(fixture ? fs.readFileSync(fixture.html, 'utf8') : 'Not found');
});

(async () => {
  let browser;
  try {
    const prepare = spawnSync(python, ['-c', generate, temporary, root], { encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 });
    assert.equal(prepare.status, 0, prepare.stderr);
    fixtures = JSON.parse(fs.readFileSync(path.join(temporary, 'oracle.json'), 'utf8'));
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    browser = await chromium.launch({ channel: 'chrome', headless: true });
    const layoutFailures = [];
    for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
      for (const fixture of fixtures) {
        const page = await browser.newPage({ viewport, acceptDownloads: true });
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        const compact = fs.readFileSync(fixture.compact, 'utf8');
        const embedded = compact.replaceAll('&', '\\u0026').replaceAll('<', '\\u003c').replaceAll('>', '\\u003e').replaceAll('\u2028', '\\u2028').replaceAll('\u2029', '\\u2029');
        await page.goto(`http://127.0.0.1:${server.address().port}/${fixture.name}.html`);
        const context = `${fixture.name}, ${viewport.width}px`;
        assert.deepEqual(errors, [], `${context}: browser initialization`);
        assert.equal(await page.locator('#condition-data').textContent(), embedded, `${context}: original embedded JSON must remain exact`);
        assert.deepEqual(await page.locator('#combination option').allTextContents(), fixture.combinations, `${context}: adjacent integers and lexical grid values need exact labels`);
        assert.equal(await page.locator('#combination').inputValue(), fixture.initial, `${context}: exact initial grid point`);
        assert.deepEqual(await page.locator('#overview thead th').allTextContents(), fixture.headings, `${context}: overview headings`);
        assert.deepEqual(await page.locator('.definition-label').allTextContents(), fixture.definitionLabels, `${context}: definition labels`);
        assert.deepEqual(await page.locator('.definition-overrides').allTextContents(), fixture.definitionValues, `${context}: definition numbers`);
        for (const selector of ['.lab-purpose', '#assumptions li', '#boundaries li']) {
          assert.equal(await page.locator(selector).textContent(), fixture.literalText, `${context}: numeric and escaped text stays literal`);
        }
        for (const [index, expected] of fixture.cases.entries()) {
          await page.locator('#scenario').selectOption(expected.scenario);
          if (index % 2) {
            const planIndex = await page.locator('#plan option').evaluateAll((options, value) => options.findIndex(option => option.value === value), expected.plan);
            await page.locator('#overview tbody tr').nth(planIndex).locator('button').nth(Number(expected.combination)).click();
          } else {
            await page.locator('#combination').selectOption(expected.combination);
            await page.locator('#plan').selectOption(expected.plan);
          }
          const actual = await page.evaluate(() => {
            const texts = selector => Array.from(document.querySelectorAll(selector), node => node.textContent);
            return {
              scenario: document.getElementById('scenario').value, plan: document.getElementById('plan').value,
              combination: document.getElementById('combination').value,
              state: document.querySelector('#current-state .state').textContent,
              planLabel: document.querySelector('#current-state .state-plan').textContent,
              caveat: document.querySelector('#current-state .state-caveat').textContent,
              overviewLabels: Array.from(document.querySelectorAll('#overview button[aria-pressed="true"]'), node => node.getAttribute('aria-label')),
              inputLabels: texts('#inputs .label'),
              inputValues: Array.from(document.querySelectorAll('#inputs .number'), node => node.firstChild.textContent),
              derivedLabels: texts('#derived .label'),
              derivedValues: Array.from(document.querySelectorAll('#derived tbody tr'), row => row.cells[2].firstChild.firstChild.textContent),
              formulas: texts('#derived .formula'), constraints: texts('#constraints .state'),
              sensitivity: Array.from(document.querySelectorAll('.sens-item'), item => ({
                title: item.querySelector('.sens-title').textContent,
                values: Array.from(item.querySelectorAll('.sens-value'), node => node.textContent),
                states: Array.from(item.querySelectorAll('.sens-step .state'), node => node.textContent),
                current: Array.from(item.querySelectorAll('.sens-step'), (node, ordinal) => node.classList.contains('is-current') ? ordinal : -1).filter(ordinal => ordinal >= 0)
              }))
            };
          });
          const { id, overviewLabel, ...view } = expected;
          assert.deepEqual(actual, { ...view, overviewLabels: [overviewLabel] }, `${context}, ${id}: selectors, overview, scalar text, or sensitivity chose the wrong case`);
        }
        const link = page.locator('a[download="condition-results.json"]');
        const href = await link.getAttribute('href');
        assert.equal(Buffer.from(href.split(',')[1], 'base64').toString('utf8'), compact, `${context}: download data must preserve original numeric tokens`);
        const downloading = page.waitForEvent('download');
        await link.click();
        const download = await downloading;
        assert.equal(download.suggestedFilename(), 'condition-results.json');
        assert.equal(fs.readFileSync(await download.path(), 'utf8'), compact, `${context}: downloaded file must preserve original numeric tokens`);
        assert.equal(await page.locator('#condition-data').textContent(), embedded, `${context}: interactions must not rewrite source JSON`);
        assert.deepEqual(errors, [], `${context}: no browser errors`);
        if (fixture.name === 'wide') {
          const overflow = await page.evaluate(() => {
            const targets = [
              ['.state-caveat', '.current-state'], ['.sens-step', '.sens-item'],
              ['.definition-body', '#definitions'], ['.definition-overrides', '#definitions']
            ];
            return targets.flatMap(([selector, containerSelector]) => Array.from(document.querySelectorAll(selector), (element, index) => {
              const box = element.getBoundingClientRect();
              const container = element.closest(containerSelector).getBoundingClientRect();
              const internalOverflow = element.scrollWidth > element.clientWidth + 1;
              const outsideContainer = box.left < container.left - 1 || box.right > container.right + 1;
              const outsideViewport = box.left < -1 || box.right > document.documentElement.clientWidth + 1;
              return internalOverflow || outsideContainer || outsideViewport ? {
                selector, index, width: element.clientWidth, scrollWidth: element.scrollWidth,
                left: box.left, right: box.right, containerLeft: container.left, containerRight: container.right,
                viewportWidth: document.documentElement.clientWidth, internalOverflow, outsideContainer, outsideViewport
              } : null;
            }).filter(Boolean));
          });
          layoutFailures.push(...overflow.map(item => ({ viewport, ...item })));
        }
        console.log(JSON.stringify({ viewport, fixture: fixture.name, cases: fixture.cases.length, exactLabels: 'passed', sensitivity: 'passed', selectorsAndOverview: 'passed', download: 'passed', ...(fixture.name === 'wide' ? { layoutFailures: layoutFailures.filter(item => item.viewport.width === viewport.width).length } : {}) }));
        await page.close();
      }
    }
    assert.deepEqual(layoutFailures, [], 'Long integer prose, sensitivity steps, and definitions must fit their containers and viewport without clipping; tables may scroll horizontally.');
    console.log('Condition precision passed: desktop/mobile large integers, lexical numbers, null, booleans, signed zero, multi-axis case identity, literal strings, exact JSON downloads, and unclipped long values.');
  } finally {
    if (browser) await browser.close();
    if (server.listening) await new Promise(resolve => server.close(resolve));
    assert.equal(path.dirname(path.resolve(temporary)), path.resolve(os.tmpdir()));
    assert.ok(path.basename(temporary).startsWith('condition-precision-'));
    fs.rmSync(temporary, { recursive: true, force: true });
  }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
