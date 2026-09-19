import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from xi_kari_runtime import execution
from xi_kari_runtime.authoring import _validate_provider_execution
from xi_kari_runtime.canonical_json import sha256_bytes
from xi_kari_runtime.output_transport import OUTPUT_TRANSPORT
from xi_kari_runtime.output_transport import parse_provider_events
from xi_kari_runtime.retrieval_execution import _event_stream


@pytest.mark.parametrize("parser", [parse_provider_events, _event_stream])
@pytest.mark.parametrize("event", [
    {"type": "error", "message": "Reconnecting... 2/5 (stream disconnected before completion: tls handshake eof)"},
    {"type": "item.completed", "item": {"id": "notice", "type": "error", "message": "Skill descriptions were shortened to fit the skills context budget. Codex can still see every skill, but some descriptions are shorter. Disable unused skills or plugins to leave more room for the rest."}},
])
def test_completed_provider_turn_retains_recovered_transport_and_skill_notices(parser, event):
    web = {"type": "item.completed", "item": {"id": "search-1", "type": "web_search", "query": "fixture", "action": {"type": "search", "query": "fixture"}}}
    events = [{"type": "thread.started", "thread_id": "recovered"}, {"type": "turn.started"}, web, event, {"type": "turn.completed"}]
    raw = b"\n".join(json.dumps(row).encode() for row in events) + b"\n"
    assert parser(raw)[0] == "recovered"
    assert parser(raw)[1] == events
    with pytest.raises(ValueError):
        parser(b"\n".join(json.dumps(row).encode() for row in events[:-1]))


@pytest.mark.parametrize("parser", [parse_provider_events, _event_stream])
@pytest.mark.parametrize("event", [
    {"type": "turn.failed", "error": {"message": "quota exceeded"}},
    {"type": "error", "message": "authentication failed"},
    {"type": "item.completed", "item": {"id": "failure", "type": "error", "message": "unrecognized provider error"}},
])
def test_completed_marker_does_not_override_a_real_provider_failure(parser, event):
    events = [{"type": "thread.started", "thread_id": "failed"}, {"type": "turn.started"}, event, {"type": "turn.completed"}]
    with pytest.raises(ValueError):
        parser(b"\n".join(json.dumps(row).encode() for row in events))


def read_output(workspace, notice=b"SEMANTIC_OUTPUT_READY", limit=16 * 1024 * 1024):
    return execution.read_semantic_output(workspace, notice=notice, limit=limit)


def test_large_complete_json_is_read_from_the_fixed_file(tmp_path):
    payload = {"sections": [{"text": "完整保留条件、反例、机制和结论。" * 5000} for _ in range(12)]}
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    assert len(raw) > 1024 * 1024
    (tmp_path / "semantic-output.json").write_bytes(raw)
    assert read_output(tmp_path) == raw


def test_missing_file_cannot_be_replaced_by_inline_final_json(tmp_path):
    with pytest.raises(ValueError, match="notice|unavailable|missing"):
        read_output(tmp_path, notice=b'{"semantic_packet":{}}')
    assert not list(tmp_path.iterdir())


def test_other_filename_and_model_chosen_path_are_not_accepted(tmp_path):
    (tmp_path / "elsewhere.json").write_text('{"complete":true}', encoding="utf-8")
    with pytest.raises(ValueError, match="unavailable|missing"):
        read_output(tmp_path)
    with pytest.raises(ValueError, match="notice"):
        read_output(tmp_path, notice=b'{"path":"elsewhere.json"}')


@pytest.mark.parametrize("raw", [b'{"section":', b'[1,2]', b'{"x":1,"x":2}', b'{"x":NaN}'])
def test_truncated_or_non_object_or_ambiguous_json_is_rejected(tmp_path, raw):
    (tmp_path / "semantic-output.json").write_bytes(raw)
    with pytest.raises(ValueError, match="JSON|object"):
        read_output(tmp_path)


def test_output_size_limit_is_checked_before_parsing(tmp_path):
    (tmp_path / "semantic-output.json").write_text('{"text":"too long"}', encoding="utf-8")
    with pytest.raises(ValueError, match="size limit"):
        read_output(tmp_path, limit=8)


def test_output_symlink_is_rejected(tmp_path):
    target = tmp_path / "other.json"
    target.write_text('{"text":"outside target"}', encoding="utf-8")
    try:
        (tmp_path / "semantic-output.json").symlink_to(target)
    except OSError as error:
        pytest.skip(f"Host does not allow symlink creation: {error}")
    with pytest.raises(ValueError, match="symlink|reparse"):
        read_output(tmp_path)


def test_directory_at_output_path_is_rejected(tmp_path):
    (tmp_path / "semantic-output.json").mkdir()
    with pytest.raises(ValueError, match="regular file"):
        read_output(tmp_path)


def test_windows_reparse_point_is_rejected_before_file_open(tmp_path, monkeypatch):
    original = Path.lstat
    def inspect(path):
        if path.name == "semantic-output.json":
            return SimpleNamespace(st_mode=0o100600, st_file_attributes=0x400)
        return original(path)
    monkeypatch.setattr(Path, "lstat", inspect)
    with pytest.raises(ValueError, match="reparse"):
        read_output(tmp_path)


def provider_receipt():
    payload = {"reader_sections": ["Full argument"], "answer_delivery": None}
    raw = json.dumps(payload).encode()
    events = b'{"type":"thread.started","thread_id":"thread-1"}\n{"type":"turn.started"}\n{"type":"turn.completed"}\n'
    return payload, {
        "protocol": OUTPUT_TRANSPORT, "provider_parent_pid": 123, "provider_child_pid": 456,
        "exit_status": 0, "thread_id": "thread-1", "events": events.decode(), "events_sha256": sha256_bytes(events),
        "semantic_file_content": raw.decode(), "semantic_file_sha256": sha256_bytes(raw), "semantic_file_byte_count": len(raw),
    }


def test_provider_receipt_binds_actual_child_and_complete_output():
    payload, receipt = provider_receipt()
    _validate_provider_execution(receipt, payload=payload, adapter_pid=123)
    with pytest.raises(ValueError, match="actual adapter"):
        _validate_provider_execution(receipt, payload=payload, adapter_pid=999)


def test_provider_receipt_rejects_file_content_tampering():
    payload, receipt = provider_receipt()
    receipt["semantic_file_content"] += " "
    with pytest.raises(ValueError, match="differs from its receipt"):
        _validate_provider_execution(receipt, payload=payload, adapter_pid=123)


def test_provider_receipt_rejects_substituted_semantic_packet():
    payload, receipt = provider_receipt()
    payload["reader_sections"] = ["A shortened summary"]
    with pytest.raises(ValueError, match="differs from its semantic packet"):
        _validate_provider_execution(receipt, payload=payload, adapter_pid=123)


def test_provider_receipt_rejects_a_failed_event_stream():
    payload, receipt = provider_receipt()
    receipt["events"] = receipt["events"].replace('"turn.completed"', '"turn.failed"')
    receipt["events_sha256"] = sha256_bytes(receipt["events"].encode())
    with pytest.raises(ValueError, match="failed turn"):
        _validate_provider_execution(receipt, payload=payload, adapter_pid=123)
