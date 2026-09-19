"""Fixed-file transport for complete semantic authoring in a private workspace."""

from __future__ import annotations

from pathlib import Path
import re
import stat
from typing import Any

from .canonical_json import read_bounded_regular_file, read_json_text


SEMANTIC_OUTPUT_FILENAME = "semantic-output.json"
COMPLETION_NOTICE = b"SEMANTIC_OUTPUT_READY"
OUTPUT_TRANSPORT = "xi-kari.v3.semantic-file-output/v1"
MAX_PROVIDER_EVENT_BYTES = 16 * 1024 * 1024
MAX_PROVIDER_EVENT_LINES = 10000
_RECONNECT_NOTICE = re.compile(r"Reconnecting\.\.\. [1-5]/5 \(stream disconnected before completion: [^\r\n]+\)")
_SKILL_BUDGET_NOTICE = (
    "Skill descriptions were shortened to fit the skills context budget. "
    "Codex can still see every skill, but some descriptions are shorter. "
    "Disable unused skills or plugins to leave more room for the rest."
)


def is_provider_failure_event(event: dict[str, Any]) -> bool:
    """Keep known CLI notices in a stream that must still end in completion."""

    if event.get("type") == "turn.failed":
        return True
    if event.get("type") == "error":
        message = event.get("message")
        return not (set(event) == {"type", "message"} and isinstance(message, str)
                    and _RECONNECT_NOTICE.fullmatch(message))
    item = event.get("item")
    if event.get("type") in {"item.started", "item.updated", "item.completed"} and isinstance(item, dict) and item.get("type") == "error":
        return item.get("message") != _SKILL_BUDGET_NOTICE
    return False


def read_semantic_output(workspace: Path, *, notice: bytes, limit: int) -> bytes:
    """Read strict JSON only from the fixed output, never a model-supplied path."""

    if not isinstance(notice, bytes) or notice.strip() != COMPLETION_NOTICE:
        raise ValueError("semantic output completion notice is invalid")
    workspace = Path(workspace).absolute()
    output = workspace / SEMANTIC_OUTPUT_FILENAME
    for path in (output, workspace, *workspace.parents):
        try:
            metadata = path.lstat()
        except OSError as error:
            raise ValueError(f"semantic output is unavailable: {path}") from error
        if stat.S_ISLNK(metadata.st_mode) or getattr(metadata, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            raise ValueError(f"semantic output refuses symlink or reparse path: {path}")
    raw = read_bounded_regular_file(output, limit=limit)
    try:
        payload = read_json_text(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as error:
        raise ValueError("semantic output file is not strict UTF-8 JSON") from error
    if not isinstance(payload, dict):
        raise ValueError("semantic output file must contain one JSON object")
    return raw


def parse_provider_events(raw: bytes) -> tuple[str, list[dict[str, Any]]]:
    """Check the captured provider event stream without accepting model receipts."""

    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_PROVIDER_EVENT_BYTES:
        raise ValueError("provider JSONL event stream size is invalid")
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise ValueError("provider JSONL event stream is not UTF-8") from error
    if not lines or len(lines) > MAX_PROVIDER_EVENT_LINES or any(not line for line in lines):
        raise ValueError("provider JSONL event stream line count is invalid")
    events = []
    for number, line in enumerate(lines, start=1):
        try:
            event = read_json_text(line)
        except ValueError as error:
            raise ValueError(f"provider JSONL event is invalid at line {number}") from error
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            raise ValueError(f"provider JSONL event is not an object at line {number}")
        events.append(event)
    if any(is_provider_failure_event(event) for event in events):
        raise ValueError("provider event stream contains a failed turn")
    if events[0]["type"] != "thread.started" or len(events) < 3 or events[1]["type"] != "turn.started" or events[-1]["type"] != "turn.completed":
        raise ValueError("provider event stream does not contain a complete thread and turn")
    thread_id = events[0].get("thread_id")
    if not isinstance(thread_id, str) or not thread_id:
        raise ValueError("provider event stream has no thread identity")
    return thread_id, events
