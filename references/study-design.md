# 研究设计与采集说明

用于分析走到「还需要什么材料才能区分」这一步的场合：几种解释都说得通，当前材料无法分开它们，需要把尚未解决的实质问题转成别人能接着执行的观察与采集安排。

纯规范争议、文本解释和已有充分材料的问题不需要强行做成研究设计。

## 一条硬规则：命题必须能被区分

每条竞争命题至少要写出一条**能区分它的观察**。写不出区分观察的内容不能作为研究命题登记——请把它改成两条可以区分的命题，或者作为已知事实写进正文。工具会在缺少区分观察时报错并拒绝通过，而不是放过。

这正是研究设计的意义所在：不是罗列还想知道什么，而是说明**看到什么就能把它与别的解释分开**。

## 缺失保留为缺失

除研究问题与命题本身外，其余字段都可以先不填：

- 观察对象与位置、时间窗、所需材料与字段
- 保持的条件、改变的条件
- 混杂与选择偏差
- 停止条件
- 执行者与权限（由谁在什么权限内完成）

未填写的字段被报告为缺失，并在生成的说明里标注 `（设计未填写，保留为缺失，未补默认值）`。工具不会补 0、不会编造分母、不会生成看起来完整的假数据。缺失项由实际承担研究的人补齐。

工具不判断研究是否值得做、观察是否真实可获得、来源是否可信。这些仍由作者负责。

## 输入格式

```json
{
  "schema_version": 1,
  "question": "这次研究要回答的问题",
  "propositions": [
    {
      "id": "capacity",
      "statement": "一种竞争解释",
      "supports": ["什么观察支持它"],
      "excludes": ["什么观察排除它"],
      "distinguishing": ["什么观察能把它与别的解释分开"]
    }
  ],
  "observation_targets": ["看哪些对象与位置"],
  "time_window": "时间窗与单位",
  "required_materials": ["需要哪些材料与字段"],
  "hold_conditions": ["哪些条件保持不变"],
  "change_conditions": ["哪些条件发生改变"],
  "confounders": ["混杂与选择偏差"],
  "stop_conditions": ["什么情况下停止某项判断"],
  "execution": [{ "who": "由谁完成", "authority": "在什么权限内" }]
}
```

## 命令

工具需要Python 3.10以上，只用标准库，不联网。以下命令使用`$skillRoot`表示当前`SKILL.md`所在安装目录，`$taskRoot`表示安装外的用户任务目录，可从任意当前目录调用；路径设置见[宿主接入](host-setup.md)。

```powershell
python "$skillRoot/scripts/study_design.py" --design "$taskRoot/研究设计.json" validate
python "$skillRoot/scripts/study_design.py" --design "$taskRoot/研究设计.json" render --output "$taskRoot/研究与采集说明.md"
python "$skillRoot/scripts/study_design.py" --design "$skillRoot/assets/examples/study-design-example.json" validate
```

`validate` 只读，打印结构报告与缺失清单，不写文件。`render` 生成一份可交接的《研究与采集说明》，写明要区分哪些命题、看哪些对象、记录什么字段、什么情况下停止。输出必须落在安装目录之外的用户任务目录。

`$skillRoot/assets/examples/study-design-example.json`是一份字段填满的示例，全部为教学占位内容，不含任何现实机构数据。

## 结果怎样接回分析

实际取得材料后，新结果按[现实使用与反馈](real-world-use.md)接入受影响的解释、方案与图表；需要长期留用的案例按[案例积累](case-library.md)保存。区分观察显示多个机制并存时，更新各机制的支持范围，而不是强选一个故事；只证实记录口径变化时，先修正比较口径，不能据此认定实际问题没有变化。

失败与不区分的结果同样有内容价值，不要只留下支持预想结论的一次运行。
