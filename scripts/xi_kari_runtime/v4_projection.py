"""Semantic views of version-four records for the typed visibility consumer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .domains import domain_reader_records


def projection_roots(payload: Mapping[str, Any]) -> dict[str, Any]:
    roots: dict[str, Any] = {}
    trace = payload.get('domain_read_trace')
    if isinstance(trace, Mapping):
        roots['domain_read_trace'] = {'records': domain_reader_records(trace)}
    if 'domain_usage' in payload:
        roots['domain_usage'] = payload['domain_usage']
    return roots
