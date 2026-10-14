# 方案比较表

用于需要把多个候选方案在同一组维度上比清楚、并且每个取值都要留下依据身份的场合。它保护的是最容易被抹掉的一件事：**这个数字是事实、是假设，还是我们还不知道。**

三五个方案、少量维度、心里有数的比较，直接写成表格即可。这里登记的是依据身份和不可排序的维度，不能代替判断方案价值。

## 每个单元格都要声明依据

单元格有三种身份，必须显式写出，不写就报错：

| 身份 | 含义 | 要求 |
| --- | --- | --- |
| `observed` | 作者声明有来源的事实 | 必须给出 `source`；工具不核验该来源 |
| `assumed` | 作者设定的假设或方案取值 | 在表格、Markdown、HTML 中都会被标出 |
| `unknown` | 尚无可信取值 | `value` 必须为 `null`，不能用数值冒充 |

`unknown` 永远不会被当成 0、最差或最好，也不会进入任何排序。`basis=unknown` 却写了数值会被拒绝；`basis=observed` 却不给 `source` 也会被拒绝。缺失不能靠省略表达：每个候选在每个维度上都必须有一格，拿不准就写 `unknown`。

## 排序只在有共同尺度时产生

每个维度声明自己的朝向：

- `higher_is_better` / `lower_is_better`：工具列出**本次取值下**的顺序，并说明该顺序只在列出的取值与依据条件下成立。
- `not_orderable`：该维度没有共同比较尺度（例如「可逆性」这种定性判断），工具不生成任何排序，只列出各方案在该维度的取值与理由。

工具不产生跨维度加权，也不给出「整体最优方案」。这是刻意的：把不同量纲的维度合成一个分数，等于用一个未声明的价值判断替换掉用户自己的取舍。比较是工具，取舍是作者与用户的职责。

## 输入格式

```json
{
  "schema_version": 1,
  "title": "比较标题",
  "purpose": "这次比较要回答什么",
  "fictional": true,
  "assumptions": ["本次比较依赖的设定"],
  "boundaries": ["本表不能支持的结论"],
  "candidates": [{ "id": "auto", "label": "完全自动排序" }],
  "dimensions": [
    { "id": "extra_hours", "label": "额外工时", "direction": "lower_is_better", "unit": "工时" },
    { "id": "reversible", "label": "可逆性", "direction": "not_orderable" }
  ],
  "cells": {
    "auto": {
      "extra_hours": { "value": 0, "basis": "assumed", "note": "教学设定" },
      "reversible": { "value": "低", "basis": "assumed" }
    }
  }
}
```

`fictional` 必须明确写出，页首会据此说明这是虚构教学模型还是作者提供的情境。

## 命令

工具需要Python 3.10以上，只用标准库。以下PowerShell命令使用`$skillRoot`表示当前`SKILL.md`所在安装目录，`$taskRoot`表示安装外的用户任务目录，可从任意当前目录调用；路径设置见[宿主接入](host-setup.md)。输出写到安装目录之外。

```powershell
python "$skillRoot/scripts/comparison.py" "$taskRoot/我的比较.json" --output "$taskRoot/比较结果"
python "$skillRoot/scripts/comparison.py" "$taskRoot/我的比较.json" --output "$taskRoot/比较结果" --format md
python "$skillRoot/scripts/comparison.py" "$skillRoot/assets/examples/comparison-example.json" --output "$taskRoot/教学比较" --format all
```

一次运行产生三件同源产物：`comparison-results.json`（完整结构化结果，唯一权威）、`comparison-table.md`、`comparison-table.html`（单文件、内联样式、离线可开、可打印、可下载完整 JSON）。`--format` 可选 `json`、`md`、`html` 或 `all`（默认）。`--force` 只覆盖本工具先前生成的同名产物，永不覆盖输入。

取值的依据身份在三种格式里都保留。HTML 用标签区分事实、假设与未知，并在打印时降为带边框的文字标记，不依赖颜色单独传达区别。

## 与理论的关系

比较表承担「方案比较」这一步的材料整理，不承担裁决。它把每个取值放回它的依据身份，使读者能看清哪些差异来自事实、哪些来自假设、哪些还悬空。最终首选与落选理由仍由正文完整写出，说明作用通道、承接者、成本与适用条件；表格不能替代那段论证。
