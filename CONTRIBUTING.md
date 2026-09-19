# 参与贡献

感谢关注 xi-kari-skill。本文说明改动这个仓库时需要遵守的边界与自检流程。

## 环境

- 指令层运行不需要 Python；改动 `scripts/`、`schemas/` 或源快照需要 Python 3.11+。
- 五条自检脚本的第三方依赖只有 `jsonschema`（含 `referencing`）：`pip install "jsonschema>=4.23,<5"`，或使用 `uv sync --group dev`。

## 提交前必须全绿的五条自检

```bash
python scripts/check_source_snapshot.py --all
python scripts/build_knowledge_index.py --check
python scripts/check_ontology.py --all
python scripts/check_xi_kari_skill.py --all
python scripts/check_xi_kari_runtime.py --all
```

改动检查器或其他脚本时，同时运行行为回归测试：

```bash
uv run pytest -q
```

CI 会在每次 push 与 pull request 上自动运行回归测试和同样的五条检查（Linux 与 Windows 双平台），另加一条公开卫生检查：文档元数据、个人机器路径、同步盘路径与私人邮箱不得入库。

## 修改边界

- `references/source/v8.2/` 是经校验的源快照，目录名与内容受 manifest 哈希锁定。不要手改快照文件；确需重建时使用 `scripts/build_source_snapshot.py`，并让五条自检重新全绿。
- runtime 的绑定器、校验器、`schemas/xk-*.schema.json` 与 `protocols/` 文档是同一套口径：改任何一处字段语义，四处都要同步，避免出现"绑定器写 X、校验器要求 Y"的失配。
- 运行产物（run 目录）只存在于平台状态目录或显式 `--runs-root`，永远不要提交进仓库。

## 提交信息

采用 Conventional Commits 风格：`feat:`、`fix:`、`docs:`、`ci:`、`test:`、`chore:`。

## 隐私边界

- 仓库内容、提交信息与文档元数据不得包含个人身份信息、真实机器路径或同步盘路径；示例路径一律使用 `<你>` 占位符。
- 维护者对外身份只使用 GitHub [@xi-kari](https://github.com/xi-kari)，提交使用 GitHub noreply 邮箱。
