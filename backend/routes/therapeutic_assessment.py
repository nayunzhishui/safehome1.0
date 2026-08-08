"""HTTP routes for the Task36-F16 therapeutic-assessment collaboration."""

from flask import Blueprint, request

from routes.auth_utils import AuthError, auth_error_response, elevate_actor_for_showcase_researcher_platform, require_login
from routes.utils import fail, ok
from services.therapeutic_assessment_service import (
    TherapeuticAssessmentError,
    assign_case,
    create_action,
    create_case,
    create_feedback,
    get_case,
    list_cases,
    participant_transition,
    resend_feedback,
    revise_feedback,
    review_feedback,
    send_feedback,
    submit_feedback_response,
    set_readiness,
    update_action,
    update_scope,
    withdraw_feedback,
)
from services.therapeutic_assessment_level_service import public_status as service_level_status
from services.therapeutic_assessment_transition_service import transition_case
from services.therapeutic_assessment_evidence_service import (
    create_action_followup,
    create_evidence,
    list_evidence,
    review_hypothesis,
)
from services.therapeutic_assessment_question_service import update_question
from services.therapeutic_assessment_consent_service import (
    create_data_item,
    get_data_item,
    update_consent,
)
from services.therapeutic_assessment_draft_service import get_draft, save_draft
from services.therapeutic_assessment_safety_service import (
    configure_responsibility_chain,
    create_safety_signal,
    public_safety_status,
    resolve_safety_event,
    restore_runtime,
)
from services.therapeutic_assessment_workbench_service import (
    get_workbench,
    save_workbench_draft,
)
from services.therapeutic_assessment_competency_service import (
    create_authorization,
    effective_authorization,
    list_authorizations,
    revoke_authorization,
)
from services.therapeutic_assessment_quality_service import (
    analyze_quality_incident,
    claim_quality_review,
    complete_quality_review,
    create_quality_incident,
    list_quality_incidents,
    list_quality_queue,
    quality_runtime_status,
    resolve_quality_incident,
)
from services.therapeutic_assessment_contract_service import (
    contract_status,
    create_snapshot,
    validate_dimensions,
)
from services.therapeutic_assessment_queue_service import (
    claim_work_item,
    create_duty_shift,
    create_work_item,
    handoff_work_item,
    list_duty_shifts,
    list_work_items,
    queue_runtime_status,
    run_queue_monitor,
)
from services.therapeutic_assessment_lifecycle_service import (
    get_case_lifecycle,
    get_lifecycle_metrics,
)
from services.therapeutic_assessment_release_gate_service import (
    evaluate_release_gate,
    list_release_evidence,
    record_release_evidence,
    release_gate_status,
    verify_release_evidence,
)
from services.therapeutic_assessment_stop_recovery_service import (
    record_recovery_evidence,
    report_stop_incident,
    restore_after_incident,
    stop_recovery_status,
    verify_recovery_evidence,
)
from services.publication_gate_service import (
    PublicationGateError,
    list_candidates,
    recover_candidate,
    withdraw_candidate,
)
from services.therapeutic_assessment_launch_service import (
    latest_screening,
    public_scope as adult_launch_scope,
    record_screening,
)
from services.therapeutic_assessment_child_service import (
    get_safeguard as get_child_safeguard,
    initialize as initialize_child_safeguard,
    public_policy as child_safeguard_policy,
    update_decision as update_child_decision,
    update_gates as update_child_gates,
)
from services.therapeutic_assessment_multi_party_service import (
    get_safeguard as get_multi_party_safeguard,
    initialize as initialize_multi_party_safeguard,
    public_policy as multi_party_policy,
    update_consent as update_multi_party_consent,
    update_gates as update_multi_party_gates,
    update_safety_screen as update_multi_party_safety_screen,
)
from services.therapeutic_assessment_ai_assist_service import (
    create_candidates as create_ai_assist_candidates,
    decide_candidate as decide_ai_assist_candidate,
    list_candidates as list_ai_assist_candidates,
    public_policy as ai_assist_policy,
)
from services.therapeutic_assessment_method_service import (
    get_method as get_method_library_item,
    public_catalog as method_library_catalog,
)
from services.therapeutic_assessment_research_protocol_service import (
    get_protocol as get_research_protocol,
    preview_export as preview_research_export,
)
from services.therapeutic_assessment_pilot_evidence_service import (
    build_package as build_pilot_evidence_package,
)


