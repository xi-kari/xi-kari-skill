from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import pytest


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA256 = "ffc45afdc288ecd268fd02e46d47318b7ddf17bf7b47605aa6c413c95398544b"
E3_POSITIVE = "只有观察、命名、评分或发布与对象发生实际因果耦合时，才登记观测参与。"
E3_BOUNDARY = (
    "仅有时序先后或“被观察会改变对象”的机制故事不足以通过；"
    "必须定位通道，并建立未观测、替代观测或阻断反事实。"
)


def _e3_identity() -> dict:
    register = json.loads(
        (ROOT / "references/ontology/v9.0/authored/identity-register.json").read_text(
            encoding="utf-8"
        )
    )
    return next(row for row in register["identities"] if row["source_concept_id"] == "E3")


def test_e3_boundary_is_bound_to_the_locked_docx_paragraph() -> None:
    source = ROOT / "source/跨尺度多圈层结构推演框架v9.0.docx"
    assert sha256(source.read_bytes()).hexdigest() == SOURCE_SHA256
    with ZipFile(source) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
    namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = document.findall("w:body/w:p", namespaces)
    title = "".join(paragraphs[327].itertext())
    text = "".join(paragraphs[328].itertext())
    assert title == "4.8.3　E3 条件性观测参与"
    assert text == E3_POSITIVE + E3_BOUNDARY
    identity = _e3_identity()
    assert identity["source_layer"]["source_anchors"] == ["V90-P00445", "V90-P00446"]
    assert identity["source_layer"]["source_refs"][1]["text"] == text


@pytest.mark.parametrize("boundary_kind", ["interpretation", "acceptance", "migration"])
def test_e3_authored_boundaries_preserve_its_observation_conditions(boundary_kind: str) -> None:
    identity = _e3_identity()
    boundaries = {
        "interpretation": identity["interpretation_layer"]["negative_boundary"],
        "acceptance": identity["interpretation_layer"]["acceptance"]["negative"],
        "migration": identity["legacy_identity_decision"]["boundary"],
    }
    assert boundaries[boundary_kind] == E3_BOUNDARY


@pytest.mark.parametrize(
    ("relative", "prefix"),
    [
        ("references/ontology/v9.0/cards/e3.md", "禁止边界："),
        ("references/learning-packs/v9.0/02-evidence-qualification.md", "- `E3`："),
        ("references/learning-packs/v9.0/09-dependency-roles.md", "- `E3`："),
    ],
)
def test_e3_reader_boundaries_preserve_its_observation_conditions(relative: str, prefix: str) -> None:
    text = (ROOT / relative).read_text(encoding="utf-8")
    boundaries = [line.removeprefix(prefix) for line in text.splitlines() if line.startswith(prefix)]
    assert boundaries == [E3_BOUNDARY]


def test_e3_generated_migration_boundary_preserves_its_observation_conditions() -> None:
    migration = json.loads(
        (ROOT / "references/ontology/v9.0/concept-migration-map.json").read_text(encoding="utf-8")
    )
    identity = next(row for row in migration["preserved_identities"] if row["source_concept_id"] == "E3")
    assert identity["legacy_identity_decision"]["boundary"] == E3_BOUNDARY
