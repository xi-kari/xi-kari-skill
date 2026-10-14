# 导出 Word 文档

负责人需要把完整答案交成 Word 文件时使用。它处理的是**交付格式**，不改变正文内容：导出的文档与交给阅读页的 Markdown 是同一份论证，只是换了一种承载方式。

篇幅短、接收方不要求 Word 时不必生成。论文、报告、需要批注和修订的稿子用 Word；需要全文搜索、章节跳转和离线阅读的用[阅读页](presentation.md)。

## 命令

工具需要Python 3.10以上，只用标准库，不联网。以下PowerShell命令使用`$skillRoot`表示当前`SKILL.md`所在安装目录，`$taskRoot`表示安装外的用户任务目录，可从任意当前目录调用；路径设置见[宿主接入](host-setup.md)。输出必须落在安装目录之外。

```powershell
python "$skillRoot/scripts/render_docx.py" "$taskRoot/xi-kari-answer.md" --output "$taskRoot/xi-kari-answer.docx"
python "$skillRoot/scripts/render_docx.py" "$taskRoot/xi-kari-answer.md" --output "$taskRoot/交付稿.docx" --title '算法治理的民主悖论'
```

`--title` 只设置文档标题，不改动正文。输入与输出不能是同一个文件。

## 支持的语法

标题（一至六级）、段落、粗体、斜体、有序与无序列表（含嵌套）、引用块、围栏代码块、管道表格、分隔线、脚注、本地图片。

脚注集中到文末脚注章节，正文保留上标编号并可对照。本地图片按字节内嵌进文档，接收方打开时不依赖原路径；**远程图片不会被下载**，只保留替代文字与地址说明，因为导出过程不联网。

不支持的 Markdown 扩展保留为可见原文，并在命令输出的 `unsupported` 字段中列出，不会静默丢弃。这类内容需要在 Word 里手工整理时，来源仍然可查。

## 输出身份

生成的是标准 OOXML 包（`[Content_Types].xml`、`_rels/.rels`、`word/document.xml`、`word/_rels/document.xml.rels`、`word/styles.xml`），Word、WPS、LibreOffice 均可直接打开。所有文本按 XML 规则转义，正文里的 `<`、`&`、引号和中文都不会破坏文档结构。

导出的文档是当前完整稿的一个版本。正文后续修改后需要重新导出，不要让 Word 文件与实际论证脱节。若接收方要在此基础上做批注和修订，把 Word 文件交给他们之后，修订意见回来后按[稿件工作](manuscript-work.md)处理合并，不要让两边各自演进而无法合稿。

## 与其他交付方式的关系

| 交付需要 | 用什么 |
| --- | --- |
| 打开即读、全文搜索、章节跳转、离线 | [长文阅读页面](presentation.md)，`render_answer.py` |
| 交给他人批注、修订、打印成稿 | 本文件，`render_docx.py` |
| 条件与情景的离散比较 | [条件模型](condition-lab.md)，`condition_lab.py` |
| 方案在同一组维度上的比较 | [方案比较表](comparison-table.md)，`comparison.py` |

这些产物共同回答同一个问题，格式不同。任一正文结论改变时，受影响的产物都要同步，不能只更新其中一份。
