from copy import deepcopy
from importlib import import_module
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import shutil
import sys
from zipfile import ZIP_DEFLATED, ZipFile
import xml.etree.ElementTree as ET

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SOURCE = ROOT / "source" / "跨尺度多圈层结构推演框架v9.0.docx"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"


def _directory_digest(path: Path) -> str:
    digest = sha256()
    for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _generated_files(path: Path) -> dict[str, bytes]:
    return {
        item.relative_to(path).as_posix(): item.read_bytes()
        for item in path.rglob("*")
        if item.is_file()
    }


def _source_root(path: Path, source_bytes: bytes | None = None) -> Path:
    (path / "source").mkdir(parents=True)
    (path / "source" / SOURCE.name).write_bytes(
        SOURCE.read_bytes() if source_bytes is None else source_bytes
    )
    return path


def _rewrite_xml_member(source: bytes, member_name: str, mutate) -> bytes:
    with ZipFile(BytesIO(source)) as archive:
        entries = [(item, archive.read(item)) for item in archive.infolist()]
    root = ET.fromstring(dict((item.filename, payload) for item, payload in entries)[member_name])
    mutate(root)
    replacement = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for item, payload in entries:
            archive.writestr(item, replacement if item.filename == member_name else payload)
    return output.getvalue()


def test_v90_build_profile_does_not_switch_the_active_runtime() -> None:
    profile_module = import_module("scripts.xi_kari_runtime.source_profile")

    profile = profile_module.get_source_profile("v9.0")

    assert profile_module.SOURCE_VERSION == "v8.3"
    assert profile.source_version == "v9.0"
    assert profile.anchor_prefix == "V90"
    assert profile.document_name == "跨尺度多圈层结构推演框架v9.0.docx"
    assert profile.manifest_schema_path == "schemas/source-manifest-v90.schema.json"
    assert profile.candidate_schema_path == "schemas/source-candidate-v90.schema.json"


def test_v90_target_extracts_complete_source_coordinates() -> None:
    builder = import_module("build_source_snapshot")
    snapshot = builder.extract_snapshot_for_version(SOURCE.read_bytes(), "v9.0")

    assert len(snapshot.body_blocks) == 1952
    assert len(snapshot.paragraphs) == 4298
    assert sum(bool(paragraph.text.strip()) for paragraph in snapshot.paragraphs) == 4175
    assert len(snapshot.tables) == 120
    assert len(snapshot.source_unit_sequence) == 4418
    assert snapshot.paragraphs[0].anchor == "V90-P00001"
    assert snapshot.paragraphs[0].locator == "word/document.xml/body/p[1]"
    assert snapshot.body_blocks[0].anchor == "V90-B00001"
    assert snapshot.tables[0].anchor == "V90-T001"
    assert [division.title for division in snapshot.divisions] == [
        "Front matter",
        "第一部分　导读",
        "第二部分　边界与方法",
        "第三部分　通用结构语法",
        "第四部分　根假设与推论",
        "第五部分　跨尺度与跨圈层变换",
        "第六部分　运转与演化",
        "第七部分　人类结构化世界",
        "第八部分　人类状态原型",
        "第九部分　行动者状态与人格假设",
        "第十部分　多圈层对象与联合状态",
        "第十一部分　事件驱动的动态推演",
        "第十二部分　条件前瞻与有限选择",
        "第十三部分　接口与工具",
        "第十四部分　规范选择",
        "第十五部分　干涉与应用",
        "第十六部分　治理",
        "附录A　人类变量接口卡册",
        "附录B　编号体系与术语总表",
        "附录C 共同方法内核与跨学科桥接",
        "附录D　领域解释与应用图谱",
    ]


