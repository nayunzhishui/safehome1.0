import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from scripts.audit_api_boundaries import snapshots_semantically_equal


def _snapshot(location: str, rule: str = "select_star_in_http_adapter") -> dict:
    return {
        "schema": "safehome.api-boundary-audit.v1",
        "rules": ["select_star_in_http_adapter"],
        "counts": {"blocker": 0, "warning": 1},
        "quality_boundary": "test",
        "findings": [
            {
                "severity": "warning",
                "rule": rule,
                "location": location,
                "handler": "list_consent_records",
            }
        ],
    }


def test_api_boundary_snapshot_ignores_line_only_drift():
    assert snapshots_semantically_equal(
        _snapshot("backend/routes/consent.py:101"),
        _snapshot("backend/routes/consent.py:103"),
    )


def test_api_boundary_snapshot_still_detects_semantic_drift():
    assert not snapshots_semantically_equal(
        _snapshot("backend/routes/consent.py:101"),
        _snapshot("backend/routes/consent.py:103", rule="possible_unbounded_list"),
    )
