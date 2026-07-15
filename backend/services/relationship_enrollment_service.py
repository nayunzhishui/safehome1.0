"""Enrollment module for relationship-pilot participation and dossier access."""

from __future__ import annotations

from database import get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from services.assessment_profile_service import ProfilePositionUnavailable, build_assessment_profile_position
from services.relationship_pilot_common import (
    BOUNDARY,
    RELATIONSHIP_WORKSHEET_IDS,
    RESEARCH_ROLES,
    RelationshipPilotError,
    ServiceResult,
    enrollment_by_id,
    expand_enrollment,
    expand_task,
    own_or_researcher,
    worksheet,
)
from services.showcase_access_service import allow_showcase_program_participation


def create_enrollment(actor: dict, payload: dict) -> ServiceResult:
    if actor.get("role") not in {"student", "admin"} and not allow_showcase_program_participation():
        raise RelationshipPilotError("forbidden", "关系探索试点当前仅向已授权的学生试点账号开放。", 403)
    if payload.get("research_consent") is not True:
        raise RelationshipPilotError("consent_required", "参加第二阶段前需要明确同意研究用途说明。")
    user_id = str(actor["id"])
    requested_result_id = str(payload.get("assessment_result_id") or "").strip()
    with get_connection() as conn:
        where = ["user_id = ?", f"worksheet_id IN ({','.join('?' for _ in RELATIONSHIP_WORKSHEET_IDS)})"]
        params = [user_id, *sorted(RELATIONSHIP_WORKSHEET_IDS)]
        if requested_result_id:
            where.append("id = ?")
            params.append(requested_result_id)
        row = conn.execute(
            f"SELECT * FROM assessment_results WHERE {' AND '.join(where)} ORDER BY created_at DESC LIMIT 1",
            params,
        ).fetchone()
        if row is None:
            raise RelationshipPilotError("assessment_required", "需先完成一份亲密关系试点测一测。", 409)
        result = row_to_dict(row)
        existing = conn.execute(
            "SELECT * FROM relationship_pilot_enrollments WHERE assessment_result_id = ?",
            (result["id"],),
        ).fetchone()
        if existing:
            existing_item = row_to_dict(existing)
            if str(existing_item["user_id"]) != user_id:
                raise RelationshipPilotError("association_conflict", "该测评结果已关联其他报名记录。", 409)
            return ServiceResult(expand_enrollment(existing_item))

        worksheet_item = worksheet(result["worksheet_id"])
        if not worksheet_item:
            raise RelationshipPilotError("worksheet_unavailable", "测评内容暂不可用。", 409)
        result["answers"] = json_loads(result.get("answers_json"), [])
        scores = json_loads(result.get("scores_json"), {})
        try:
            profile = build_assessment_profile_position(result, worksheet_item)
        except ProfilePositionUnavailable as exc:
            raise RelationshipPilotError("profile_unavailable", exc.reason, 409) from exc
        selected = next(
            (cluster for cluster in profile.get("clusters", []) if cluster.get("cluster_id") == profile.get("position", {}).get("cluster_id")),
            {},
        )
        dimensions = scores.get("dimensions", [])
        radar_features = [
            {"code": item.get("code"), "z_score": selected.get("dimension_z", {}).get(item.get("code"))}
            for item in profile.get("radar_support", {}).get("dimensions", [])
            if isinstance(selected.get("dimension_z", {}).get(item.get("code")), (int, float))
        ]
        review_status = "pending_review" if worksheet_item.get("review_status") != "approved" or not profile.get("position", {}).get("can_use_interpretation") else "ready"
        enrollment_id = new_id("rel_enroll")
        timestamp = now_iso()
        profile_snapshot = {
            "model_id": profile.get("model_id"),
            "cluster_id": profile.get("position", {}).get("cluster_id"),
            "profile_name": profile.get("position", {}).get("display_name") or profile.get("position", {}).get("profile_name"),
            "profile_description": profile.get("explanation"),
            "confidence": profile.get("position", {}).get("confidence"),
            "interpretation_status": profile.get("position", {}).get("interpretation_status"),
            "suggested_assessment_questions": profile.get("suggested_assessment_questions", []),
            "recommended_project_tasks": profile.get("recommended_project_tasks", []),
            "boundary_notice": profile.get("boundary_notice") or BOUNDARY,
        }
        try:
            conn.execute(
                """
                INSERT INTO relationship_pilot_enrollments (
                    id, user_id, assessment_result_id, worksheet_id, profile_model_id, profile_cluster_id,
                    dimensions_json, radar_features_json, profile_json, consent_scope, status, review_status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'enrolled', ?, ?, ?)
                """,
                (
                    enrollment_id, user_id, result["id"], result["worksheet_id"], profile.get("model_id"),
                    profile.get("position", {}).get("cluster_id"), json_dumps(dimensions), json_dumps(radar_features),
                    json_dumps(profile_snapshot), "relationship_pilot_stage2_v1", review_status, timestamp, timestamp,
                ),
            )
        except Exception:
            existing = conn.execute(
                "SELECT * FROM relationship_pilot_enrollments WHERE assessment_result_id = ?",
                (result["id"],),
            ).fetchone()
            if existing:
                return ServiceResult(expand_enrollment(row_to_dict(existing)))
            raise
        write_audit_log(conn, "relationship_enrollment_created", user_id, "relationship_pilot_enrollment", enrollment_id, {"assessment_result_id": result["id"], "consent_scope": "relationship_pilot_stage2_v1"})
        conn.commit()
        created = conn.execute("SELECT * FROM relationship_pilot_enrollments WHERE id = ?", (enrollment_id,)).fetchone()
    return ServiceResult(expand_enrollment(row_to_dict(created)), 201)


