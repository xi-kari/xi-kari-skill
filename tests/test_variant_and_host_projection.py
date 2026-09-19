from copy import deepcopy

import pytest

from scripts.xi_kari_runtime import authoring, semantic_probe
from scripts.xi_kari_runtime.semantic_projection import substantive_semantic_atoms


def variant(monkeypatch, omitted):
    semantic = {field: {} for field in authoring.SEMANTIC_AUTHORING_FIELDS if field != omitted}
    authored = {"semantic_packet": semantic}
    monkeypatch.setattr(semantic_probe, "validate_semantic_probe_authorings", lambda *args, **kwargs: {"stance-support": authored})
    monkeypatch.setattr(semantic_probe, "build_variant_contract", lambda *args, **kwargs: {
        "problem_contract_sha256": "1" * 64, "stance_neutrality_key": "2" * 64,
    })
    before = deepcopy(semantic)
    result = semantic_probe._variant(
        {"runtime_binding": {}}, {}, {}, {}, {}, "0" * 64,
        requested_stance="support", time_window=None,
    )
    assert semantic == before
    return result[0]


@pytest.mark.parametrize("omitted", ["answer_delivery", "framework_gap"])
def test_optional_variant_fields_are_normalized_without_truncating(monkeypatch, omitted):
    result = variant(monkeypatch, omitted)
    assert result[omitted] is None
    assert "reader_sections" in result


def test_required_variant_content_is_still_mandatory(monkeypatch):
    with pytest.raises(ValueError, match="reader_sections"):
        variant(monkeypatch, "reader_sections")


def test_runtime_host_capture_metadata_is_not_an_authored_argument():
    payload = {"retrieval": {"sources": [{
        "source_id": "SOURCE-A", "title": "事实材料", "content": "材料正文",
        "host_observation": {
            "status": "captured", "response_status": 200, "peer_ip": "192.0.2.1",
            "text_character_count": 4, "excerpt_start": 0, "excerpt_end": 4,
        },
    }], "assessments": [{"cannot_prove": ["该材料不能证明行为人的动机。"]}]}}
    paths = {atom["canonical_path"] for atom in substantive_semantic_atoms(payload)}
    assert not any("host_observation" in path for path in paths)
    assert "retrieval.assessments[0].cannot_prove[0]" in paths
