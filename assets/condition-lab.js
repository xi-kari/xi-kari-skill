"use strict";
(() => {
  const data = JSON.parse(document.getElementById("condition-data").textContent);
  const stateNames = {
    known: "已计算", unknown: "未知", error: "计算错误", satisfied: "满足", violated: "不满足",
    satisfies_model_constraints: "满足所列模型约束", violates_model_constraints: "不满足所列模型约束",
    calculation_error: "存在计算错误", undetermined: "尚不能确定", no_constraints: "未定义约束"
  };
  const basisNames = { observed: "作者声明的观察值", assumed: "假设或方案设定", unknown: "未知" };
  const roleNames = { condition: "外部条件", decision: "可选决策" };
  const valueText = value => value === null ? "未知" : typeof value === "boolean" ? (value ? "是" : "否") : String(value);
  const node = (tag, text = "") => {
    const element = document.createElement(tag);
    element.textContent = text;
    return element;
  };
  const table = (target, headings, rows) => {
    const element = document.getElementById(target);
    element.replaceChildren();
    if (!rows.length) { element.append(node("p", "此模型未定义本项。")); return; }
    const result = node("table"), head = node("thead"), row = node("tr"), body = node("tbody");
    headings.forEach(title => { const cell = node("th", title); cell.scope = "col"; row.append(cell); });
    head.append(row);
    rows.forEach(values => { const line = node("tr"); values.forEach(value => line.append(node("td", String(value)))); body.append(line); });
    result.append(head, body);
    element.append(result);
  };
  const fillSelect = (id, items) => {
    const select = document.getElementById(id);
    items.forEach(([value, label]) => {
      const option = node("option", label); option.value = String(value); select.append(option);
    });
    return select;
  };
  const scenario = fillSelect("scenario", data.scenarios.map(item => [item.id, item.label]));
  const combination = fillSelect("combination", data.explore_combinations.map((item, index) => [index, Object.entries(item).map(([key, value]) => `${data.model.inputs[key].label}: ${valueText(value)} ${data.model.inputs[key].unit || ""}`).join("；") || "无额外离散条件"]));
  const initialCombination = data.explore_combinations.findIndex(item => Object.entries(item).every(([key, value]) => Object.is(data.model.inputs[key].value, value)));
  if (initialCombination >= 0) combination.value = String(initialCombination);
  const plan = fillSelect("plan", data.plans.map(item => [item.id, item.label]));
  document.getElementById("scope").textContent = (data.model.fictional ? "这是明确虚构的教学模型，输入不是现实事实。" : "这是作者提供的情境模型；输入来源与假设仍需分别判断。") + ` 已计算 ${data.case_count} 个组合。`;
  ["assumptions", "boundaries"].forEach(key => data.model[key].forEach(text => document.getElementById(key).append(node("li", text))));
  ["scenarios", "plans"].forEach(key => data[key].forEach(item => {
    const paragraph = node("p");
    paragraph.append(node("strong", item.label + "："), document.createTextNode((item.note || "") + " " + Object.entries(item.overrides).map(([name, value]) => `${data.model.inputs[name].label} = ${valueText(value)}`).join("；")));
    document.getElementById("definitions").append(paragraph);
  }));
  const update = () => {
    const peers = data.cases.filter(item => item.scenario === scenario.value && item.explore_index === Number(combination.value));
    const current = peers.find(item => item.plan === plan.value);
    if (!current) { document.getElementById("current-state").textContent = "此组合没有计算结果，不能插值推断。"; return; }
    document.getElementById("current-state").textContent = `${current.plan_label} · ${stateNames[current.state]}。该状态不等于现实可实施、最优或成功概率。`;
    table("comparison", ["方案", "所列约束", "不满足、未知或出错的约束"], peers.map(item => [item.plan_label, stateNames[item.state], item.constraints.filter(value => value.state !== "satisfied").map(value => `${value.description}（${stateNames[value.state]}）`).join("；") || "无；仍需检查模型未表示的条件"]));
    table("inputs", ["输入 / 标识", "当前值", "单位", "依据与角色", "来源 / 说明"], Object.entries(current.inputs).map(([key, item]) => [`${item.label} / ${key}`, valueText(item.value), item.unit || "—", `${basisNames[item.basis]}；${roleNames[item.role]}；${item.origin}`, [item.source || "未提供来源", item.original_source ? "原输入来源（不是覆盖值依据）：" + item.original_source : "", item.note || ""].filter(Boolean).join("；")]));
    table("derived", ["计算量 / 标识", "公式", "结果", "单位", "说明"], current.derived.map(item => [`${item.label} / ${item.id}`, item.formula, item.state === "known" ? valueText(item.value) : stateNames[item.state], item.unit || "—", [item.note || "", item.reason || ""].filter(Boolean).join("；")]));
    table("constraints", ["约束", "公式", "结果", "说明"], current.constraints.map(item => [item.description, item.formula, stateNames[item.state], item.reason || "仅判断该显式公式"]));
  };
  [scenario, combination, plan].forEach(select => select.addEventListener("change", update));
  update();
})();
