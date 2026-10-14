"""Exercise copied install payloads without giving runtime tools writable resources."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]


def inventory(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*") if path.is_file()
    }


class PortableRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="xikari-portable-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.install = self.root / "另一个 用户" / "技能 安装"
        self.work = self.root / "独立 任务"
        self.cwd = self.root / "无关 工作目录"
        self.work.mkdir()
        self.cwd.mkdir()
        payload = json.loads((REPO / "skill-package.json").read_text(encoding="utf-8"))["files"]
        self.assertIn("scripts/xikari_paths.py", payload)
        for name in payload:
            target = self.install / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / name, target)
        self.before = inventory(self.install)
        self.dirs_before = sorted(p.relative_to(self.install).as_posix() for p in self.install.rglob("*") if p.is_dir())
        self.input = self.work / "完整 正文.md"
        self.input.write_text("# 任务案例\n\n第一段材料。\n\n第二段材料。\n", encoding="utf-8")
        self.model = self.install / "assets/examples/condition-project.json"
        self.record = self.install / "assets/examples/case-record.json"

    def command(self, script, *arguments, cwd=None, success=True):
        result = subprocess.run(
            [sys.executable, str(self.install / "scripts" / script), *map(str, arguments)],
            cwd=cwd or self.cwd, capture_output=True, encoding="utf-8", timeout=45,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("技能安装目录是只读资源", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        return result

    def unchanged(self):
        self.assertEqual(inventory(self.install), self.before)
        self.assertEqual(
            sorted(p.relative_to(self.install).as_posix() for p in self.install.rglob("*") if p.is_dir()),
            self.dirs_before,
        )
        self.assertFalse(list(self.install.rglob("__pycache__")))

    def test_all_tools_run_from_unrelated_cwd_without_changing_install(self):
        self.command("read_source.py", "--check")
        self.command("read_source.py", "--chunk", "1")
        catalog = self.work / "材料" / "catalog.json"
        self.command("evidence.py", "--catalog", catalog, "add", self.install / "SKILL.md", "--id", "instruction")
        self.command("evidence.py", "--catalog", catalog, "clip", "--id", "instruction", "--clip-id", "title", "--at", "L1", "--support", "只支持所选原文")
        self.command("condition_lab.py", self.model, "--output", self.work / "条件推演")
        self.command("condition_lab.py", self.model, "--output", self.work / "条件推演", "--force")
        self.command("casebook.py", "--library", self.work / "案例" / "library.json", "add", "--record", self.record)
        self.command("manuscript.py", "snapshot", "--root", self.work, "--file", self.input.name, "--output-dir", self.work / "快照")
        candidate = self.work / "候选.md"
        candidate.write_text(self.input.read_text(encoding="utf-8") + "\n新段落。\n", encoding="utf-8")
        self.command("manuscript.py", "compare", "--current", self.input, "--candidate", candidate, "--output", self.work / "差异.txt")
        self.command("manuscript.py", "merge", "--base", self.input, "--current", self.input, "--candidate", candidate, "--output", self.work / "合稿.md")
        self.command("render_answer.py", self.input, "--output", self.work / "阅读" / "answer.html")
        self.assertTrue((self.work / "阅读/answer.html").is_file())
        self.assertTrue((self.work / "条件推演/condition-results.html").is_file())
        self.assertEqual((self.work / "合稿.md").read_bytes(), candidate.read_bytes())
        self.unchanged()

    def reject_outputs(self, output, cwd=None):
        self.command("evidence.py", "--catalog", output / "materials.json", "add", self.input, "--id", "source", cwd=cwd, success=False)
        self.command("condition_lab.py", self.model, "--output", output, "--force", cwd=cwd, success=False)
        self.command("casebook.py", "--library", output / "library.json", "add", "--record", self.record, cwd=cwd, success=False)
        self.command("manuscript.py", "snapshot", "--root", self.work, "--file", self.input.name, "--output-dir", output / "snapshot", cwd=cwd, success=False)
        self.command("manuscript.py", "compare", "--current", self.input, "--candidate", self.input, "--output", output / "difference.txt", cwd=cwd, success=False)
        self.command("render_answer.py", self.input, "--output", output / "answer.html", cwd=cwd, success=False)

    def test_install_and_dotdot_outputs_are_refused_before_creating_files(self):
        self.reject_outputs(self.install / "不应 创建" / "深层")
        self.reject_outputs(self.install / "scripts" / ".." / "不应 创建")
        self.reject_outputs(Path("."), cwd=self.install)
        self.command("render_answer.py", self.input, "--output", self.install / "SKILL.md", success=False)
        self.unchanged()

    def directory_link(self, alias, target):
        try:
            alias.symlink_to(target, target_is_directory=True)
        except OSError:
            if os.name != "nt":
                self.skipTest("Directory links are unavailable")
            # Directory junctions do not require Developer Mode on Windows.
            shell = shutil.which("pwsh") or shutil.which("powershell")
            if shell is None:
                self.skipTest("PowerShell is unavailable for a Windows directory junction")
            quote = lambda path: "'" + str(path).replace("'", "''") + "'"
            result = subprocess.run(
                [shell, "-NoProfile", "-Command",
                 f"New-Item -ItemType Junction -Path {quote(alias)} -Target {quote(target)} | Out-Null"],
                capture_output=True, encoding="utf-8",
            )
            if result.returncode or not alias.exists():
                self.skipTest("Neither directory symlinks nor junctions are available")

    def test_parent_directory_link_to_install_is_refused(self):
        alias = self.work / "link-to-skill"
        self.directory_link(alias, self.install)
        try:
            self.reject_outputs(alias / "不应 创建")
            self.unchanged()
        finally:
            # Remove this exact link, never descend into the installed payload.
            alias.unlink() if alias.is_symlink() else alias.rmdir()

    def test_install_link_outward_does_not_make_install_a_work_directory(self):
        alias = self.install / "external-work"
        self.directory_link(alias, self.work)
        try:
            self.reject_outputs(alias / "不应 创建")
            self.assertFalse((self.work / "不应 创建").exists())
        finally:
            alias.unlink() if alias.is_symlink() else alias.rmdir()
        self.unchanged()

    def test_shared_module_does_not_cache_first_install_root(self):
        helper = REPO / "scripts/xikari_paths.py"
        spec = importlib.util.spec_from_file_location("portable_paths_test", helper)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        caller = self.install / "scripts/evidence.py"
        with self.assertRaises(module.InstalledResourceError):
            module.require_external_output(self.install / "new.json", caller)
        self.assertEqual(module.require_external_output(self.work / "new.json", caller), self.work / "new.json")
        second = self.root / "第二份安装"
        with self.assertRaises(module.InstalledResourceError):
            module.require_external_output(second / "new.json", second / "scripts/evidence.py")
        self.unchanged()


if __name__ == "__main__":
    unittest.main()
