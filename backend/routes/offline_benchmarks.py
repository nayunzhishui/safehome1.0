"""Internal governed offline benchmark endpoints."""

from flask import Blueprint, request

from routes.auth_utils import AuthError, auth_error_response, require_role
from routes.utils import fail, ok
from services.offline_benchmark_service import (
    OfflineBenchmarkError,
    analyze_network_payload,
    adjudicate_case,
    agreement_summary,
    disable_runtime,
    get_affect_model_candidates,
    get_annotation_governance,
    get_config,
    get_network_analysis_policy,
    list_adjudication_queue,
    list_blind_cases,
    list_dataset_cards,
    list_runs,
    review_run,
    run_affect_benchmark,
    run_network_benchmark,
    save_annotation,
    split_report,
    sync_registry,
)
from services.group_network_analysis_service import NetworkAnalysisError
from services.affect_shadow_service import (
    AffectShadowError,
    list_model_versions,
    list_review_queue as list_shadow_review_queue,
    list_shadow_runs,
    register_model_version,
    run_shadow,
)
from services.affect_monitor_service import (
    apply_runtime_action,
    get_monitoring_status,
    run_monitor_drill,
)
from services.affect_release_gate_service import (
    build_release_gate,
    record_external_evidence,
    release_gate_status,
)


bp = Blueprint("offline_benchmarks", __name__, url_prefix="/api/research/benchmarks")


def _actor(*roles: str):
    try:
        return require_role(*roles, allow_legacy_admin=True), None
    except AuthError as exc:
        return None, auth_error_response(exc)


def _response(callback):
    try:
        return ok(callback())
    except (OfflineBenchmarkError, NetworkAnalysisError, AffectShadowError) as exc:
        return fail(exc.code, str(exc), status=exc.status, details=exc.details or None)


@bp.get("/config")
def config():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(get_config)


@bp.post("/dataset-cards/sync")
def dataset_cards_sync():
    actor, error = _actor("admin")
    if error:
        return error
    return _response(lambda: sync_registry(actor))


@bp.get("/dataset-cards")
def dataset_cards():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: {"items": list_dataset_cards()})


@bp.get("/cases")
def cases():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: list_blind_cases(actor, request.args.get("offset", 0), request.args.get("limit", 20)))


@bp.get("/annotation-governance")
def annotation_governance():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(get_annotation_governance)


@bp.get("/model-candidates")
def model_candidates():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(get_affect_model_candidates)


@bp.get("/network-policy")
def network_policy():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(get_network_analysis_policy)


@bp.post("/network/analyze")
def network_analyze():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: analyze_network_payload(actor, payload))


@bp.post("/model-versions")
def model_version_create():
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(
        lambda: register_model_version(actor, str(payload.get("code_commit") or ""))
    )


@bp.get("/model-versions")
def model_versions():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(list_model_versions)


@bp.post("/shadow-runs")
def shadow_run_create():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(
        lambda: run_shadow(actor, str(payload.get("model_version_id") or ""))
    )


@bp.post("/shadow-runs/<run_id>/replay")
def shadow_run_replay(run_id: str):
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(
        lambda: run_shadow(
            actor,
            str(payload.get("model_version_id") or ""),
            parent_run_id=run_id,
        )
    )


@bp.get("/shadow-runs")
def shadow_runs():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: list_shadow_runs(actor))


@bp.get("/shadow-review-queue")
def shadow_review_queue():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: list_shadow_review_queue(actor))


@bp.get("/monitoring")
def monitoring_status():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(get_monitoring_status)


@bp.post("/monitoring/drills")
def monitoring_drill_create():
    actor, error = _actor("supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(
        lambda: run_monitor_drill(
            actor,
            str(payload.get("scenario") or ""),
            str(payload.get("model_version_id") or "") or None,
        )
    )


@bp.post("/runtime-actions/<action>")
def runtime_action_create(action: str):
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: apply_runtime_action(actor, action, payload))


@bp.get("/release-gate")
def release_gate_get():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(release_gate_status)


@bp.post("/release-gate/packages")
def release_gate_package_create():
    actor, error = _actor("supervisor", "admin")
    if error:
        return error
    return _response(lambda: build_release_gate(actor))


@bp.post("/release-gate/evidence")
def release_gate_evidence_create():
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: record_external_evidence(actor, payload))


@bp.post("/cases/<case_id>/annotations")
def annotation_create(case_id: str):
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: save_annotation(actor, case_id, payload))


@bp.get("/agreement")
def agreement():
    actor, error = _actor("supervisor", "admin")
    if error:
        return error
    return _response(agreement_summary)


@bp.get("/adjudication-queue")
def adjudication_queue():
    actor, error = _actor("supervisor", "admin")
    if error:
        return error
    return _response(list_adjudication_queue)


@bp.post("/cases/<case_id>/adjudications")
def adjudication_create(case_id: str):
    actor, error = _actor("supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: adjudicate_case(actor, case_id, payload))


@bp.get("/split-report")
def annotation_split_report():
    actor, error = _actor("supervisor", "admin")
    if error:
        return error
    return _response(split_report)


@bp.post("/runs/affect")
def affect_run():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: run_affect_benchmark(actor))


@bp.post("/runs/network")
def network_run():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: run_network_benchmark(actor))


@bp.get("/runs")
def runs():
    actor, error = _actor("researcher", "supervisor", "admin")
    if error:
        return error
    return _response(lambda: {"items": list_runs(actor)})


@bp.post("/runs/<run_id>/reviews")
def run_review(run_id: str):
    actor, error = _actor("supervisor", "admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: review_run(actor, run_id, payload))


@bp.post("/disable")
def disable():
    actor, error = _actor("admin")
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    return _response(lambda: disable_runtime(actor, payload))
