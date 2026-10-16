"""Preserve manuscript branches and combine explicit, non-overlapping edits."""

from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass
import difflib
import hashlib
import io
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from xikari_paths import require_external_output
finally:
    sys.path.pop(0)


SNAPSHOT_INDEX = ".manuscript-snapshot.json"


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def check_new_file(path: Path) -> None:
    require_external_output(path, __file__)
    if path.exists() or path.is_symlink():
        raise ValueError(f"Output already exists: {path}")
    if not path.parent.is_dir():
        raise ValueError(f"Output parent directory does not exist: {path.parent}")


def write_new(path: Path, data: bytes) -> None:
    check_new_file(path)
    with path.open("xb") as stream:
        stream.write(data)


def read_text(path: Path) -> str:
    # Decode bytes directly: TextIO newline conversion would destroy CRLF.
    return path.read_bytes().decode("utf-8")


def physical_lines(text: str) -> list[str]:
    return list(io.StringIO(text, newline=""))


def snapshot(root: Path, files: list[str], output: Path) -> dict:
    require_external_output(output, __file__)
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"Snapshot root is not a directory: {root}")
    if output.exists() or output.is_symlink():
        raise ValueError(f"Snapshot directory already exists: {output}")
    if not output.parent.is_dir():
        raise ValueError(f"Snapshot parent directory does not exist: {output.parent}")
    if not files:
        raise ValueError("Select at least one file")
    selected = []
    seen = set()
    for name in files:
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError(f"File must be a path within the root: {name}")
        source = (root / relative).resolve(strict=True)
        if not source.is_relative_to(root) or not source.is_file():
            raise ValueError(f"File resolves outside the root or is not a file: {name}")
        if relative == Path(SNAPSHOT_INDEX) or relative in seen:
            raise ValueError(f"Duplicate or reserved snapshot path: {name}")
        seen.add(relative)
        selected.append((relative, source.read_bytes()))
    # Read every selected file before creating a directory; no recursive copy.
    records = [
        {"path": path.as_posix(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        for path, data in selected
    ]
    index = {"schema_version": 1, "source_root": str(root), "files": records}
    output.mkdir()
    created_files = []
    created_dirs = [output]
    try:
        for relative, data in selected:
            target = output / relative
            parents = []
            cursor = target.parent
            while cursor != output and not cursor.exists():
                parents.append(cursor)
                cursor = cursor.parent
            for directory in reversed(parents):
                directory.mkdir()
                created_dirs.append(directory)
            write_new(target, data)
            created_files.append(target)
        write_new(output / SNAPSHOT_INDEX, json_bytes(index))
        created_files.append(output / SNAPSHOT_INDEX)
    except OSError:
        # Only remove entries created here, never recursively remove a directory.
        for path in reversed(created_files):
            path.unlink(missing_ok=True)
        for directory in reversed(created_dirs):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise
    return {"snapshot": str(output.resolve()), "files": len(selected)}


def compare(current: Path, candidate: Path, output: Path) -> dict:
    check_new_file(output)
    left, right = read_text(current), read_text(candidate)
    lines = difflib.unified_diff(
        physical_lines(left), physical_lines(right),
        fromfile=str(current), tofile=str(candidate), lineterm="\n",
    )
    chunks = []
    for line in lines:
        chunks.append(line)
        if not line.endswith(("\n", "\r")):
            chunks.append("\n\\ No newline at end of file\n")
    write_new(output, "".join(chunks).encode("utf-8"))
    return {"different": left != right, "diff": str(output.resolve())}


@dataclass(frozen=True)
class Edit:
    start: int
    end: int
    replacement: tuple[str, ...]

    def as_dict(self) -> dict:
        return {
            "base_start_line": self.start + 1,
            "base_end_line_exclusive": self.end + 1,
            "replacement": "".join(self.replacement),
        }


def edits(base: list[str], variant: list[str]) -> list[Edit]:
    matcher = difflib.SequenceMatcher(None, base, variant, autojunk=False)
    return [
        Edit(i1, i2, tuple(variant[j1:j2]))
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
        if tag != "equal"
    ]


def overlaps(left: Edit, right: Edit) -> bool:
    if left.start == left.end:
        # An insertion at a changed range's boundary has ambiguous ordering.
        return right.start <= left.start <= right.end
    if right.start == right.end:
        return left.start <= right.start <= left.end
    return max(left.start, right.start) < min(left.end, right.end)


def merge_text(base: str, current: str, candidate: str) -> tuple[str | None, list[dict]]:
    if current == candidate:
        return current, []
    if current == base:
        return candidate, []
    if candidate == base:
        return current, []
    original = physical_lines(base)
    current_edits = edits(original, physical_lines(current))
    candidate_edits = edits(original, physical_lines(candidate))
    conflicts = []
    for left in current_edits:
        for right in candidate_edits:
            if left != right and overlaps(left, right):
                start, end = min(left.start, right.start), max(left.end, right.end)
                conflicts.append({
                    "base_start_line": start + 1,
                    "base_end_line_exclusive": end + 1,
                    "base_text": "".join(original[start:end]),
                    "current_edit": left.as_dict(),
                    "candidate_edit": right.as_dict(),
                })
    if conflicts:
        return None, conflicts
    combined = sorted(set(current_edits + candidate_edits), key=lambda edit: (edit.start, edit.end))
    pieces = []
    cursor = 0
    for edit in combined:
        pieces.extend(original[cursor:edit.start])
        pieces.extend(edit.replacement)
        cursor = edit.end
    pieces.extend(original[cursor:])
    return "".join(pieces), []


def merge(base: Path, current: Path, candidate: Path, output: Path, conflict_output: Path | None = None) -> dict:
    check_new_file(output)
    if conflict_output is not None:
        check_new_file(conflict_output)
        if conflict_output.resolve() == output.resolve():
            raise ValueError("Conflict report and merged manuscript must use different output paths")
    merged, conflicts = merge_text(read_text(base), read_text(current), read_text(candidate))
    if conflicts:
        report = {
            "status": "conflict", "merged_output_written": False,
            "base": str(base.resolve()), "current": str(current.resolve()),
            "candidate": str(candidate.resolve()), "conflicts": conflicts,
        }
        if conflict_output is not None:
            write_new(conflict_output, json_bytes(report))
            report["conflict_report"] = str(conflict_output.resolve())
        return report
    write_new(output, merged.encode("utf-8"))
    return {"status": "merged", "output": str(output.resolve())}


def load_links(path: Path) -> tuple[dict, dict]:
    value = json.loads(read_text(path).lstrip("\ufeff"))
    if not isinstance(value, dict) or not isinstance(value.get("nodes"), list) or not isinstance(value.get("links"), list):
        raise ValueError("Links file must contain nodes and links arrays")
    nodes = {}
    for node in value["nodes"]:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str) or not node["id"].strip():
            raise ValueError("Every node must have a nonempty string id")
        if node["id"] in nodes:
            raise ValueError(f"Duplicate node id: {node['id']}")
        location = node.get("location")
        if not isinstance(location, dict) or not isinstance(location.get("path"), str) or not location["path"].strip():
            raise ValueError(f"Node needs a location.path: {node['id']}")
        if "line" in location and (type(location["line"]) is not int or location["line"] < 1):
            raise ValueError(f"Node location.line must be a positive integer: {node['id']}")
        for field in ("heading", "anchor"):
            if field in location and not isinstance(location[field], str):
                raise ValueError(f"Node location.{field} must be a string: {node['id']}")
        if "label" in node and not isinstance(node["label"], str):
            raise ValueError(f"Node label must be a string: {node['id']}")
        nodes[node["id"]] = node
    adjacency = {key: [] for key in nodes}
    for link in value["links"]:
        if not isinstance(link, dict):
            raise ValueError("Each link must be an object with source and dependent")
        source, dependent = link.get("source"), link.get("dependent")
        if not isinstance(source, str) or not isinstance(dependent, str) or source not in nodes or dependent not in nodes:
            raise ValueError(f"Link refers to an unknown node: {source!r} -> {dependent!r}")
        if dependent not in adjacency[source]:
            adjacency[source].append(dependent)
    return nodes, adjacency


def affected(links: Path, changed: list[str]) -> dict:
    nodes, adjacency = load_links(links)
    origins = list(dict.fromkeys(changed))
    if not origins:
        raise ValueError("Specify at least one changed node")
    for origin in origins:
        if origin not in nodes:
            raise ValueError(f"Unknown changed node: {origin}")
    paths = {key: [] for key in nodes}
    for origin in origins:
        visited = {origin}
        queue = deque([(origin, [origin])])
        while queue:
            key, route = queue.popleft()
            for dependent in adjacency[key]:
                if dependent in visited:
                    continue
                visited.add(dependent)
                next_route = route + [dependent]
                paths[dependent].append({"changed": origin, "path": next_route})
                queue.append((dependent, next_route))
    return {
        "scope": "explicit_dependencies_only",
        "changed": [nodes[key] for key in origins],
        "affected": [dict(node, reached_by=paths[key]) for key, node in nodes.items() if paths[key] and key not in origins],
        "note": "Only declared dependencies are listed. Read the actual manuscript to assess semantic effects and branch adoption.",
    }


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    commands = argument_parser.add_subparsers(dest="command", required=True)
    snapshot_parser = commands.add_parser("snapshot", help="Copy explicitly selected files into a new directory")
    snapshot_parser.add_argument("--root", type=Path, required=True)
    snapshot_parser.add_argument("--file", action="append", required=True, dest="files")
    snapshot_parser.add_argument("--output-dir", type=Path, required=True)
    compare_parser = commands.add_parser("compare", help="Write a unified text diff")
    compare_parser.add_argument("--current", type=Path, required=True)
    compare_parser.add_argument("--candidate", type=Path, required=True)
    compare_parser.add_argument("--output", type=Path, required=True)
    merge_parser = commands.add_parser("merge", help="Combine non-overlapping changes from a common base")
    for name in ("base", "current", "candidate", "output"):
        merge_parser.add_argument(f"--{name}", type=Path, required=True)
    merge_parser.add_argument("--conflicts", type=Path)
    affected_parser = commands.add_parser("affected", help="Follow explicitly declared dependencies")
    affected_parser.add_argument("--links", type=Path, required=True)
    affected_parser.add_argument("--changed", action="append", required=True)
    affected_parser.add_argument("--output", type=Path)
    return argument_parser


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "snapshot":
            result = snapshot(args.root, args.files, args.output_dir)
        elif args.command == "compare":
            result = compare(args.current, args.candidate, args.output)
        elif args.command == "merge":
            result = merge(args.base, args.current, args.candidate, args.output, args.conflicts)
        else:
            result = affected(args.links, args.changed)
            if args.output is not None:
                write_new(args.output, json_bytes(result))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result.get("status") == "conflict" else 0
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