bp = Blueprint("therapeutic_assessment", __name__, url_prefix="/api/therapeutic-assessment")


def _actor():
    try:
        return elevate_actor_for_showcase_researcher_platform(
            require_login(allow_legacy_admin=True)
        ), None
    except AuthError as exc:
        return None, auth_error_response(exc)


def _respond(callable_, *args, **kwargs):
    try:
        result = callable_(*args, **kwargs)
    except (TherapeuticAssessmentError, PublicationGateError) as exc:
        return fail(exc.code, exc.message, status=exc.status, details=exc.details)
    if isinstance(result, tuple):
        data, status = result
        return ok(data, status=status)
    return ok(result)


def _payload():
    return request.get_json(silent=True) or {}


def _key():
    return str(request.headers.get("Idempotency-Key") or "")


@bp.get("/launch-scope")
def get_launch_scope_route():
    actor, error = _actor()
    return error or _respond(adult_launch_scope)


@bp.get("/child-safeguards")
def get_child_safeguards_policy_route():
    actor, error = _actor()
    return error or _respond(child_safeguard_policy)


@bp.get("/multi-party-safeguards")
def get_multi_party_policy_route():
    actor, error = _actor()
    return error or _respond(multi_party_policy)


@bp.get("/ai-assist")
def get_ai_assist_policy_route():
    actor, error = _actor()
    return error or _respond(ai_assist_policy)


@bp.get("/method-library")
def get_method_library_route():
    actor, error = _actor()
    return error or _respond(method_library_catalog, actor)


@bp.get("/method-library/<item_id>")
def get_method_library_item_route(item_id: str):
    actor, error = _actor()
    return error or _respond(get_method_library_item, actor, item_id)


@bp.get("/research-protocol")
def get_research_protocol_route():
    actor, error = _actor()
    return error or _respond(get_research_protocol, actor)


@bp.post("/research-export/preview")
def post_research_export_preview_route():
    actor, error = _actor()
    return error or _respond(preview_research_export, actor, _payload())


@bp.get("/pilot-evidence/<stage_id>")
def get_pilot_evidence_route(stage_id: str):
    actor, error = _actor()
    return error or _respond(build_pilot_evidence_package, actor, stage_id)


@bp.post("/cases/<case_id>/ai-assist/candidates")
def post_ai_assist_candidates_route(case_id: str):
    actor, error = _actor()
    return error or _respond(
        create_ai_assist_candidates, actor, case_id, _payload(), _key()
    )


@bp.get("/cases/<case_id>/ai-assist/candidates")
def get_ai_assist_candidates_route(case_id: str):
    actor, error = _actor()
    return error or _respond(list_ai_assist_candidates, actor, case_id)


@bp.patch("/ai-assist/candidates/<candidate_id>")
def patch_ai_assist_candidate_route(candidate_id: str):
    actor, error = _actor()
    return error or _respond(
        decide_ai_assist_candidate, actor, candidate_id, _payload(), _key()
    )


@bp.post("/cases/<case_id>/multi-party-safeguards")
def post_multi_party_safeguard_route(case_id: str):
    actor, error = _actor()
    return error or _respond(
        initialize_multi_party_safeguard, actor, case_id, _payload(), _key()
    )


@bp.get("/cases/<case_id>/multi-party-safeguards")
def get_multi_party_safeguard_route(case_id: str):
    actor, error = _actor()
    return error or _respond(get_multi_party_safeguard, actor, case_id)


@bp.patch("/cases/<case_id>/multi-party-safeguards/consent")
def patch_multi_party_consent_route(case_id: str):
    actor, error = _actor()
    return error or _respond(
        update_multi_party_consent, actor, case_id, _payload(), _key()
    )


@bp.patch("/cases/<case_id>/multi-party-safeguards/safety-screen")
def patch_multi_party_safety_route(case_id: str):
    actor, error = _actor()
    return error or _respond(
        update_multi_party_safety_screen, actor, case_id, _payload(), _key()
    )


