# 讲解怎样写：字段与对应的版面

讲解写在 `content/section-lessons.json` 的 `lessons` 里，键是原文的阅读单元（`3.3`、`C.12`、`intro-03-part`、`front-scope` 等，完整列表见 `content/reading-units.json`）。运行 `npm run build`（或 `npm run dev`）时，生成脚本会把讲解放到对应原文小节之后；每一页只加载自己的讲解。

讲解在页面上是一张叠在原文上的“描图纸”：网格、胶带、左上角的详图索引圈写着节号。原文保持墨色印刷，讲解永远和原文分得开。每个字段对应一种画法，字段为空或不写，对应的模块就不出现。

| 字段 | 类型 | 画法 |
| --- | --- | --- |
| `title` | 文字 | 讲解的题目，写在“读懂这一节”下面；首页逐节目录也用它。 |
| `lead` | 文字 | 一句话要点。仿宋大字，带荧光笔底纹（深色模式是一道黄线）。 |
| `explanation` | 文字数组 | 讲解正文，一项一段。 |
| `keyTerms` | `[{term, text, ref?, href?}]` | “这一节用到的词”：两栏小词表。`ref` 是链接文字（如 `§3.1`），`href` 指向原文位置。 |
| `sourceQuotes` | `[{text, ref?, href?}]` | “原文这样说”：仿宋引文，左边一道墨线。引文须与原文逐字一致。 |
| `argumentSteps` | 文字数组 | “论证怎样展开”：带编号圆圈的尺寸链，适合有先后的推理步骤。 |
| `distinctions` | `[{leftTitle, leftText, rightTitle, rightText}]` | “把容易混淆的地方分开”：剖切对照，中缝一枚黄色 ≠。 |
| `diagramPath`、`diagramCaption` | 文字 | 一张图版：四角套准线，点击放大。图片放在 `public/images/`，路径写 `/images/x.svg`。 |
| `figures` | `[{path, alt, caption}]` | 图版按顺序编号；与主图路径相同的项只显示一次。可放大、查看原始尺寸。 |
| `teachingExamples` | `[{title, text, assumptions?, boundary?}]` | 虚线框加“教学情景”标签：假设的、用来说明区别的例子。`assumptions` 显示为“设定”条。 |
| `model` | `feedback`、`joint` 或 `prediction` | 在讲解里放入对应的交互教学模型。§3.3、C.12、§4.6 不写也会自动放入。 |
| `caseNotes` | `[{title, text, sourceLabel, sourceUrl, sourceLocator?, boundary?, href?}]` | 实线折角卡片加“真实案例”标签：有出处的事实。出处单独成框，`boundary` 显示为“适用边界”，`href` 指向完整案例页。 |
| `boundaries` | 文字数组 | “这一步还不能推出什么”：左边一条黄黑警示胶带，每条前面一个禁止符号。 |
| `counterexamples` | `[{identity, text, effect, sourceIds}]` | 反例、它限制的判断与可回查来源；教学反例、现实反证和未决边界保留不同身份。 |
| `applicability.reason`、`openQuestions` | 文字、文字数组 | 本节适用范围和仍待回答的问题。 |
| `questions` | 文字数组 | “读完后，试着辨认”：编号的自测问题。 |
| `questionAnswers` | `[{question, answer, basis?}]` | 可展开的解释，点开时平滑展开；`basis` 显示为“依据”。 |
| `summary` | 文字 | “收束”：一句话结论，荧光笔底纹。 |
| `caseLinks` | `[{title, href}]` | 讲解末尾的“继续阅读”链接。 |
| `sourceRefs` | `[{section, startLine, endLine}]` | 在材料区显示原文位置，也兼容交付格式的 `start_line`、`end_line`。 |
| `sources` | 来源对象数组 | 展示题名、日期、位置、支持范围、限制和交付者标注的阅读范围。 |
| `lecturePath`、`sourcesPath`、`sourceSlicePath`、`diagramsPath` | 资源路径 | 完整交付原稿、来源登记、原文对照和图解材料的下载入口。 |
| `supplementaryFiles` | `[{title, path}]` | 实际存在的补充数据下载。 |

模块的出场顺序固定：要点 → 正文 → 用到的词 → 原文引文 → 论证步骤 → 区分对照 → 图版 → 教学情景 → 交互模型 → 真实案例 → 反例 → 不能推出什么 → 适用范围与待解问题 → 自测与回答 → 收束 → 继续阅读 → 来源与材料。

正文支持换行、明确的 Markdown 链接、粗体与行内代码，HTML 标签始终作为文字。原文节号可直接跳转。相对图片和资料地址以交付任务的资源目录解析；绝对外部链接保留其地址。图解制作方案留在可下载的图解材料中，不把计划中的交互描述成已实现功能。

`content/section-lessons.json` 保留导入的内容。限定核读后的补充可写入 `content/lesson-overrides.json`，其 `baseSha256` 必须匹配导入文件，`lessons` 按单元键给出完整字段替换。正文与搜索共同读取补充后的内容；完整交付原稿继续保留原始字节。

## 一个最小的例子

```json
{
  "lessons": {
    "3.1": {
      "title": "先把对象说清楚，再谈它有没有效",
      "lead": "D0 只声明候选对象，不证明对象有效。",
      "explanation": ["……", "……"],
      "distinctions": [
        { "leftTitle": "声明对象", "leftText": "……", "rightTitle": "对象有效", "rightText": "……" }
      ],
      "boundaries": ["……"],
      "questions": ["……"]
    }
  }
}
```

## 写作上的约定

- 讲解解释原文作出的区别和它的边界，不改写作者的定义；引用定义请回到原文节号。
- 教学情景和真实案例分开写：前者用 `teachingExamples`，后者用 `caseNotes` 并给出可核对的出处。
- 标题用的朱雀仿宋已包含 3,755 个常用字和站内用到的全部字。讲解里出现常用字以外的生僻字时，那几个字会退回系统字体；需要时重新运行 `python scripts/build_fonts.py --font <ZhuqueFangsong-Regular.ttf>` 补齐。
