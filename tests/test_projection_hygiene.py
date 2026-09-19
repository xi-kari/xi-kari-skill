from pathlib import Path
import subprocess
import sys

import pytest

from scripts.check_projection_hygiene import scan_text


@pytest.mark.parametrize(
    ("text", "rule"),
    [
        ("a1" * 32, "sha256-hex"),
        ("A1" * 32, "sha256-hex"),
        ("散列为" + "a1" * 32 + "，已核验。", "sha256-hex"),
        ("status=passed", "kv-field"),
        ("运行信息：run.status=complete，检查完成。", "kv-field"),
        ("- `main_answer_complete = true`", "kv-field"),
        ("| mode=open-world | 已检查 |", "kv-field"),
        ("后续为not_run，因为上一阶未获支持。", "machine-token"),
        ("MATCH", "machine-token"),
        ("undetermined", "machine-token"),
        ("已完成XK11。", "machine-id"),
        ("概念为 V82-CORE-001。", "machine-id"),
        ("引用 XK-PROV-CAPACITY。", "machine-id"),
        ("MECHANISM-001、CLAIM-001、NODE-001", "machine-id"),
        ("该MECHANISM-001支持这一判断。", "machine-id"),
        ("K1 与 HV11 已复核。", "machine-id"),
        ("```powershell\npython scripts/check_source_snapshot.py --all\n```", "command-dump"),
        ("~~~bash\npython scripts/check_source_snapshot.py --all\n~~~", "command-dump"),
        ("```\npython scripts/check_source_snapshot.py --all\n```", "command-dump"),
        ("~~~\n$ uv run pytest -q\n~~~", "command-dump"),
        ("> ```bash\n> python --version\n> ```", "command-dump"),
        ("- 记录\n\n    ```bash\n    python --version\n    ```", "command-dump"),
        ("[资料](https://example.org/?status=passed)，status=passed。", "kv-field"),
        ("Exit status: 0", "exit-code"),
        ("| 第一卷 | 亲读全文 | 已读 |", "receipt-row"),
        ("# 结论\n\n当前：完成/通过/下一步：交付", "status-opening"),
        ("**当前：**完成/通过/下一步：交付", "status-opening"),
        ("__判断强度：__可靠", "status-opening"),
        ("**当前**：完成/通过/下一步：交付", "status-opening"),
    ],
)
def test_rejects_reader_visible_machine_residue(text: str, rule: str) -> None:
    findings = scan_text("answer.md", text)
    assert any(f":{rule}:" in finding for finding in findings), findings


@pytest.mark.parametrize(
    "text",
    [
        "排班调整只改变了工作时间，还不能证明人员配置会随之改变。",
        "后续推演没有开展，因为上一阶缺少把时间节省转为人员调配的通道。",
        "本次没有做数字预测，因为缺少可校准依据。",
        "# 排班变化尚不能证明组织规则改变\n\n这一判断仍需补证。",
        "核心判断仍需补证。\n\n当前：两种解释都有可能，需要比较人员实际调配情况。",
        "[资料](https://example.org/search?q=work&lang=zh)",
        "[读取明细](source-read-receipt.md)",
        "| 选择 | 后果 |\n| --- | --- |\n| 等待 | 保留调整空间 |",
        "```mermaid\ngraph LR\nA --> B\n```",
        "Python 可以用于处理记录，但不能替代事实核验。",
        "[资料](https://example.org/?mode=report&status=active#details)",
        "matching、not_running 和 XK110 是不同的字串。",
        "a1" * 33,
        "```mermaid\ngraph LR\nA --> B\n```\n\nPython 可以处理记录。",
        "> 这份材料支持排班发生变化，尚不能说明人员数量改变。",
        "    这份材料支持排班发生变化，尚不能说明人员数量改变。",
        "核心判断仍需补证。\n\n**当前：**两种解释都有可能。",
        "> ```mermaid\n> graph LR\n> A --> B\n> ```",
    ],
)
def test_accepts_readable_content(text: str) -> None:
    assert scan_text("answer.md", text) == []


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_projection_hygiene.py"


def run_checker(*paths: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *(str(path) for path in paths)],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def test_cli_accepts_utf8_bom_without_writing(tmp_path: Path) -> None:
    answer = tmp_path / "answer.md"
    original = "排班变化仍需进一步观察。\n".encode("utf-8-sig")
    answer.write_bytes(original)
    result = run_checker(answer)
    assert result.returncode == 0, result.stderr
    assert answer.read_bytes() == original


def test_cli_reports_dirty_second_file_and_line_without_writing(tmp_path: Path) -> None:
    clean = tmp_path / "answer.md"
    dirty = tmp_path / "projection.md"
    clean.write_text("排班变化仍需进一步观察。\n", encoding="utf-8")
    original = "# 结论\n\nstatus=passed\n".encode("utf-8")
    dirty.write_bytes(original)
    result = run_checker(clean, dirty)
    assert result.returncode == 1
    assert f"{dirty}:3:kv-field:" in result.stderr
    assert dirty.read_bytes() == original


def test_cli_reports_missing_file(tmp_path: Path) -> None:
    assert run_checker(tmp_path / "missing.md").returncode == 2


def test_cli_reports_invalid_utf8(tmp_path: Path) -> None:
    answer = tmp_path / "answer.md"
    answer.write_bytes(b"\xff\xfe\x00")
    assert run_checker(answer).returncode == 2


def test_cli_requires_input() -> None:
    assert run_checker().returncode == 2
