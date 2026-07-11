import importlib
import math
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _service():
    return importlib.import_module("services.assessment_profile_service")


def test_model_admission_blocks_internal_models_from_automatic_matching():
    service = _service()
    internal = {"admission_status": "internal_only", "worksheet_link_status": "connected"}
    internal["artifact_hash"] = service.compute_model_artifact_hash(internal)
    pilot = {"admission_status": "pilot_approved", "worksheet_link_status": "connected"}
    pilot["artifact_hash"] = service.compute_model_artifact_hash(pilot)
    production = {"admission_status": "production_approved", "worksheet_link_status": "connected"}
    production["artifact_hash"] = service.compute_model_artifact_hash(production)

    assert service.model_is_connectable(internal) is False
    assert service.model_is_connectable(pilot) is True
    assert service.model_is_connectable(production) is True
    assert service.model_is_connectable({"worksheet_link_status": "connected"}) is False
    pilot["standard_scale_name"] = "tampered"
    assert service.model_is_connectable(pilot) is False


def test_gmm_assignment_uses_weights_and_diagonal_covariances():
    service = _service()
    model = {
        "selected_method": "gaussian_mixture",
        "assignment_version": "gmm_diag_posterior_v1",
        "mixture_weights": [0.01, 0.99],
        "diag_covariances": [{"x": 100.0}, {"x": 1.0}],
        "clusters": [
            {"cluster_id": 0, "center_z": {"x": 0.0}},
            {"cluster_id": 1, "center_z": {"x": 2.0}},
        ],
    }

    assignment = service.assign_profile_cluster(model, ["x"], {"x": 0.9})

    assert assignment["cluster"]["cluster_id"] == 1
    assert assignment["posterior"] > 0.9
    assert 0 <= assignment["normalized_entropy"] <= 1
    assert math.isclose(assignment["mahalanobis_distance"], 1.1, rel_tol=1e-6)


def test_pending_interpretation_approval_blocks_profile_name_and_tasks():
    service = _service()
    guard = service.interpretation_guard(
        {
            "interpretation_approval_status": "pending_researcher_review",
            "assignment_thresholds": {"min_posterior": 0.6, "max_entropy": 0.7, "max_mahalanobis": 3.0},
        },
        {"posterior": 0.95, "normalized_entropy": 0.1, "mahalanobis_distance": 0.5},
    )

    assert guard["status"] == "pending_approval"
    assert guard["can_use_interpretation"] is False
