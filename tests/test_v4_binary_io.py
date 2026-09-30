from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from xi_kari_runtime.canonical_json import read_bounded_regular_file


def test_signed_runtime_reader_preserves_crlf_and_ctrl_z_bytes(tmp_path):
    payload = b'first\r\nsecond\r\n\x1aafter\xff'
    path = tmp_path / 'actual-process.bin'
    path.write_bytes(payload)
    assert read_bounded_regular_file(path, limit=len(payload)) == payload


def test_byte_preservation_does_not_bypass_the_physical_file_limit(tmp_path):
    payload = b'a\r\n' * 20
    path = tmp_path / 'too-large.bin'
    path.write_bytes(payload)
    with pytest.raises(ValueError, match='size limit'):
        read_bounded_regular_file(path, limit=len(payload) - 1)