@bp.patch("/cases/<case_id>/multi-party-safeguards/gates")
def patch_multi_party_gates_route(case_id: str):
    actor, error = _actor()
    return error or _respond(
        update_multi_party_gates, actor, case_id, _payload(), _key()
    )


@bp.post("/cases/<case_id>/child-safeguards")
def post_child_safeguard_route(case_id: str):
    actor, error = _actor()
    return error or _respond(
        initialize_child_safeguard, actor, case_id, _payload(), _key()
    )


@bp.get("/cases/<case_id>/child-safeguards")
def get_child_safeguard_route(case_id: str):
    actor, error = _actor()
    return error or _respond(get_child_safeguard, actor, case_id)


@bp.patch("/cases/<case_id>/child-safeguards/decision")
def patch_child_safeguard_decision_route(case_id: str):
    actor, error = _actor()
    return error or _respond(
        update_child_decision, actor, case_id, _payload(), _key()
    )


@bp.patch("/cases/<case_id>/child-safeguards/gates")
def patch_child_safeguard_gates_route(case_id: str):
    actor, error = _actor()
    return error or _respond(
        update_child_gates, actor, case_id, _payload(), _key()
    )


@bp.post("/cases/<case_id>/launch-screenings")
def post_launch_screening_route(case_id: str):
    actor, error = _actor()
    return error or _respond(record_screening, actor, case_id, _payload(), _key())


@bp.get("/cases/<case_id>/launch-screenings/latest")
def get_latest_launch_screening_route(case_id: str):
    actor, error = _actor()
    return error or _respond(latest_screening, actor, case_id)


@bp.get("/service-levels")
def get_service_levels_route():
    actor, error = _actor()
    return error or ok(service_level_status())


@bp.get("/production-contract")
def get_production_contract_route():
    actor, error = _actor()
    return error or _respond(contract_status)


@bp.post("/production-contract/check")
def post_production_contract_check_route():
    actor, error = _actor()
    return error or _respond(validate_dimensions, _payload())


@bp.post("/production-contract/snapshots")
def post_production_contract_snapshot_route():
    actor, error = _actor()
    if error:
        return error
    if actor.get("role") != "admin":
        return fail("forbidden", "只有管理员可以冻结机器契约快照。", status=403)
    return _respond(create_snapshot, actor)


@bp.get("/work-queue")
def get_work_queue_route():
    actor, error = _actor()
    return error or _respond(list_work_items, actor, request.args.to_dict())


@bp.post("/cases/<case_id>/work-queue")
def post_work_queue_route(case_id: str):
    actor, error = _actor()
    return error or _respond(create_work_item, actor, case_id, _payload(), _key())


@bp.post("/work-queue/<item_id>/claim")
def post_work_queue_claim_route(item_id: str):
    actor, error = _actor()
    return error or _respond(claim_work_item, actor, item_id, _payload(), _key())


@bp.post("/work-queue/<item_id>/handoff")
def post_work_queue_handoff_route(item_id: str):
    actor, error = _actor()
    return error or _respond(handoff_work_item, actor, item_id, _payload(), _key())


@bp.get("/work-queue/runtime")
def get_work_queue_runtime_route():
    actor, error = _actor()
    return error or _respond(queue_runtime_status)


@bp.post("/work-queue/monitor")
def post_work_queue_monitor_route():
    actor, error = _actor()
    return error or _respond(run_queue_monitor, actor)


@bp.get("/duty-shifts")
def get_duty_shifts_route():
    actor, error = _actor()
    return error or _respond(list_duty_shifts, actor, request.args.to_dict())


@bp.post("/duty-shifts")
def post_duty_shift_route():
    actor, error = _actor()
    return error or _respond(create_duty_shift, actor, _payload(), _key())


@bp.get("/publication-candidates")
def get_publication_candidates_route():
    actor, error = _actor()
    return error or _respond(
        list_candidates,
        actor,
        status=str(request.args.get("status") or ""),
        channel=str(request.args.get("channel") or ""),
        limit=int(request.args.get("limit") or 50),
    )