def test_v90_target_preserves_list_structure() -> None:
    builder = import_module("build_source_snapshot")
    snapshot = builder.extract_snapshot_for_version(SOURCE.read_bytes(), "v9.0")
    numbered = [paragraph.numbering for paragraph in snapshot.paragraphs if paragraph.numbering]

    assert len(numbered) == 162
    assert sum(item.num_fmt == "decimal" for item in numbered) == 23
    assert sum(item.num_fmt == "bullet" for item in numbered) == 139

    expected_decimal_groups = {
        **{f"V90-P{ordinal:05d}": index for index, ordinal in enumerate(range(692, 698), 1)},
        **{f"V90-P{ordinal:05d}": index for index, ordinal in enumerate(range(884, 888), 1)},
        **{f"V90-P{ordinal:05d}": index for index, ordinal in enumerate(range(2684, 2691), 1)},
        **{f"V90-P{ordinal:05d}": index for index, ordinal in enumerate(range(2746, 2752), 1)},
    }
    observed = {
        paragraph.anchor: paragraph.numbering.sequence_ordinal
        for paragraph in snapshot.paragraphs
        if paragraph.numbering and paragraph.numbering.num_fmt == "decimal"
    }
    assert observed == expected_decimal_groups


def test_v90_build_is_deterministic_in_two_fresh_roots(tmp_path: Path) -> None:
    builder = import_module("build_source_snapshot")
    first = _source_root(tmp_path / "first")
    second = _source_root(tmp_path / "second")

    assert builder.build(first, check=False, source_version="v9.0") == []
    assert builder.build(second, check=False, source_version="v9.0") == []

    first_files = _generated_files(first / "references" / "source" / "v9.0")
    second_files = _generated_files(second / "references" / "source" / "v9.0")
    assert first_files
    assert first_files == second_files


def test_v90_check_is_read_only_for_valid_and_tampered_snapshots(tmp_path: Path) -> None:
    builder = import_module("build_source_snapshot")
    root = _source_root(tmp_path / "check")
    assert builder.build(root, check=False, source_version="v9.0") == []
    snapshot_dir = root / "references" / "source" / "v9.0"

    before_valid = _directory_digest(snapshot_dir)
    assert builder.build(root, check=True, source_version="v9.0") == []
    assert _directory_digest(snapshot_dir) == before_valid

    tampered = snapshot_dir / "audit" / "paragraphs.jsonl"
    tampered.write_bytes(tampered.read_bytes() + b"{}\n")
    before_invalid = _directory_digest(snapshot_dir)
    errors = builder.build(root, check=True, source_version="v9.0")
    assert any("generated file differs: audit/paragraphs.jsonl" in error for error in errors)
    assert _directory_digest(snapshot_dir) == before_invalid


