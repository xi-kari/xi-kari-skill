"""Build the explicit Xikari skill payload for Windows hosts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def selected_files(root: Path) -> tuple[dict, list[str]]:
    metadata = json.loads((root / "skill-package.json").read_text(encoding="utf-8"))
    files = metadata["files"]
    if not files or len(files) != len(set(name.casefold() for name in files)):
        raise ValueError("Package paths must be nonempty and unique")
    for name in files:
        relative = PurePosixPath(name)
        target = (root / name).resolve()
        if relative.is_absolute() or ".." in relative.parts or "\\" in name or ":" in name:
            raise ValueError(f"Invalid package path: {name}")
        if not target.is_relative_to(root.resolve()) or not target.is_file():
            raise ValueError(f"Missing or external package file: {name}")
    return metadata, sorted(files)


def build(root: Path, output: Path) -> dict:
    metadata, names = selected_files(root)
    payload = {name: (root / name).read_bytes() for name in names}
    source_manifest = json.loads(payload["source/source-manifest.json"])
    source = payload["source/" + source_manifest["source_file"]]
    if hashlib.sha256(source).hexdigest() != source_manifest["sha256"]:
        raise ValueError("Theory source does not match its manifest")
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"xi-kari-skill-{metadata['version']}-windows.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in payload.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 13, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, data)
    raw = archive.read_bytes()
    manifest = {
        "name": metadata["name"], "version": metadata["version"],
        "archive": archive.name, "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw), "file_count": len(payload),
        "theory_source_sha256": source_manifest["sha256"],
        "files": [{"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                  for name, data in payload.items()]
    }
    (output / "install-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "SHA256SUMS").write_text(f"{manifest['sha256']}  {archive.name}\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(ROOT, args.output)
    print(json.dumps({k: v for k, v in result.items() if k != "files"}, ensure_ascii=False))