@bp.post("/publication-candidates/<candidate_id>/recover")
def post_publication_candidate_recover_route(candidate_id: str):
    actor, error = _actor()
    return error or _respond(
        recover_candidate,
        actor,
        candidate_id,
        _payload(),
        _key(),
    )


@bp.post("/publication-candidates/<candidate_id>/withdraw")
def post_publication_candidate_withdraw_route(candidate_id: str):
    actor, error = _actor()
    return error or _respond(
        withdraw_candidate,
        actor,
        candidate_id,
        _payload(),
        _key(),
    )


@bp.get("/cases")
def get_cases_route():
    actor, error = _actor()
    return error or _respond(list_cases, actor)


@bp.post("/cases")
def post_case_route():
    actor, error = _actor()
    return error or _respond(create_case, actor, _payload(), _key())


@bp.get("/cases/<case_id>")
def get_case_route(case_id: str):
    actor, error = _actor()
    return error or _respond(get_case, actor, case_id)


@bp.patch("/cases/<case_id>/scope")
def patch_scope_route(case_id: str):
    actor, error = _actor()
    return error or _respond(update_scope, actor, case_id, _payload(), _key())


@bp.patch("/cases/<case_id>/question")
def patch_question_route(case_id: str):
    actor, error = _actor()
    return error or _respond(update_question, actor, case_id, _payload(), _key())


@bp.post("/cases/<case_id>/transitions")
def post_transition_route(case_id: str):
    actor, error = _actor()
    return error or _respond(transition_case, actor, case_id, _payload(), _key())


@bp.get("/cases/<case_id>/evidence")
def get_evidence_route(case_id: str):
    actor, error = _actor()
    return error or _respond(list_evidence, actor, case_id)


@bp.post("/cases/<case_id>/evidence")
def post_evidence_route(case_id: str):
    actor, error = _actor()
    return error or _respond(create_evidence, actor, case_id, _payload(), _key())


@bp.get("/cases/<case_id>/researcher-workbench")
def get_researcher_workbench_route(case_id: str):
    actor, error = _actor()
    return error or _respond(get_workbench, actor, case_id, request.args.to_dict())


@bp.get("/cases/<case_id>/lifecycle")
def get_case_lifecycle_route(case_id: str):
    actor, error = _actor()
    return error or _respond(get_case_lifecycle, actor, case_id)


@bp.get("/lifecycle/metrics")
def get_lifecycle_metrics_route():
    actor, error = _actor()
    return error or _respond(get_lifecycle_metrics, actor)


@bp.get("/production-gate")
def get_production_gate_route():
    actor, error = _actor()
    return error or _respond(release_gate_status, actor)


@bp.post("/production-gate/evaluate")
def post_production_gate_evaluate_route():
    actor, error = _actor()
    return error or _respond(evaluate_release_gate, actor, _key())


@bp.get("/production-gate/evidence")
def get_production_gate_evidence_route():
    actor, error = _actor()
    return error or _respond(list_release_evidence, actor)


@bp.post("/production-gate/evidence")
def post_production_gate_evidence_route():
    actor, error = _actor()
    return error or _respond(record_release_evidence, actor, _payload(), _key())


@bp.post("/production-gate/evidence/<evidence_id>/verify")
def post_production_gate_evidence_verify_route(evidence_id: str):
    actor, error = _actor()
    return error or _respond(
        verify_release_evidence,
        actor,
        evidence_id,
        _payload(),
        _key(),
    )


@bp.get("/stop-recovery/status")
def get_stop_recovery_status_route():
    actor, error = _actor()
    return error or _respond(stop_recovery_status, actor)


@bp.post("/stop-recovery/incidents")
def post_stop_recovery_incident_route():
    actor, error = _actor()
    return error or _respond(report_stop_incident, actor, _payload(), _key())


@bp.post("/stop-recovery/incidents/<incident_id>/evidence")
def post_stop_recovery_evidence_route(incident_id: str):
    actor, error = _actor()
    return error or _respond(
        record_recovery_evidence,
        actor,
        incident_id,
        _payload(),
        _key(),
    )


