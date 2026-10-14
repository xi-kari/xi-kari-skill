"""Keep installed skill resources separate from caller-selected work products."""

from __future__ import annotations

import os
from pathlib import Path


class InstalledResourceError(OSError):
    """An output would modify the installed skill rather than task data."""


def require_external_output(path: Path | str, caller: Path | str) -> Path:
    """Reject lexical and resolved outputs within this caller's skill package.

    Inspect existing parent links before any directory, lock, or temporary file
    is created. The caller supplies its own location so importing multiple skill
    copies in one Python process cannot reuse a cached installation root.
    """
    caller_path = Path(caller)
    roots = {
        Path(os.path.abspath(caller_path)).parents[1],
        caller_path.resolve().parents[1],
    }
    target = Path(path)
    locations = {Path(os.path.abspath(target)), target.resolve()}
    if any(location == root or location.is_relative_to(root)
           for location in locations for root in roots):
        raise InstalledResourceError(
            f"技能安装目录是只读资源，不能写入: {path}。请指定安装目录之外的任务输出目录。"
        )
    return target
