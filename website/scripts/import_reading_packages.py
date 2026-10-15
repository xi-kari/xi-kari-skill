"""Import source-aligned reading packages without executing their contents."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import unicodedata
from urllib.parse import urlsplit
import zipfile


class ImportValidationError(ValueError):
    """A package cannot be imported without changing or losing its identity."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def checked_member(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if (
        not name
        or "\\" in name
        or ":" in name
        or path.is_absolute()
        or any(part in {".", ".."} for part in name.split("/"))
    ):
        raise ImportValidationError(f"Unsafe archive path: {name!r}")
    return path


def read_archive(path: Path) -> dict[str, bytes]:
    members: dict[str, bytes] = {}
    with zipfile.ZipFile(path) as archive:
        for entry in archive.infolist():
            checked_member(entry.filename)
            if stat.S_ISLNK(entry.external_attr >> 16):
                raise ImportValidationError(f"Archive symlink: {entry.filename}")
            if entry.is_dir():
                continue
            if entry.filename in members:
                raise ImportValidationError(f"Repeated archive member: {entry.filename}")
            if entry.file_size > 64 * 1024 * 1024:
                raise ImportValidationError(f"Oversized archive member: {entry.filename}")
            members[entry.filename] = archive.read(entry)
    return members


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ImportValidationError(message)


