"use strict";
(() => {
  const data = JSON.parse(document.getElementById("condition-data").textContent);
  const stateNames = {
    known: "已计算", unknown: "未知", error: "计算错误", satisfied: "满足", violated: "不满足",
    satisfies_model_constraints: "满足所列模型约束", violates_model_constraints: "不满足所列模型约束",
    calculation_error: "存在计算错误", undetermined: "尚不能确定", no_constraints: "未定义约束"
  };
  const shortNames = {
    satisfied: "满足", violated: "不满足", unknown: "未知", error: "计算错误",
    satisfies_model_constraints: "满足", violates_model_constraints: "不满足",
    calculation_error: "计算错误", undetermined: "尚不能确定", no_constraints: "未定义约束"
  };
  const kinds = {
    satisfied: "ok", satisfies_model_constraints: "ok", violated: "bad", violates_model_constraints: "bad",
    unknown: "unsure", undetermined: "unsure", error: "err", calculation_error: "err", no_constraints: "none"
  };
  const basisNames = { observed: "作者声明的观察值", assumed: "假设或方案设定", unknown: "未知" };
  const roleNames = { condition: "外部条件", decision: "可选决策" };
  const inputs = data.model.inputs;
  const valueText = value => value === null ? "未知" : typeof value === "boolean" ? (value ? "是" : "否") : String(value);
  const withUnit = (key, value) => `${valueText(value)}${inputs[key].unit && value !== null && typeof value !== "boolean" ? " " + inputs[key].unit : ""}`;

  function el(tag, className, ...children) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    children.flat().forEach(child => {
      if (child === null || child === undefined || child === "") return;
      element.append(typeof child === "string" || typeof child === "number" ? document.createTextNode(String(child)) : child);
    });
    return element;
  }
  const state = (code, long = false) => el("span", `state state-${kinds[code] || "none"}`, (long ? stateNames : shortNames)[code] || code);
  const cellOf = (code, ...content) => el("span", `cell is-${kinds[code] || "none"}`, content.length ? content : state(code));
  function table(target, headings, rows, className = "") {
    const container = document.getElementById(target);
    container.replaceChildren();
    if (!rows.length) { container.append(el("p", "empty", "此模型未定义本项。")); return; }
    const head = el("tr", "", headings.map(title => { const cell = el("th", "", title); cell.scope = "col"; return cell; }));
    const body = el("tbody", "", rows.map(row => {
      const line = el("tr", row.className || "");
      row.cells.forEach((value, index) => {
        const cell = el(index === 0 && row.rowHeader ? "th" : "td", "", value);
        if (index === 0 && row.rowHeader) cell.scope = "row";
        line.append(cell);
      });
      return line;
    }));
    container.append(el("table", className, el("thead", "", head), body));
  }
  function fillSelect(id, items) {
    const select = document.getElementById(id);
    items.forEach(([value, label]) => { const option = el("option", "", label); option.value = String(value); select.append(option); });
    return select;
  }
  const combinationLabel = item => Object.entries(item).map(([key, value]) => `${inputs[key].label}: ${withUnit(key, value)}`).join("；") || "无额外离散条件";
  const shortCombination = item => Object.entries(item).map(([key, value]) => `${inputs[key].label} ${withUnit(key, value)}`).join("；") || "无额外离散条件";
  const originText = origin => {
    if (origin === "input") return "输入原值";
    if (origin === "explore") return "条件网格设定";
    const [kind, id] = origin.split(":");
    const group = kind === "scenario" ? data.scenarios : data.plans;
    const item = group.find(entry => entry.id === id);
    return `${kind === "scenario" ? "外部情景" : "方案"}设定：${item ? item.label : id}`;
  };

  const scenario = fillSelect("scenario", data.scenarios.map(item => [item.id, item.label]));
  const combination = fillSelect("combination", data.explore_combinations.map((item, index) => [index, combinationLabel(item)]));
  const initialCombination = data.explore_combinations.findIndex(item => Object.entries(item).every(([key, value]) => Object.is(inputs[key].value, value)));
  if (initialCombination >= 0) combination.value = String(initialCombination);
  const plan = fillSelect("plan", data.plans.map(item => [item.id, item.label]));
  document.getElementById("scope").textContent = (data.model.fictional ? "这是明确虚构的教学模型，输入不是现实事实。" : "这是作者提供的情境模型；输入来源与假设仍需分别判断。") + ` 已计算 ${data.case_count} 个组合。`;
  ["assumptions", "boundaries"].forEach(key => data.model[key].forEach(text => document.getElementById(key).append(el("li", "", text))));
  const definitions = document.getElementById("definitions");
  [["scenarios", "外部情景"], ["plans", "方案"]].forEach(([key, kind]) => data[key].forEach(item => {
    const overrides = Object.entries(item.overrides).map(([name, value]) => `${inputs[name].label} = ${withUnit(name, value)}`).join("；");
    definitions.append(el("div", "definition",
      el("div", "", el("span", "definition-kind", kind), el("span", "definition-label", item.label)),
      el("p", "definition-body", item.note || (item.id === "baseline" ? "沿用输入中的取值，不作覆盖。" : ""),
        overrides ? el("span", "definition-overrides", overrides) : null)));
  }));

  function select(planId, combinationIndex) {
    plan.value = planId; combination.value = String(combinationIndex);
    update();
    document.querySelector('#overview button[aria-pressed="true"]')?.focus({ preventScroll: true });
  }
  function caseFor(scenarioId, explore, planId) {
    return data.cases.find(item => item.scenario === scenarioId && item.plan === planId &&
      Object.entries(explore).every(([key, value]) => Object.is(item.explore[key], value)));
  }

  function update() {
    const peers = data.cases.filter(item => item.scenario === scenario.value && item.explore_index === Number(combination.value));
    const current = peers.find(item => item.plan === plan.value);
    const band = document.getElementById("current-state");
    band.className = "current-state";
    if (!current) { band.replaceChildren(el("span", "state-caveat", "此组合没有计算结果，不能插值推断。")); return; }
    band.classList.add(`is-${kinds[current.state] || "none"}`);
    const scenarioLabel = data.scenarios.find(item => item.id === current.scenario)?.label || current.scenario_label;
    band.replaceChildren(state(current.state, true),
      el("span", "state-plan", `方案：${current.plan_label}`),
      el("span", "state-caveat", `${scenarioLabel}；${combinationLabel(current.explore)}。该状态不等于现实可实施、最优或成功概率。`));

    const combos = data.explore_combinations;
    const overviewHead = ["方案", ...combos.map(shortCombination)];
    table("overview", overviewHead, data.plans.map(item => ({
      rowHeader: true,
      className: item.id === current.plan ? "is-current-row" : "",
      cells: [item.label, ...combos.map((_, index) => {
        const entry = data.cases.find(value => value.scenario === scenario.value && value.plan === item.id && value.explore_index === index);
        if (!entry) return el("span", "note", "未计算");
        const button = el("button", `cell is-${kinds[entry.state] || "none"}`, state(entry.state));
        button.type = "button";
        button.setAttribute("aria-pressed", String(entry.id === current.id));
        button.setAttribute("aria-label", `${item.label}，${combinationLabel(combos[index])}：${stateNames[entry.state]}`);
        button.addEventListener("click", () => select(item.id, index));
        return button;
      })]
    })), "matrix");

    table("comparison", ["方案", ...current.constraints.map(item => item.description), "所列约束"], peers.map(item => ({
      rowHeader: true,
      className: item.plan === current.plan ? "is-current-row" : "",
      cells: [item.plan_label, ...item.constraints.map(value => cellOf(value.state)), el("span", "overall-cell", cellOf(item.state, state(item.state, true)))]
    })), "matrix");

    table("constraints", ["约束", "公式", "结果", "说明"], current.constraints.map(item => ({
      cells: [el("span", "label", item.description), el("code", "formula", item.formula), state(item.state), el("span", "note", item.reason || "仅判断该显式公式")]
    })));
    table("derived", ["计算量", "公式", "结果", "说明"], current.derived.map(item => ({
      cells: [
        [el("span", "label", item.label), el("span", "ident", item.id)],
        el("code", "formula", item.formula),
        item.state === "known" ? el("span", "number", valueText(item.value), item.unit ? el("span", "unit", item.unit) : null) : state(item.state),
        el("span", "note", [item.note || "", item.reason || ""].filter(Boolean).join("；") || "—")
      ]
    })));
    table("inputs", ["输入", "当前值", "依据", "角色", "来源与说明"], Object.entries(current.inputs).map(([key, item]) => ({
      cells: [
        [el("span", "label", item.label), el("span", "ident", key)],
        el("span", "number", valueText(item.value), item.unit ? el("span", "unit", item.unit) : null),
        el("span", `basis basis-${item.basis}`, basisNames[item.basis]),
        el("span", "role", roleNames[item.role]),
        [el("span", "", item.source || "未提供来源"),
          item.original_source ? el("span", "note", "原输入来源（不是覆盖值依据）：" + item.original_source) : null,
          item.note ? el("span", "note", item.note) : null,
          el("span", "origin", originText(item.origin))]
      ]
    })));

    const sensitivity = document.getElementById("sensitivity");
    sensitivity.replaceChildren();
    if (!data.sensitivity.length) {
      sensitivity.append(el("p", "empty", "此模型没有声明离散条件网格，因此没有单项比较。"));
    }
    data.sensitivity.forEach(item => {
      const unit = inputs[item.condition].unit;
      const steps = item.values.map(value => {
        const explore = { ...current.explore, [item.condition]: value };
        const entry = caseFor(current.scenario, explore, current.plan);
        const step = el("li", `sens-step${Object.is(current.explore[item.condition], value) ? " is-current" : ""}`,
          el("span", "sens-value", withUnit(item.condition, value)), entry ? state(entry.state) : el("span", "note", "未计算"));
        return step;
      });
      sensitivity.append(el("div", "sens-item",
        el("div", "sens-head", el("h3", "sens-title", item.label + (unit ? `（${unit}）` : "")),
          el("span", `sens-flag${item.decisive ? "" : " is-quiet"}`, item.decisive ? "单独改变过模型状态" : "未单独改变模型状态")),
        el("p", "sens-summary", `在 ${item.groups} 组“其余条件都相同”的比较中，有 ${item.state_changing_groups} 组只因这一项取值不同而改变了模型状态。`),
        el("p", "sens-strip-label", "当前情景与方案下，只改这一项："),
        el("ol", "sens-strip", steps)));
    });
  }
  [scenario, combination, plan].forEach(control => control.addEventListener("change", update));
  update();
})();
