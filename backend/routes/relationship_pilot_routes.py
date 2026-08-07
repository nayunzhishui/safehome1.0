"""Thin HTTP adapter for the relationship-pilot domain modules."""

from __future__ import annotations

import json

from flask import Blueprint, Response, request

from routes.auth_utils import (
    AuthError,
    auth_error_response,
    elevate_actor_for_showcase_researcher_platform,
    require_capability,
    require_login,
)
from routes.utils import fail, ok
from services.participant_safeguard_service import ParticipantSafeguardError, assert_participant_capability
from services.relationship_enrollment_service import create_enrollment, get_enrollment, list_enrollments
from services.relationship_growth_service import create_longitudinal_entry, get_growth, researcher_dashboard
from services.relationship_pilot_common import RelationshipPilotError, ServiceResult
from services.relationship_report_service import confirm_report, create_report, get_report, save_hypothesis_feedback, send_report, update_report
from services.relationship_task_service import create_narrative, create_note, create_task, confirm_narrative, get_narrative
from services.runtime_metrics import record_operation_failure


bp = Blueprint("relationship_pilot", __name__, url_prefix="/api/relationship-pilot")


def _actor():
    try:
        actor = require_login(allow_legacy_admin=True)
        return elevate_actor_for_showcase_researcher_platform(actor), None
    except AuthError as exc:
        return None, auth_error_response(exc)


def _researcher(capability_id: str):
    try:
        return require_capability(capability_id, allow_legacy_admin=True), None
    except AuthError as exc:
        return None, auth_error_response(exc)


def _participant_research_guard(actor: dict):
    """Apply the ordinary participant safeguard even if showcase changes role."""
    participant_role = str(actor.get("original_role") or actor.get("role") or "")
    if participant_role != "student":
        return None
    try:
        assert_participant_capability(str(actor["id"]), "research")
    except ParticipantSafeguardError as exc:
        return fail(exc.code, exc.message, status=exc.status, details=exc.details or None)
    return None


def _respond(callable_, *args, **kwargs):
    try:
        result: ServiceResult = callable_(*args, **kwargs)
    except RelationshipPilotError as exc:
        record_operation_failure(callable_.__name__)
        return fail(exc.code, exc.message, status=exc.status, details=exc.details or None)
    except Exception:
        record_operation_failure(callable_.__name__)
        raise
    return ok(result.data, status=result.status)


@bp.post("/enrollments")
def create_enrollment_route():
    actor, error = _actor()
    if error:
        return error
    guard_error = _participant_research_guard(actor)
    if guard_error:
        return guard_error
    return _respond(create_enrollment, actor, request.get_json(silent=True) or {})


@bp.get("/enrollments")
def list_enrollments_route():
    actor, error = _actor()
    if error:
        return error
    return _respond(list_enrollments, actor)


@bp.get("/enrollments/<enrollment_id>")
def get_enrollment_route(enrollment_id: str):
    actor, error = _actor()
    if error:
        return error
    return _respond(get_enrollment, actor, enrollment_id)


@bp.post("/enrollments/<enrollment_id>/report")
def create_report_route(enrollment_id: str):
    actor, error = _researcher("research.feedback.write")
    if error:
        return error
    return _respond(create_report, actor, enrollment_id)


@bp.get("/reports/<report_id>")
def get_report_route(report_id: str):
    actor, error = _actor()
    if error:
        return error
    download = request.args.get("download") == "1"
    try:
        result = get_report(actor, report_id, download=download)
    except RelationshipPilotError as exc:
        return fail(exc.code, exc.message, status=exc.status, details=exc.details or None)
    if download:
        body = json.dumps(result.data, ensure_ascii=False, indent=2)
        return Response(body, mimetype="application/json", headers={"Content-Disposition": f'attachment; filename="relationship-report-{report_id}.json"'})
    return ok(result.data, status=result.status)


@bp.put("/reports/<report_id>/hypotheses/<int:hypothesis_index>")
def save_hypothesis_feedback_route(report_id: str, hypothesis_index: int):
    actor, error = _actor()
    if error:
        return error
    guard_error = _participant_research_guard(actor)
    if guard_error:
        return guard_error
    response = str((request.get_json(silent=True) or {}).get("response") or "").strip()
    return _respond(save_hypothesis_feedback, actor, report_id, hypothesis_index, response)


@bp.post("/reports/<report_id>/confirm")
def confirm_report_route(report_id: str):
    actor, error = _researcher("research.feedback.write")
    if error:
        return error
    return _respond(confirm_report, actor, report_id)


@bp.patch("/reports/<report_id>")
def update_report_route(report_id: str):
    actor, error = _researcher("research.feedback.write")
    if error:
        return error
    return _respond(update_report, actor, report_id, request.get_json(silent=True) or {})


@bp.post("/reports/<report_id>/send")
def send_report_route(report_id: str):
    actor, error = _researcher("research.feedback.write")
    if error:
        return error
    return _respond(send_report, actor, report_id)


@bp.post("/enrollments/<enrollment_id>/tasks")
def create_task_route(enrollment_id: str):
    actor, error = _actor()
    if error:
        return error
    guard_error = _participant_research_guard(actor)
    if guard_error:
        return guard_error
    return _respond(
        create_task,
        actor,
        enrollment_id,
        request.get_json(silent=True) or {},
        request.headers.get("Idempotency-Key", ""),
    )


@bp.post("/enrollments/<enrollment_id>/longitudinal")
def create_longitudinal_entry_route(enrollment_id: str):
    actor, error = _actor()
    if error:
        return error
    guard_error = _participant_research_guard(actor)
    if guard_error:
        return guard_error
    return _respond(
        create_longitudinal_entry,
        actor,
        enrollment_id,
        request.get_json(silent=True) or {},
        request.headers.get("Idempotency-Key", ""),
    )


@bp.get("/growth")
def relationship_growth_route():
    actor, error = _actor()
    if error:
        return error
    return _respond(get_growth, actor, str(request.args.get("user_id") or "").strip())


@bp.get("/researcher/dashboard")
def researcher_dashboard_route():
    actor, error = _researcher("research.dashboard.read")
    if error:
        return error
    return _respond(researcher_dashboard, actor)


@bp.post("/enrollments/<enrollment_id>/notes")
def create_note_route(enrollment_id: str):
    actor, error = _researcher("research.feedback.write")
    if error:
        return error
    note = str((request.get_json(silent=True) or {}).get("note") or "")
    return _respond(create_note, actor, enrollment_id, note)


@bp.post("/enrollments/<enrollment_id>/narrative")
def create_narrative_route(enrollment_id: str):
    actor, error = _researcher("research.narrative.manage")
    if error:
        return error
    return _respond(create_narrative, actor, enrollment_id, request.get_json(silent=True) or {})


@bp.post("/narratives/<narrative_id>/confirm")
def confirm_narrative_route(narrative_id: str):
    actor, error = _researcher("research.narrative.manage")
    if error:
        return error
    return _respond(confirm_narrative, actor, narrative_id)


@bp.get("/narratives/<narrative_id>")
def get_narrative_route(narrative_id: str):
    actor, error = _actor()
    if error:
        return error
    return _respond(get_narrative, actor, narrative_id)