@bp.post("/stop-recovery/evidence/<evidence_id>/verify")
def post_stop_recovery_evidence_verify_route(evidence_id: str):
    actor, error = _actor()
    return error or _respond(
        verify_recovery_evidence,
        actor,
        evidence_id,
        _payload(),
        _key(),
    )


@bp.post("/stop-recovery/incidents/<incident_id>/restore")
def post_stop_recovery_restore_route(incident_id: str):
    actor, error = _actor()
    return error or _respond(
        restore_after_incident,
        actor,
        incident_id,
        _payload(),
        _key(),
    )


@bp.put("/cases/<case_id>/researcher-workbench/draft")
def put_researcher_workbench_draft_route(case_id: str):
    actor, error = _actor()
    return error or _respond(save_workbench_draft, actor, case_id, _payload(), _key())


@bp.post("/evidence/<evidence_id>/review")
def post_evidence_review_route(evidence_id: str):
    actor, error = _actor()
    return error or _respond(review_hypothesis, actor, evidence_id, _payload(), _key())


@bp.post("/cases/<case_id>/data-items")
def post_data_item_route(case_id: str):
    actor, error = _actor()
    return error or _respond(create_data_item, actor, case_id, _payload(), _key())


@bp.get("/data-items/<item_id>")
def get_data_item_route(item_id: str):
    actor, error = _actor()
    return error or _respond(get_data_item, actor, item_id)


@bp.patch("/data-items/<item_id>/consent")
def patch_data_consent_route(item_id: str):
    actor, error = _actor()
    return error or _respond(update_consent, actor, item_id, _payload(), _key())


@bp.get("/cases/<case_id>/participant-drafts/<step_id>")
def get_participant_draft_route(case_id: str, step_id: str):
    actor, error = _actor()
    return error or _respond(get_draft, actor, case_id, step_id)


@bp.put("/cases/<case_id>/participant-drafts/<step_id>")
def put_participant_draft_route(case_id: str, step_id: str):
    actor, error = _actor()
    return error or _respond(save_draft, actor, case_id, step_id, _payload(), _key())


@bp.get("/safety/status")
def get_safety_status_route():
    actor, error = _actor()
    return error or _respond(public_safety_status, actor)


@bp.put("/cases/<case_id>/responsibility-chain")
def put_responsibility_chain_route(case_id: str):
    actor, error = _actor()
    return error or _respond(configure_responsibility_chain, actor, case_id, _payload(), _key())


@bp.post("/cases/<case_id>/safety-signals")
def post_safety_signal_route(case_id: str):
    actor, error = _actor()
    return error or _respond(create_safety_signal, actor, case_id, _payload(), _key())


@bp.post("/safety-events/<event_id>/resolve")
def post_safety_resolution_route(event_id: str):
    actor, error = _actor()
    return error or _respond(resolve_safety_event, actor, event_id, _payload(), _key())


@bp.post("/safety/runtime/restore")
def post_safety_runtime_restore_route():
    actor, error = _actor()
    return error or _respond(restore_runtime, actor, _payload())


@bp.post("/cases/<case_id>/disagree")
def post_disagree_route(case_id: str):
    actor, error = _actor()
    return error or _respond(participant_transition, actor, case_id, _payload(), _key(), "disagree")


@bp.post("/cases/<case_id>/withdraw")
def post_withdraw_route(case_id: str):
    actor, error = _actor()
    return error or _respond(participant_transition, actor, case_id, _payload(), _key(), "withdraw")


@bp.post("/cases/<case_id>/assign")
def post_assign_route(case_id: str):
    actor, error = _actor()
    return error or _respond(assign_case, actor, case_id, _payload(), _key())


@bp.post("/cases/<case_id>/readiness")
def post_readiness_route(case_id: str):
    actor, error = _actor()
    return error or _respond(set_readiness, actor, case_id, _payload(), _key())


@bp.post("/cases/<case_id>/feedback-versions")
def post_feedback_route(case_id: str):
    actor, error = _actor()
    return error or _respond(create_feedback, actor, case_id, _payload(), _key())


@bp.post("/feedback-versions/<feedback_id>/review")
def post_review_route(feedback_id: str):
    actor, error = _actor()
    return error or _respond(review_feedback, actor, feedback_id, _payload(), _key())


