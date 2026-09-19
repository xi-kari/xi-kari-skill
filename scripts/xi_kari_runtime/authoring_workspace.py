"""Private authoring attempts outside system temporary and package directories."""

from contextlib import contextmanager
import os
from pathlib import Path
import shutil
import tempfile
import uuid

from .canonical_json import atomic_write_json


def failure_causes(error: BaseException) -> list[dict]:
    chain = []
    cause: BaseException | None = error
    seen: set[int] = set()
    while cause is not None and id(cause) not in seen:
        seen.add(id(cause))
        item = {"type": type(cause).__name__, "message": str(cause)}
        for field in ("errno", "winerror", "filename"):
            value = getattr(cause, field, None)
            if value is not None:
                item[field] = value
        chain.append(item)
        cause = cause.__cause__ or cause.__context__
    return chain


class AuthoringFailure(ValueError):
    """A failed authoring attempt whose diagnostic bytes remain available."""

    def __init__(self, message: str, diagnostics_path: Path):
        super().__init__(f"{message}; diagnostics: {diagnostics_path}")
        self.diagnostics_path = diagnostics_path


@contextmanager
def private_authoring_directory(*, prefix: str, repository_root: Path, runs_root: Path | None = None):
    from .materialization import default_runs_root, _require_external_runs_root

    root = Path(runs_root or default_runs_root()).expanduser().resolve()
    _require_external_runs_root(root, repository_root)
    root_existed = root.exists()
    root.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        # Preserve the host user's inherited ACE when the sandbox account owns
        # newly created output files. Windows mode 0700 instead uses OWNER RIGHTS.
        directory = root / f"{prefix}{uuid.uuid4().hex}"
        directory.mkdir()
    else:
        directory = Path(tempfile.mkdtemp(prefix=prefix, dir=root))

    def cleanup():
        directory.resolve().relative_to(root)
        shutil.rmtree(directory)

    try:
        yield directory
    except AuthoringFailure:
        cleanup()
        raise
    except Exception as error:
        atomic_write_json(directory / "failure.json", {
            "state": "failed", "error_chain": failure_causes(error),
        })
        raise AuthoringFailure(str(error), directory) from error
    else:
        cleanup()
    finally:
        if not root_existed:
            try:
                root.rmdir()
            except OSError:
                pass
