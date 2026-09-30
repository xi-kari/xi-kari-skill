from copy import deepcopy
from pathlib import Path
import hashlib
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


def inputs():
    content = 'Actual bounded fixture content.'
    host = {'run_id': 'fixture', 'mode': 'open-world', 'sources': [{
        'source_id': 'HOST-1', 'url': 'https://example.invalid/fixture',
        'content': content, 'content_sha256': hashlib.sha256(content.encode()).hexdigest(),
    }]}
    author = {'mode': 'open-world', 'sources': [{
        'source_id': 'MODEL-1', 'url': 'https://example.invalid/fixture', 'content': content,
        'source_revision': 'study-v1', 'canonical_locator': 'MODEL-1:P1',
        'lineage_refs': ['study-cohort-v1'], 'independence_key': 'study-cohort-v1',
        'research_design': 'registered comparison', 'read_extent': 'full provided content',
        'provenance_refs': ['original experiment report'], 'availability_status': 'available',
        'visibility': 'public', 'protected_review': None,
    }]}
    return host, author


def test_material_projection_preserves_responsibilities_and_runtime_byte_identity():
    from xi_kari_runtime.v4_retrieval import bind_material_responsibilities, host_retrieval_view
    host, author = inputs()
    checked = bind_material_responsibilities(host, author)
    source = checked['sources'][0]
    assert source['content_sha256'] == host['sources'][0]['content_sha256']
    assert source['canonical_locator'] == 'https://example.invalid/fixture:P1'
    assert source['source_revision'] == 'study-v1'
    assert source['research_design'] == author['sources'][0]['research_design']
    assert host_retrieval_view(checked) == host
    assert 'research_design' not in host['sources'][0]


def test_projected_material_cannot_borrow_another_document_locator():
    from xi_kari_runtime.v4_retrieval import bind_material_responsibilities
    host, author = inputs()
    author['sources'][0]['canonical_locator'] = 'https://example.invalid/other:P1'
    with pytest.raises(ValueError, match='locator'):
        bind_material_responsibilities(host, author)


def test_material_projection_rejects_invented_content_or_changed_host_hash():
    from xi_kari_runtime.v4_retrieval import bind_material_responsibilities
    host, author = inputs()
    author['sources'][0]['content'] = 'A different asserted material.'
    with pytest.raises(ValueError, match='content'):
        bind_material_responsibilities(host, author)
    host, author = inputs()
    host['sources'][0]['content_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='hash'):
        bind_material_responsibilities(host, author)


def test_projection_requires_actual_responsibility_metadata_for_each_source():
    from xi_kari_runtime.v4_retrieval import bind_material_responsibilities
    host, author = inputs()
    del author['sources'][0]['research_design']
    with pytest.raises(ValueError, match='responsibilities'):
        bind_material_responsibilities(host, author)


def test_runtime_run_identity_can_be_added_without_changing_the_original_transport():
    from xi_kari_runtime.v4_retrieval import bind_material_responsibilities, host_retrieval_view
    host, author = inputs()
    del host['run_id']
    checked = bind_material_responsibilities(host, author, run_id='runtime-owned')
    assert checked['run_id'] == 'runtime-owned'
    assert host_retrieval_view(checked) == host


@pytest.mark.parametrize('verdict', ['admitted', 'rejected'])
def test_source_admission_is_derived_from_its_actual_assessment(verdict):
    from xi_kari_runtime.v4_retrieval import bind_material_responsibilities, host_retrieval_view
    host, author = inputs()
    host['assessments'] = [{'source_id': 'HOST-1', 'verdict': verdict}]
    checked = bind_material_responsibilities(host, author)
    assert checked['sources'][0]['assessment_verdict'] == verdict
    assert host_retrieval_view(checked) == host