def test_v90_aliases_domains_and_toc_exclusion_are_explicit() -> None:
    base = ROOT / "references" / "source" / "v9.0"
    aliases = json.loads((base / "indexes" / "aliases.json").read_text(encoding="utf-8"))
    domains = json.loads((base / "indexes" / "domain-entries.json").read_text(encoding="utf-8"))
    paragraphs = [
        json.loads(line)
        for line in (base / "audit" / "paragraphs.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    candidates = [
        json.loads(line)
        for line in (base / "indexes" / "candidates.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert aliases["body_blocks"]["XK9-B01952"] == "V90-B01952"
    assert aliases["paragraphs"]["XK9-P04298"] == "V90-P04298"
    assert aliases["tables"]["XK9-T120"] == "V90-T120"
    assert [row["domain_id"] for row in domains] == [f"D.{ordinal:02d}" for ordinal in range(1, 33)]
    assert domains[0]["source_anchor"] == "V90-P04075"
    assert domains[-1]["source_anchor"] == "V90-P04292"

    toc_anchors = {row["anchor"] for row in paragraphs if row["style_id"] == "TOCItem"}
    candidate_anchors = {
        anchor for candidate in candidates for anchor in candidate["source_anchors"]
    }
    assert len(toc_anchors) == 52
    assert toc_anchors.isdisjoint(candidate_anchors)


def test_v90_wrong_raw_identity_is_rejected_before_writing(tmp_path: Path) -> None:
    builder = import_module("build_source_snapshot")

    def mutate(root: ET.Element) -> None:
        paragraph = root.find(f".//{W}p")
        assert paragraph is not None
        text = paragraph.find(f".//{W}t")
        assert text is not None
        text.text = (text.text or "") + "x"

    changed = _rewrite_xml_member(SOURCE.read_bytes(), "word/document.xml", mutate)
    root = _source_root(tmp_path / "wrong-raw", changed)
    errors = builder.build(root, check=False, source_version="v9.0")

    assert any("raw SHA256 mismatch" in error for error in errors)
    assert not (root / "references" / "source" / "v9.0").exists()


@pytest.mark.parametrize(
    ("case", "expected_fragment"),
    [
        ("move_empty", "semantic SHA256 mismatch"),
        ("move_duplicate_text", "semantic SHA256 mismatch"),
        ("remove_table", "table count mismatch"),
        ("remove_cell_paragraph", "table cell has no paragraph"),
        ("table_merge", "semantic SHA256 mismatch"),
        ("list_level", "numbering template"),
        ("numbering_restart", "list structure SHA256 mismatch"),
        ("nested_table", "nested table requires explicit extractor extension"),
        ("heading_title", "sequence differs from the pinned source profile"),
    ],
)
def test_v90_ooxml_structure_mutations_are_rejected(
    tmp_path: Path, case: str, expected_fragment: str
) -> None:
    builder = import_module("build_source_snapshot")
    source = SOURCE.read_bytes()

    if case == "move_empty":
        def mutate(root: ET.Element) -> None:
            body = root.find(f"{W}body")
            assert body is not None
            children = list(body)
            empty = next(
                child
                for child in children
                if child.tag == f"{W}p"
                and not "".join(node.text or "" for node in child.iter(f"{W}t")).strip()
            )
            body.remove(empty)
            body.insert(200, empty)

        changed = _rewrite_xml_member(source, "word/document.xml", mutate)
    elif case == "move_duplicate_text":
        def mutate(root: ET.Element) -> None:
            body = root.find(f"{W}body")
            assert body is not None
            seen: dict[str, ET.Element] = {}
            for index, child in enumerate(list(body)):
                if child.tag != f"{W}p":
                    continue
                text = "".join(node.text or "" for node in child.iter(f"{W}t"))
                if text.strip() and text in seen:
                    first = seen[text]
                    body.remove(first)
                    body.insert(index, first)
                    return
                seen[text] = child
            raise AssertionError("fixed source has no duplicate direct paragraph text")

        changed = _rewrite_xml_member(source, "word/document.xml", mutate)
    elif case == "remove_table":
        def mutate(root: ET.Element) -> None:
            body = root.find(f"{W}body")
            assert body is not None
            table = next(child for child in body if child.tag == f"{W}tbl")
            body.remove(table)

        changed = _rewrite_xml_member(source, "word/document.xml", mutate)
    elif case == "remove_cell_paragraph":
        def mutate(root: ET.Element) -> None:
            cell = next(value for value in root.iter(f"{W}tc"))
            cell.remove(cell.findall(f"{W}p")[0])

        changed = _rewrite_xml_member(source, "word/document.xml", mutate)
    elif case == "table_merge":
        def mutate(root: ET.Element) -> None:
            cell = root.find(f".//{W}tc")
            assert cell is not None
            properties = cell.find(f"{W}tcPr")
            if properties is None:
                properties = ET.Element(f"{W}tcPr")
                cell.insert(0, properties)
            grid_span = ET.SubElement(properties, f"{W}gridSpan")
            grid_span.set(f"{W}val", "2")
            vertical_merge = ET.SubElement(properties, f"{W}vMerge")
            vertical_merge.set(f"{W}val", "restart")

        changed = _rewrite_xml_member(source, "word/document.xml", mutate)
    elif case == "list_level":
        def mutate(root: ET.Element) -> None:
            ilvl = root.find(f".//{W}numPr/{W}ilvl")
            assert ilvl is not None
            ilvl.set(f"{W}val", "1")

        changed = _rewrite_xml_member(source, "word/document.xml", mutate)
    elif case == "numbering_restart":
        def mutate(root: ET.Element) -> None:
            start = root.find(f".//{W}abstractNum/{W}lvl/{W}start")
            assert start is not None
            start.set(f"{W}val", "2")

        changed = _rewrite_xml_member(source, "word/numbering.xml", mutate)
    elif case == "nested_table":
        def mutate(root: ET.Element) -> None:
            table = root.find(f".//{W}tbl")
            cell = root.find(f".//{W}tc")
            assert table is not None and cell is not None
            cell.append(deepcopy(table))

        changed = _rewrite_xml_member(source, "word/document.xml", mutate)
    else:
        def mutate(root: ET.Element) -> None:
            seen = 0
            for paragraph in root.iter(f"{W}p"):
                style = paragraph.find(f"{W}pPr/{W}pStyle")
                if style is not None and style.get(f"{W}val") == "Heading1":
                    seen += 1
                    if seen == 1:
                        continue
                    text = paragraph.find(f".//{W}t")
                    assert text is not None
                    text.text = (text.text or "") + "改"
                    return
            raise AssertionError("fixed source has no Heading1")

        changed = _rewrite_xml_member(source, "word/document.xml", mutate)

    root = _source_root(tmp_path / case, changed)
    errors = builder.build(root, check=False, source_version="v9.0")
    assert errors
    assert any(expected_fragment in error for error in errors), errors
    assert not (root / "references" / "source" / "v9.0").exists()


def test_v90_mixed_cross_volume_and_text_candidate_tampering_is_rejected(
    tmp_path: Path,
) -> None:
    checker = import_module("check_source_snapshot")
    root = tmp_path / "repo"
    shutil.copytree(ROOT, root)
    candidate_path = root / "references" / "source" / "v9.0" / "indexes" / "candidates.jsonl"
    rows = candidate_path.read_text(encoding="utf-8").splitlines()
    first = json.loads(rows[0])
    first["source_anchors"] = ["V83-P0001"]
    first["source_span"]["paragraph_anchors"] = ["V83-P0001"]
    rows[0] = json.dumps(first, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    second = json.loads(rows[1])
    second["source_anchors"] = ["V90-P04075"]
    second["source_span"] = {
        "start_anchor": "V90-P04075",
        "end_anchor": "V90-P04075",
        "paragraph_anchors": ["V90-P04075"],
    }
    rows[1] = json.dumps(second, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    third = json.loads(rows[2])
    third["source_text"] = third["source_text"] + "tampered"
    rows[2] = json.dumps(third, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    candidate_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    errors = checker.build(root, check=True, source_version="v9.0")
    errors.extend(checker.check_v90_candidate_index(root))

    assert any("generated file differs: indexes/candidates.jsonl" in error for error in errors)
    assert any("does not match '^V90-P" in error for error in errors)
    assert any("paragraph candidate span is not exact" in error for error in errors)
    assert any("source_text differs from exact paragraph" in error for error in errors)
    assert any("semantic fingerprint differs from source payload" in error for error in errors)


def test_v90_duplicate_source_unit_is_rejected(tmp_path: Path) -> None:
    checker = import_module("check_source_snapshot")
    root = tmp_path / "repo"
    shutil.copytree(ROOT, root)
    manifest_path = root / "references" / "source" / "v9.0" / "source-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_unit_sequence"][1] = manifest["source_unit_sequence"][0]
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    errors = checker.build(root, check=True, source_version="v9.0")
    errors.extend(checker.check_v90_source_units(root))

    assert any("generated file differs: source-manifest.json" in error for error in errors)
    assert any("source unit sequence differs from body/table document order" in error for error in errors)
    assert any("source unit sequence contains duplicates" in error for error in errors)