@bp.post("/feedback-versions/<feedback_id>/send")
def post_send_route(feedback_id: str):
    actor, error = _actor()
    return error or _respond(send_feedback, actor, feedback_id, _key())


@bp.post("/feedback-versions/<feedback_id>/responses")
def post_feedback_response_route(feedback_id: str):
    actor, error = _actor()
    return error or _respond(submit_feedback_response, actor, feedback_id, _payload(), _key())


@bp.post("/feedback-versions/<feedback_id>/revise")
def post_feedback_revise_route(feedback_id: str):
    actor, error = _actor()
    return error or _respond(revise_feedback, actor, feedback_id, _payload(), _key())


@bp.post("/feedback-versions/<feedback_id>/withdraw")
def post_feedback_withdraw_route(feedback_id: str):
    actor, error = _actor()
    return error or _respond(withdraw_feedback, actor, feedback_id, _payload(), _key())


@bp.post("/feedback-versions/<feedback_id>/resend")
def post_feedback_resend_route(feedback_id: str):
    actor, error = _actor()
    return error or _respond(resend_feedback, actor, feedback_id, _key())


@bp.post("/cases/<case_id>/actions")
def post_action_route(case_id: str):
    actor, error = _actor()
    return error or _respond(create_action, actor, case_id, _payload(), _key())


@bp.patch("/actions/<action_id>")
def patch_action_route(action_id: str):
    actor, error = _actor()
    return error or _respond(update_action, actor, action_id, _payload(), _key())


@bp.post("/actions/<action_id>/followups")
def post_action_followup_route(action_id: str):
    actor, error = _actor()
    return error or _respond(create_action_followup, actor, action_id, _payload(), _key())


@bp.get("/competency/authorizations")
def get_competency_authorizations_route():
    actor, error = _actor()
    return error or _respond(list_authorizations, actor, request.args.to_dict())


@bp.post("/competency/authorizations")
def post_competency_authorization_route():
    actor, error = _actor()
    return error or _respond(create_authorization, actor, _payload(), _key())


@bp.patch("/competency/authorizations/<authorization_id>/revoke")
def patch_competency_authorization_revoke_route(authorization_id: str):
    actor, error = _actor()
    return error or _respond(revoke_authorization, actor, authorization_id, _payload(), _key())


@bp.get("/competency/effective")
def get_competency_effective_route():
    actor, error = _actor()
    return error or _respond(effective_authorization, actor, request.args.to_dict())


@bp.get("/quality/runtime")
def get_quality_runtime_route():
    actor, error = _actor()
    return error or _respond(quality_runtime_status)


@bp.get("/quality/reviews")
def get_quality_reviews_route():
    actor, error = _actor()
    return error or _respond(list_quality_queue, actor, request.args.to_dict())


@bp.post("/quality/reviews/<review_id>/claim")
def post_quality_review_claim_route(review_id: str):
    actor, error = _actor()
    return error or _respond(claim_quality_review, actor, review_id, _payload(), _key())


@bp.post("/quality/reviews/<review_id>/complete")
def post_quality_review_complete_route(review_id: str):
    actor, error = _actor()
    return error or _respond(complete_quality_review, actor, review_id, _payload(), _key())


@bp.post("/cases/<case_id>/quality-incidents")
def post_quality_incident_route(case_id: str):
    actor, error = _actor()
    return error or _respond(create_quality_incident, actor, case_id, _payload(), _key())


@bp.get("/quality/incidents")
def get_quality_incidents_route():
    actor, error = _actor()
    return error or _respond(list_quality_incidents, actor, request.args.to_dict())


@bp.post("/quality/incidents/<incident_id>/impact-analysis")
def post_quality_incident_analysis_route(incident_id: str):
    actor, error = _actor()
    return error or _respond(analyze_quality_incident, actor, incident_id, _payload(), _key())


@bp.post("/quality/incidents/<incident_id>/resolve")
def post_quality_incident_resolution_route(incident_id: str):
    actor, error = _actor()
    return error or _respond(resolve_quality_incident, actor, incident_id, _payload(), _key())
