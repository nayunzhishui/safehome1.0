"""Choose one privacy-minimized participant action from existing workflow facts."""

from urllib.parse import quote

from database import get_connection, json_loads, now_iso, row_to_dict
from services.training_schedule_service import assignment_schedule, current_local_day, parse_day


ASSIGNMENT_MODULE_TYPE = "training_plan_assignment"
ASSIGNMENT_SOURCE_ID = "current"
FEEDBACK_MESSAGE_TYPES = {
    "relationship_stage_feedback",
    "relationship_report",
    "relationship_narrative",
    "researcher_message",
    "supervision_feedback",
}


def _action(
    action_type: str,
    title: str,
    description: str,
    button_label: str,
    url: str,
    *,
    source_type: str,
    source_id: str | None = None,
    estimated_minutes: int | None = None,
) -> dict:
    return {
        "type": action_type,
        "title": title,
        "description": description,
        "button_label": button_label,
        "url": url,
        "source_type": source_type,
        "source_id": source_id,
        "estimated_minutes": estimated_minutes,
    }

def _latest_assignment(conn, user_id: str) -> tuple[dict | None, str | None]:
    row = conn.execute(
        """
        SELECT id, data_json
        FROM records
        WHERE user_id = ? AND module_type = ? AND source_id = ?
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        (user_id, ASSIGNMENT_MODULE_TYPE, ASSIGNMENT_SOURCE_ID),
    ).fetchone()
    if row is None:
        return None, None
    item = row_to_dict(row)
    return json_loads(item.get("data_json"), {}), item.get("id")


def _base_action(
    *,
    assessment_count: int,
    diary_count: int,
    latest_checkin_at: str | None,
    assignment: dict | None,
    assignment_id: str | None,
) -> tuple[str, dict]:
    today = current_local_day()
    schedule = assignment_schedule(assignment, latest_checkin_at)
    completed_today = parse_day(latest_checkin_at) == today

    if schedule and schedule.get("status") == "paused":
        return "paused", _action(
            "training_paused",
            "练习计划当前已暂停",
            "恢复前不会安排新的练习，你可以先查看或调整练习节奏。",
            "查看练习节奏",
            "/pages/personalized-plan/index",
            source_type=ASSIGNMENT_MODULE_TYPE,
            source_id=assignment_id,
        )
    if schedule and schedule.get("status") == "completed":
        return "completed", _action(
            "training_stage_completed",
            "这一阶段已经完成",
            "可以回看近期记录，或在准备好时重新设置练习节奏。",
            "查看本周复盘",
            "/pages/weekly-report/index",
            source_type=ASSIGNMENT_MODULE_TYPE,
            source_id=assignment_id,
        )
    if completed_today:
        return "completed", _action(
            "today_completed",
            "今天的一小步已经完成",
            "不用继续赶进度，可以简单回看今天留下的记录。",
            "查看今天的记录",
            "/pages/weekly-report/index",
            source_type="checkin",
            estimated_minutes=1,
        )
    if schedule and schedule.get("is_due_today"):
        return "ready", _action(
            "practice_due",
            "完成一次轻量练习",
            schedule.get("due_reason") or "今天已到练习时间，先选一张最容易完成的卡。",
            "选择今天的练习",
            "/pages/personalized-plan/index",
            source_type=ASSIGNMENT_MODULE_TYPE,
            source_id=assignment_id,
            estimated_minutes=5,
        )
    if assessment_count == 0:
        return "ready", _action(
            "start_assessment",
            "先完成一次支持性测评",
            "用几分钟了解当前状态，再决定今天最适合从哪里开始。",
            "去测一测",
            "/pages/assessment/index",
            source_type="assessment_results",
            estimated_minutes=5,
        )
    if diary_count == 0:
        return "ready", _action(
            "start_diary",
            "记录一件刚发生的小事",
            "写清具体场景，比一次解释很多事情更容易开始。",
            "记录一次",
            "/pages/diary-form/index",
            source_type="emotion_diaries",
            estimated_minutes=3,
        )
    if schedule is None:
        return "ready", _action(
            "set_training_cadence",
            "设置适合自己的练习节奏",
            "由你决定练习频率，系统只在到期时提醒下一步。",
            "设置练习节奏",
            "/pages/personalized-plan/index",
            source_type=ASSIGNMENT_MODULE_TYPE,
            estimated_minutes=2,
        )
    return "not_due", _action(
        "training_not_due",
        "今天不用赶练习进度",
        schedule.get("due_reason") or "当前没有到期练习，可以按自己的节奏继续。",
        "查看练习节奏",
        "/pages/personalized-plan/index",
        source_type=ASSIGNMENT_MODULE_TYPE,
        source_id=assignment_id,
    )


def build_today_journey(user_id: str) -> dict:
    with get_connection() as conn:
        unread = conn.execute(
            """
            SELECT id, title, message_type, source_type, source_id
            FROM messages
            WHERE user_id = ? AND status = 'unread'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        assessment_row = conn.execute(
            "SELECT COUNT(*) AS count FROM assessment_results WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        diary_row = conn.execute(
            "SELECT COUNT(*) AS count FROM emotion_diaries WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        checkin_row = conn.execute(
            """
            SELECT created_at
            FROM checkins
            WHERE user_id = ? AND completed = 1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        assignment, assignment_id = _latest_assignment(conn, user_id)

    state, primary_action = _base_action(
        assessment_count=int(assessment_row["count"] if assessment_row else 0),
        diary_count=int(diary_row["count"] if diary_row else 0),
        latest_checkin_at=checkin_row["created_at"] if checkin_row else None,
        assignment=assignment,
        assignment_id=assignment_id,
    )
    secondary_action = None
    if unread is not None:
        message = row_to_dict(unread)
        secondary_action = primary_action
        message_type = str(message.get("message_type") or "")
        is_feedback = message_type in FEEDBACK_MESSAGE_TYPES
        primary_action = _action(
            "read_feedback" if is_feedback else "read_message",
            message.get("title") or ("有一条新的补充反馈" if is_feedback else "有一条新消息"),
            "先查看这条消息，再决定是否继续今天的其他安排。",
            "查看反馈" if is_feedback else "查看消息",
            f"/pages/message-detail/index?id={quote(str(message['id']))}",
            source_type="message",
            source_id=message.get("id"),
            estimated_minutes=2,
        )
        state = "ready"

    return {
        "user_id": user_id,
        "state": state,
        "primary_action": primary_action,
        "secondary_action": secondary_action,
        "generated_at": now_iso(),
        "state_contract": {
            "reproducible_states": ["ready", "paused", "completed", "not_due", "recoverable_error", "controlled"],
            "loading": {"client_state": "loading", "preserve_previous_action": True},
            "failure": {"state": "recoverable_error", "show_retry": True, "never_render_as_empty": True},
            "weak_network_recovery": {"retry": "manual", "preserve_local_draft": True, "deduplicate_submit": True},
        },
        "controlled_capabilities": {
            "therapeutic_assessment": {
                "status": "governance_gate_pending",
                "enabled": False,
                "entry_url": None,
                "notice": "治疗性评估仍处于受控准备阶段，人工、伦理与发布门禁通过前不会进入参与者今日任务。",
            }
        },
        "boundary_notice": "今天的一小步只用于整理当前可继续的操作，不构成诊断、治疗安排或必须完成的任务。",
    }