def text_leaves(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from text_leaves(item)
    elif isinstance(value, list):
        for item in value:
            yield from text_leaves(item)


def plain(text: str) -> str:
    return re.sub(r"[\s#*_`|>\[\](){}]+", "", unicodedata.normalize("NFKC", text))


def lecture_residuals(text: str, data: dict, sources: dict) -> list[dict]:
    """Find long text not substantially represented in structured fields."""
    leaves = sorted({plain(s) for s in text_leaves([data, sources]) if len(plain(s)) >= 12}, key=len, reverse=True)
    result = []
    for line_number, line in enumerate(text.splitlines(), 1):
        normalized = plain(line)
        if len(normalized) < 90 or line.startswith("#"):
            continue
        remaining = normalized
        for leaf in leaves:
            if leaf in remaining:
                remaining = remaining.replace(leaf, "")
        if len(remaining) >= 80 and len(remaining) / len(normalized) > 0.2:
            result.append({"line": line_number, "text": line, "unmatched_characters": len(remaining)})
    return result


def import_packages(packages_dir: Path, repository: Path, report_dir: Path) -> dict:
    units_doc = json.loads((repository / "website/content/reading-units.json").read_text(encoding="utf-8"))
    units = {unit["lesson_key"]: unit for unit in units_doc["units"]}
    require(len(units) == len(units_doc["units"]), "Reading units contain duplicate keys")
    theory_path = repository / "source/Xikari-条件结构与转化论.md"
    theory = theory_path.read_bytes()
    source_hash = sha256(theory)
    require(source_hash == units_doc["source_sha256"], "Reading units do not match the current theory")
    lines = theory.splitlines(keepends=True)
    require(len(lines) == units_doc["source_lines"], "Theory line count does not match reading units")
    task_units: dict[str, list[dict]] = {}
    covered_lines = []
    for unit in units.values():
        task_units.setdefault(unit["task_id"], []).append(unit)
        covered_lines.extend(range(unit["source_start_line"], unit["source_end_line"] + 1))
        fragment = b"".join(lines[unit["source_start_line"] - 1:unit["source_end_line"]])
        require(sha256(fragment) == unit["source_sha256"], f"Source fragment mismatch: {unit['lesson_key']}")
    require(sorted(covered_lines) == list(range(1, len(lines) + 1)), "Reading units must cover every source line exactly once")

    lessons = {}
    planned_assets: dict[str, bytes] = {"theory.md": theory}
    package_digests = {}
    package_records = []
    duplicate_records = []
    ignored_records = []
    residual_records = []
    errors = []
    counts = {}

    for path in sorted(packages_dir.glob("*.zip"), key=lambda p: ("(" in p.name, p.name)):
        try:
            members = read_archive(path)
            section_paths = [name for name in members if PurePosixPath(name).name == "sections.json"]
            if not section_paths:
                ignored_records.append({"archive": path.name, "sha256": sha256(path.read_bytes()), "files": len(members), "crc": "passed"})
                continue
            require(len(section_paths) == 1, f"Ambiguous sections.json: {path.name}")
            section_path = section_paths[0]
            prefix = str(PurePosixPath(section_path).parent) + "/"
            if prefix == "./":
                prefix = ""
            data = json.loads(members[section_path])
            task_id = data["taskId"]
            require(task_id in task_units, f"Unknown task: {task_id}")
            require(re.fullmatch(r"[A-Za-z0-9-]+", task_id) is not None, f"Unsafe task ID: {task_id}")
            digest = {name[len(prefix):] if name.startswith(prefix) else name: sha256(body) for name, body in members.items()}
            if task_id in package_digests:
                previous = package_digests[task_id]
                require(digest == previous["members"], f"Conflicting duplicate task: {task_id}")
                duplicate_records.append({"task_id": task_id, "archive": path.name, "same_as": previous["archive"], "sha256": sha256(path.read_bytes())})
                continue

            require(data["sourceSha256"] == source_hash, f"Wrong source identity: {task_id}")
            package_lessons = data["lessons"]
            expected = {unit["lesson_key"] for unit in task_units[task_id]}
            require(set(package_lessons) == expected, f"Unit coverage mismatch: {task_id}")
            theory_members = [name for name in members if name in {prefix + "source/theory.md", prefix + "source/Xikari-条件结构与转化论.md"}]
            require(len(theory_members) == 1, f"Missing or ambiguous full theory: {task_id}")
            require(sha256(members[theory_members[0]]) == source_hash, f"Full theory bytes differ: {task_id}")
            slice_members = [name for name in members if name in {prefix + "source-slice.md", prefix + f"source/{task_id}.md"}]
            require(len(slice_members) == 1, f"Missing or ambiguous source slice: {task_id}")
            start = min(unit["source_start_line"] for unit in task_units[task_id])
            end = max(unit["source_end_line"] for unit in task_units[task_id])
            require(members[slice_members[0]] == b"".join(lines[start - 1:end]), f"Source slice bytes differ: {task_id}")

            source_data = json.loads(members[prefix + "sources.json"])
            lecture = members[prefix + "lecture.md"].decode("utf-8")
            residual = lecture_residuals(lecture, data, source_data)
            residual_records.append({"task_id": task_id, "archive": path.name, "candidates": residual})

            local_assets = {}
            replacements = {}
            for name, body in members.items():
                if not name.startswith(prefix):
                    continue
                relative = name[len(prefix):]
                if name == theory_members[0]:
                    replacements[relative] = "/reading-assets/theory.md"
                elif relative in {"lecture.md", "diagrams.md"} or name == slice_members[0] or PurePosixPath(relative).suffix.lower() in {".png", ".csv", ".txt"}:
                    checked_member(relative)
                    if relative.endswith(".png"):
                        require(body.startswith(b"\x89PNG\r\n\x1a\n"), f"Invalid PNG signature: {name}")
                    output_name = f"{task_id}/{relative}"
                    local_assets[output_name] = body
                    replacements[relative] = "/reading-assets/" + output_name

            def public_url(url: str) -> str:
                if not url:
                    return url
                parsed = urlsplit(url)
                if parsed.scheme or parsed.netloc:
                    require(parsed.scheme in {"https", "http"} and bool(parsed.netloc), f"Unsafe URL in {task_id}: {url}")
                    return url
                if url.startswith("#"):
                    return url
                raw_path = parsed.path
                require(raw_path in replacements, f"Missing local asset in {task_id}: {url}")
                suffix = ("?" + parsed.query if parsed.query else "") + ("#" + parsed.fragment if parsed.fragment else "")
                return replacements[raw_path] + suffix

            sources = copy.deepcopy(source_data["sources"])
            for source in sources:
                source["url"] = public_url(source["url"])
            local_lessons = {}
            for key, original in package_lessons.items():
                unit = units[key]
                require(original["outputId"] == unit["output_id"], f"Output ID mismatch: {task_id}/{key}")
                require(original["sourceHash"] == source_hash, f"Lesson source mismatch: {task_id}/{key}")
                own_ref = any(
                    ref.get("section") in {key, unit["output_id"]}
                    and ref.get("start_line", ref.get("startLine")) == unit["source_start_line"]
                    and ref.get("end_line", ref.get("endLine")) == unit["source_end_line"]
                    for ref in original["sourceRefs"]
                )
                require(own_ref, f"Lesson source range mismatch: {task_id}/{key}")
                lesson = copy.deepcopy(original)
                for ref in lesson["sourceRefs"]:
                    ref["startLine"] = ref.get("start_line", ref.get("startLine"))
                    ref["endLine"] = ref.get("end_line", ref.get("endLine"))
                if lesson.get("diagramPath"):
                    lesson["diagramPath"] = public_url(lesson["diagramPath"])
                for figure in lesson.get("figures", []):
                    figure["path"] = public_url(figure["path"])
                for link in lesson.get("caseLinks", []):
                    link["href"] = public_url(link["href"])
                for case in lesson.get("caseNotes", []):
                    for field in ("href", "sourceUrl"):
                        if case.get(field):
                            case[field] = public_url(case[field])
                lesson["taskId"] = task_id
                lesson["sources"] = sources
                lesson["lecturePath"] = replacements["lecture.md"]
                lesson["sourcesPath"] = f"/reading-assets/{task_id}/sources.json"
                lesson["sourceSlicePath"] = replacements[slice_members[0][len(prefix):]]
                lesson["supplementaryFiles"] = [
                    {"title": PurePosixPath(relative).name, "path": target}
                    for relative, target in replacements.items()
                    if PurePosixPath(relative).suffix.lower() in {".csv", ".txt"}
                ]
                if "diagrams.md" in replacements:
                    lesson["diagramsPath"] = replacements["diagrams.md"]
                local_lessons[key] = lesson
                for field, value in original.items():
                    if isinstance(value, list):
                        counts[field] = counts.get(field, 0) + len(value)

            # Only destinations in Markdown links change; prose remains as supplied.
            for name, body in list(local_assets.items()):
                if not name.endswith(".md") or name.endswith(slice_members[0][len(prefix):]):
                    continue
                markdown = body.decode("utf-8")
                for relative, target in sorted(replacements.items(), key=lambda pair: len(pair[0]), reverse=True):
                    markdown = markdown.replace(f"]({relative})", f"]({target})")
                local_assets[name] = markdown.encode("utf-8")

            rewritten_sources = copy.deepcopy(source_data)
            rewritten_sources["sources"] = sources
            local_assets[f"{task_id}/sources.json"] = json_bytes(rewritten_sources)
            record = {
                "task_id": task_id,
                "archive": path.name,
                "sha256": sha256(path.read_bytes()),
                "members": len(members),
                "crc": "passed",
                "source_sha256": source_hash,
                "source_start_line": start,
                "source_end_line": end,
                "lesson_keys": list(package_lessons),
                "source_entries": len(sources),
                "lecture_bytes": len(members[prefix + "lecture.md"]),
                "lecture_sha256": sha256(members[prefix + "lecture.md"]),
                "lecture_difference_candidates": len(residual),
                "assets": {name: sha256(body) for name, body in local_assets.items()},
                "original_member_sha256": digest,
            }
            package_records.append(record)
            package_digests[task_id] = {"archive": path.name, "members": digest}
            lessons.update(local_lessons)
            planned_assets.update(local_assets)
        except (ImportValidationError, KeyError, ValueError, UnicodeError, zipfile.BadZipFile) as error:
            errors.append({"archive": path.name, "error": str(error)})

    missing = sorted(set(units) - set(lessons))
    if missing:
        errors.append({"missing_units": missing})
    expected_tasks = set(task_units)
    if set(package_digests) != expected_tasks:
        errors.append({"missing_tasks": sorted(expected_tasks - set(package_digests))})
    report = {
        "source_sha256": source_hash,
        "archive_count": len(list(packages_dir.glob("*.zip"))),
        "task_count": len(package_records),
        "lesson_count": len(lessons),
        "expected_task_count": len(task_units),
        "expected_lesson_count": len(units),
        "source_lines": len(lines),
        "content_counts": counts,
        "source_entries": sum(record["source_entries"] for record in package_records),
        "asset_count": len(planned_assets),
        "asset_bytes": sum(map(len, planned_assets.values())),
        "packages": package_records,
        "duplicates": duplicate_records,
        "excluded_archives": ignored_records,
        "errors": errors,
        "verification_scope": "Archive integrity, source identity, unit mapping, source ranges and content preservation; not a theory or factual peer review.",
    }
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "import-manifest.json").write_bytes(json_bytes(report))
    (report_dir / "lecture-difference-candidates.json").write_bytes(json_bytes(residual_records))
    if errors:
        raise ImportValidationError(f"Import rejected; inspect {report_dir / 'import-manifest.json'}")

    target_assets = repository / "website/public/reading-assets"
    for relative, body in planned_assets.items():
        destination = target_assets.joinpath(*checked_member(relative).parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(body)
    ordered = {key: lessons[key] for key in units}
    destination = repository / "website/content/section-lessons.json"
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_bytes(json_bytes({"lessons": ordered}))
    temporary.replace(destination)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packages", type=Path)
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--report-dir", type=Path, required=True)
    arguments = parser.parse_args()
    report = import_packages(arguments.packages, arguments.repository, arguments.report_dir)
    summary = {key: report[key] for key in ("archive_count", "task_count", "lesson_count", "asset_count", "asset_bytes", "content_counts")}
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