def list_enrollments(actor: dict) -> ServiceResult:
    where = "" if actor.get("role") in RESEARCH_ROLES else "WHERE user_id = ?"
    params = [] if not where else [actor["id"]]
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT e.*,
                   (SELECT id FROM relationship_screening_reports r WHERE r.enrollment_id = e.id ORDER BY created_at DESC LIMIT 1) AS report_id,
                   (SELECT status FROM relationship_screening_reports r WHERE r.enrollment_id = e.id ORDER BY created_at DESC LIMIT 1) AS report_status,
                   (SELECT COUNT(*) FROM relationship_pilot_tasks t WHERE t.enrollment_id = e.id) AS tasks_count
            FROM relationship_pilot_enrollments e {where}
            ORDER BY e.created_at DESC
            """,
            params,
        ).fetchall()
    items = [expand_enrollment(item) for item in rows_to_dicts(rows)]
    return ServiceResult({"items": items, "count": len(items)})


def get_enrollment(actor: dict, enrollment_id: str) -> ServiceResult:
    with get_connection() as conn:
        item = enrollment_by_id(conn, enrollment_id)
        if not item:
            raise RelationshipPilotError("not_found", "没有找到报名记录。", 404)
        if not own_or_researcher(actor, item["user_id"]):
            raise RelationshipPilotError("forbidden", "无权查看该报名记录。", 403)
        tasks = rows_to_dicts(conn.execute("SELECT * FROM relationship_pilot_tasks WHERE enrollment_id = ? ORDER BY created_at", (enrollment_id,)).fetchall())
        reports = rows_to_dicts(conn.execute("SELECT id, status, version, created_at, confirmed_at FROM relationship_screening_reports WHERE enrollment_id = ? ORDER BY created_at DESC", (enrollment_id,)).fetchall())
        notes = []
        if actor.get("role") in RESEARCH_ROLES:
            notes = rows_to_dicts(conn.execute("SELECT * FROM relationship_research_notes WHERE enrollment_id = ? ORDER BY created_at", (enrollment_id,)).fetchall())
        write_audit_log(conn, "relationship_enrollment_viewed", actor["id"], "relationship_pilot_enrollment", enrollment_id, {"role": actor.get("role"), "contains_sensitive_material": bool(tasks)})
        conn.commit()
    expanded = expand_enrollment(item)
    expanded["tasks"] = [expand_task(task) for task in tasks]
    expanded["reports"] = reports
    expanded["research_notes"] = notes
    return ServiceResult(expanded)
