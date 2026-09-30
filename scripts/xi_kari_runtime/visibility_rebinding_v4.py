"""Preserve author disclosure decisions through code-owned evidence projection."""

from collections.abc import Mapping, Sequence
from copy import deepcopy
import re
from typing import Any

from .semantic_projection import semantic_atom_paths


SUPPORT_PATH = re.compile(r'^evidence\.claims\[(\d+)\]\.support\[(\d+)\]\.(.+)$')


def rebase_evidence_visibility_v4(
    packet: dict[str, Any], *, author_claims: Sequence[Mapping[str, Any]], purpose: str,
) -> None:
    original = packet.get('visibility_ledger', {}).get('entries')
    if not isinstance(original, list):
        raise ValueError('author evidence projection requires actual disclosure decisions')
    target_paths = set(semantic_atom_paths(packet))
    records = packet['evidence']['evidence']
    by_identity = {row['evidence_id']: index for index, row in enumerate(records)}
    mapping = {}
    for claim_index, claim in enumerate(author_claims):
        for support_index, _ in enumerate(claim.get('support', [])):
            identifier = f"{claim['claim_id']}-e{support_index + 1}"
            if identifier not in by_identity:
                raise ValueError('author support has no actual normalized evidence identity')
            mapping[(claim_index, support_index)] = by_identity[identifier]
    def project(path: str) -> str:
        match = SUPPORT_PATH.fullmatch(path)
        if not match:
            return path
        key = (int(match[1]), int(match[2]))
        if key not in mapping:
            raise ValueError('author support disclosure has no actual evidence binding')
        return f'evidence.evidence[{mapping[key]}].{match[3]}'
    entries = {}
    for entry in original:
        if not isinstance(entry, Mapping) or not isinstance(entry.get('canonical_path'), str):
            raise ValueError('author disclosure entry is malformed')
        if entry.get('purpose') != purpose:
            raise ValueError('author disclosure purpose differs from the frozen contract')
        path = project(entry['canonical_path'])
        if path not in target_paths:
            if entry.get('disclosure') == 'withhold':
                raise ValueError('protected author disclosure cannot be discarded during normalization')
            continue
        if path in entries:
            raise ValueError('normalized disclosure decisions have duplicate semantic paths')
        entries[path] = {**deepcopy(dict(entry)), 'canonical_path': path}
    packet['visibility_ledger'] = {'entries': [entries[path] for path in sorted(entries)]}
    for section in packet.get('reader_sections', []):
        for binding in section.get('source_bindings', []):
            field = 'canonical_path' if 'canonical_path' in binding else 'source_path'
            if isinstance(binding.get(field), str):
                binding[field] = project(binding[field])
    # Missing runtime semantic atoms need explicit decisions from the final author.


__all__ = ('rebase_evidence_visibility_v4',)
