# 参与开发

运行问题和具体改进请提交 [Issue](https://github.com/xi-kari/xi-kari-skill/issues/new/choose)。理论讨论、使用经验和开放问题可以放在 [Discussions](https://github.com/xi-kari/xi-kari-skill/discussions?discussions_q=)。安装与宿主接入见[安装指南](docs/INSTALL.md)。

## 开发环境

当前工具与安装包在 Windows 上维护，CI 使用 Python 3.10、3.13 和 Node.js 22.x。网页测试需要 Node.js 22.22.2 及以上的 22.x，也可使用满足 `tests/dom/package.json` 中 `engines` 声明的新版 Node.js。Python 工具主体使用标准库；PDF 材料测试需要 `pypdf`，网页交互测试使用 `tests/dom` 中固定的开发依赖。

在仓库根目录准备测试依赖：

```powershell
python -m pip install pypdf==6.19.0
npm ci --prefix tests/dom --ignore-scripts --no-audit --no-fund
```

## 修改边界

- `SKILL.md` 与 `references/` 定义实际使用行为。保留完整理论学习、XK0—XK11 正序分析和持续对话协作；开发检查不应成为每轮分析的前置流程。
- `source/Xikari-条件结构与转化论.md` 是 Xikari 著理论原文。工具、排版或说明修改不要顺带改写原文；理论文本修订须与一般工程修改分开，并明确文本来源与身份。
- `skill-package.json` 明确选择安装文件。安装包只包含技能运行资源，不包含开发文档、测试、网站、私人材料、运行记录或宿主配置。
- 随包资源保持只读。任务输出、案例库、交付包和临时检查结果放在技能安装目录之外。
- `README.md` 介绍产品能力，安装说明放在 `docs/INSTALL.md`，网站内容位于 `docs/`。正文和产品文件不写迭代过程、核验回执或开发记录。
- 提交可公开的输入与复现步骤，移除凭据、个人路径和私人案例。保留第三方资源的来源与许可证。

## 验证修改

按改动范围运行相应检查，并在 PR 中写明实际结果与未覆盖部分。只调整文字时无需声称运行了完整测试。

工具、理论读取或安装清单修改：

```powershell
python -m unittest discover -s tests -v
python scripts/read_source.py --check
$xikariOutput = Join-Path ([System.IO.Path]::GetTempPath()) ('xikari-check-' + [guid]::NewGuid().ToString('N'))
python scripts/build_install_package.py --output $xikariOutput
```

阅读器、条件模型页面或项目介绍页修改，还应运行对应交互检查：

```powershell
node tests/test_reader_interaction.cjs "$PWD/tests/dom/node_modules/jsdom"
node tests/test_reader_navigation.cjs "$PWD/tests/dom/node_modules/playwright-core"
$xikariConditionOutput = Join-Path ([System.IO.Path]::GetTempPath()) ('xikari-condition-' + [guid]::NewGuid().ToString('N'))
python scripts/condition_lab.py assets/examples/condition-university.json --output $xikariConditionOutput
node tests/test_condition_interaction.cjs "$PWD/tests/dom/node_modules/jsdom" "$xikariConditionOutput/condition-results.html"
node tests/test_project_page_interaction.cjs "$PWD/tests/dom/node_modules/jsdom"
```

涉及视觉呈现时，另在实际浏览器检查桌面、手机、深浅主题及相关操作。自动化检查通过只说明所覆盖的行为符合预期，不代表理论有效性或模型理解已获证明。

## 提交 PR

围绕一个明确问题提交改动，说明触发场景、改后的行为和验证结果。不要附带私有试用产物或无关配置。若变更第三方依赖，请保留锁文件或固定版本，并验证它实际影响的工具与页面。
