"""User-owned cross-module growth overview without mixing measurement scales."""

from __future__ import annotations

from collections import defaultdict

from flask import Blueprint, request

from database import get_connection, json_loads, rows_to_dicts
from routes.auth_utils import AuthError, auth_error_response, resolve_actor_user_id
from routes.utils import ok


bp = Blueprint("general_growth", __name__, url_prefix="/api/growth")


def _short_text(value, limit: int = 72) -> str:
    text = str(value or "").strip().replace("\n", " ")
    return text if len(text) <= limit else f"{text[:limit]}…"


@bp.get("/overview")
def get_growth_overview():
    try:
        user_id = resolve_actor_user_id(request.args.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)

    with get_connection() as conn:
        thermometer = rows_to_dicts(
            conn.execute(
                "SELECT id, intensity_level, emotion_label, created_at FROM emotion_thermometer WHERE user_id = ? ORDER BY created_at DESC LIMIT 30",
                (user_id,),
            ).fetchall()
        )
        assessments = rows_to_dicts(
            conn.execute(
                "SELECT id, worksheet_id, worksheet_title, total_score, created_at FROM assessment_results WHERE user_id = ? ORDER BY created_at DESC LIMIT 30",
                (user_id,),
            ).fetchall()
        )
        diaries = rows_to_dicts(
            conn.execute(
                "SELECT id, scene, event_description, parent_emotion, created_at FROM emotion_diaries WHERE user_id = ? ORDER BY created_at DESC LIMIT 30",
                (user_id,),
            ).fetchall()
        )
        checkins = rows_to_dicts(
            conn.execute(
                """
                SELECT c.id, c.card_id, c.completed, c.created_at,
                       COALESCE(t.title, c.card_id) AS card_title
                FROM checkins c
                LEFT JOIN training_cards t ON t.id = c.card_id
                WHERE c.user_id = ?
                ORDER BY c.created_at DESC
                LIMIT 30
                """,
                (user_id,),
            ).fetchall()
        )
        program_rows = rows_to_dicts(
            conn.execute(
                "SELECT id, source_id, data_json, created_at FROM records WHERE user_id = ? AND module_type = 'program_entry' ORDER BY created_at DESC LIMIT 30",
                (user_id,),
            ).fetchall()
        )
        weekly_reports = rows_to_dicts(
            conn.execute(
                "SELECT id, week_start, week_end, next_week_suggestion, created_at FROM weekly_reports WHERE user_id = ? ORDER BY created_at DESC LIMIT 12",
                (user_id,),
            ).fetchall()
        )
        feedback_rows = rows_to_dicts(
            conn.execute(
                """
                SELECT id, title, body, message_type, status, created_at
                FROM messages
                WHERE user_id = ?
                  AND message_type IN ('relationship_stage_feedback', 'researcher_message', 'relationship_report')
                ORDER BY created_at DESC
                LIMIT 20
                """,
                (user_id,),
            ).fetchall()
        )
        feedback_stats = conn.execute(
            """
            SELECT COUNT(*) AS count,
                   SUM(CASE WHEN status = 'unread' THEN 1 ELSE 0 END) AS unread_count
            FROM messages
            WHERE user_id = ?
              AND message_type IN ('relationship_stage_feedback', 'researcher_message', 'relationship_report')
            """,
            (user_id,),
        ).fetchone()
        latest_enrollment = conn.execute(
            """
            SELECT id, status, review_status, created_at
            FROM relationship_pilot_enrollments
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        relationship_counts = conn.execute(
            """
            SELECT
              (SELECT COUNT(*) FROM relationship_pilot_enrollments WHERE user_id = ?) AS enrollment_count,
              (SELECT COUNT(*) FROM relationship_pilot_tasks WHERE user_id = ?) AS task_count,
              (SELECT COUNT(*) FROM relationship_longitudinal_entries WHERE user_id = ?) AS longitudinal_count,
              (SELECT COUNT(*) FROM relationship_screening_reports WHERE user_id = ?) AS report_count
            """,
            (user_id, user_id, user_id, user_id),
        ).fetchone()
        relationship_tasks = rows_to_dicts(
            conn.execute(
                """
                SELECT id, task_type, review_status, created_at
                FROM relationship_pilot_tasks
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 20
                """,
                (user_id,),
            ).fetchall()
        )
        relationship_entries = rows_to_dicts(
            conn.execute(
                """
                SELECT id, entry_type, review_status, created_at
                FROM relationship_longitudinal_entries
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 20
                """,
                (user_id,),
            ).fetchall()
        )
        relationship_reports = rows_to_dicts(
            conn.execute(
                """
                SELECT id, version, status, created_at
                FROM relationship_screening_reports
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 20
                """,
                (user_id,),
            ).fetchall()
        )

    programs = []
    for row in program_rows:
        data = json_loads(row.pop("data_json", None), {})
        programs.append({**row, **data})

    assessment_groups = defaultdict(list)
    for item in assessments:
        assessment_groups[item["worksheet_id"]].append(
            {
                "id": item["id"],
                "title": item["worksheet_title"],
                "value": item["total_score"],
                "created_at": item["created_at"],
            }
        )

    timeline = []
    timeline.extend(
        {
            "id": item["id"],
            "type": "diary",
            "type_label": "情绪日记",
            "title": item["scene"] or "一次具体事件",
            "summary": _short_text(item["event_description"]),
            "created_at": item["created_at"],
        }
        for item in diaries
    )
    timeline.extend(
        {
            "id": item["id"],
            "type": "checkin",
            "type_label": "训练打卡",
            "title": item["card_title"],
            "summary": "完成了一次练习" if item["completed"] else "记录了一次暂停或未完成",
            "created_at": item["created_at"],
        }
        for item in checkins
    )
    timeline.extend(
        {
            "id": item["id"],
            "type": "assessment",
            "type_label": "支持性测评",
            "title": item["worksheet_title"],
            "summary": "保存了一次阶段性自我观察",
            "created_at": item["created_at"],
        }
        for item in assessments
    )
    timeline.extend(
        {
            "id": item["id"],
            "type": "program",
            "type_label": "项目练习",
            "title": item.get("program_title") or "项目练习",
            "summary": f"完成第 {item.get('session_no') or '-'} 节记录",
            "created_at": item["created_at"],
        }
        for item in programs
    )
    timeline.extend(
        {
            "id": item["id"],
            "type": "report",
            "type_label": "本周复盘",
            "title": f"{item['week_start']} 至 {item['week_end']}",
            "summary": _short_text(item["next_week_suggestion"]) or "生成了一次本周复盘",
            "created_at": item["created_at"],
        }
        for item in weekly_reports
    )
    timeline.extend(
        {
            "id": item["id"],
            "type": "feedback",
            "type_label": "人工反馈",
            "title": item["title"] or "研究者补充反馈",
            "summary": _short_text(item["body"]),
            "created_at": item["created_at"],
        }
        for item in feedback_rows
    )
    timeline.extend(
        {
            "id": item["id"],
            "type": "relationship_task",
            "type_label": "关系探索",
            "title": "完成了一次关系探索任务",
            "summary": "任务状态已记录，具体内容仍在原记录中查看。",
            "created_at": item["created_at"],
        }
        for item in relationship_tasks
    )
    timeline.extend(
        {
            "id": item["id"],
            "type": "relationship_record",
            "type_label": "关系连续记录",
            "title": "留下了一次关系探索记录",
            "summary": "本次只汇总记录事实，不自动解释关系变化。",
            "created_at": item["created_at"],
        }
        for item in relationship_entries
    )
    timeline.extend(
        {
            "id": item["id"],
            "type": "relationship_report",
            "type_label": "关系阶段报告",
            "title": f"关系阶段报告 · {item['version']}",
            "summary": "报告与测评量尺分开呈现，需要时可回到关系探索中查看。",
            "created_at": item["created_at"],
        }
        for item in relationship_reports
    )
    timeline.sort(key=lambda item: item["created_at"] or "", reverse=True)

    activity_count = len(diaries) + len(checkins) + len(assessments) + len(programs)
    record_count = len(diaries) + len(programs) + len(weekly_reports)
    completed_practice_count = sum(1 for item in checkins if item["completed"])
    assessment_group_rows = [
        {"worksheet_id": worksheet_id, "title": rows[0]["title"], "items": list(reversed(rows))}
        for worksheet_id, rows in assessment_groups.items()
    ]
    relationship_count_data = {
        "enrollment_count": int(relationship_counts["enrollment_count"] or 0),
        "task_count": int(relationship_counts["task_count"] or 0),
        "longitudinal_count": int(relationship_counts["longitudinal_count"] or 0),
        "report_count": int(relationship_counts["report_count"] or 0),
    }
    feedback_count = int(feedback_stats["count"] or 0)
    feedback_unread_count = int(feedback_stats["unread_count"] or 0)
    if activity_count == 0:
        next_step = "可以先完成一次情绪温度记录、情绪日记或支持性测评，给自己留下一个起点。"
    elif not checkins:
        next_step = "已有一些观察记录；如果愿意，可以从推荐训练中选一个低负担动作试一次。"
    else:
        next_step = "继续按自己的节奏记录即可。等同类记录积累后，再观察变化，不急着下结论。"

    return ok(
        {
            "summary": {
                "record_count": activity_count,
                "practice_count": completed_practice_count,
                "feedback_count": feedback_count,
                "next_step": next_step,
            },
            "sections": {
                "activity": {
                    "available": bool(record_count or checkins),
                    "record_count": record_count,
                    "practice_count": completed_practice_count,
                },
                "assessments": {
                    "available": bool(assessment_group_rows),
                    "record_count": len(assessments),
                    "group_count": len(assessment_group_rows),
                    "repeat_group_count": sum(1 for group in assessment_group_rows if len(group["items"]) >= 2),
                },
                "relationship": {
                    "available": relationship_count_data["enrollment_count"] > 0,
                    **relationship_count_data,
                    "latest_enrollment_id": latest_enrollment["id"] if latest_enrollment else None,
                    "status": latest_enrollment["status"] if latest_enrollment else None,
                    "review_status": latest_enrollment["review_status"] if latest_enrollment else None,
                },
                "researcher_feedback": {
                    "available": feedback_count > 0,
                    "count": feedback_count,
                    "unread_count": feedback_unread_count,
                    "latest": {
                        "id": feedback_rows[0]["id"],
                        "title": feedback_rows[0]["title"],
                        "created_at": feedback_rows[0]["created_at"],
                    }
                    if feedback_rows
                    else None,
                },
            },
            "thermometer": list(reversed(thermometer)),
            "assessment_groups": assessment_group_rows,
            "timeline": timeline[:50],
            "boundary_notice": "本页只汇总你已保存的记录。不同量尺分开呈现；记录变化不等于诊断、能力评价或疗效证明。",
        }
    )
