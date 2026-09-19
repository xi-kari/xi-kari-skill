import pytest

from scripts.xi_kari_runtime import contracts


def test_unresolved_explanations_do_not_erase_an_independent_local_rank() -> None:
    verdict = {
        "non_decidability": {"remaining_partial_order": ["EXPLANATION-MOTIVE-A", "EXPLANATION-MOTIVE-B"]},
        "explanation_ranking": [
            {"explanation_id": "EXPLANATION-MOTIVE-A", "rank": None},
            {"explanation_id": "EXPLANATION-MOTIVE-B", "rank": None},
            {"explanation_id": "EXPLANATION-PROCEDURE", "rank": 1},
        ],
    }
    contracts.validate_partial_explanation_order(verdict)


def test_unresolved_explanation_cannot_receive_a_rank() -> None:
    verdict = {
        "non_decidability": {"remaining_partial_order": ["EXPLANATION-A", "EXPLANATION-B"]},
        "explanation_ranking": [
            {"explanation_id": "EXPLANATION-A", "rank": 1},
            {"explanation_id": "EXPLANATION-B", "rank": None},
        ],
    }
    with pytest.raises(ValueError, match="unresolved"):
        contracts.validate_partial_explanation_order(verdict)
