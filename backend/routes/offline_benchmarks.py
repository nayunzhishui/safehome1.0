"""Internal governed offline benchmark endpoints."""

from flask import Blueprint, request

from routes.auth_utils import AuthError, auth_error_response, require_role
from routes.utils import fail, ok
from services.offline_benchmark_service import (
    OfflineBenchmarkError,
    agreement_summary,
    disable_runtime,
    get_config,
    list_blind_cases,
    list_dataset_cards,
    list_runs,
    review_run,
    run_affect_benchmark,
    run_network_benchmark,
    save_annotation,
    sync_registry,
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
    except OfflineBenchmarkError as exc:
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
