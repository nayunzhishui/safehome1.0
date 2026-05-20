"""Seed demo data for the SafeHome MVP backend."""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import ensure_user, get_connection, init_db, json_dumps, new_id, now_iso
from services.feedback_service import generate_feedback


DEMO_USER_ID = "demo-parent"


def seed() -> None:
    init_db()
    timestamp = now_iso()

    with get_connection() as conn:
        ensure_user(conn, DEMO_USER_ID, "演示家长")

        goal_id = new_id("goal")
        conn.execute(
            """
            INSERT INTO goals (
                id, user_id, scene, smart_goal, motivation, start_date,
                status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, date('now'), 'active', ?, ?)
            """,
            (
                goal_id,
                DEMO_USER_ID,
                "作业拖延",
                "本周在孩子开始作业前，先用一句观察句替代催促。",
                "减少晚上作业时的冲突。",
                timestamp,
                timestamp,
            ),
        )

        diary_id = new_id("diary")
        diary_payload = {
            "user_id": DEMO_USER_ID,
            "goal_id": goal_id,
            "scene": "作业拖延",
            "event_description": "孩子回家后一直不写作业，我忍不住说了好几次你怎么又这样。",
            "parent_emotion": "着急",
            "parent_emotion_intensity": 8,
            "child_emotion": "烦躁",
            "child_emotion_intensity": 7,
            "automatic_thought": "他就是故意拖，不想学。",
            "body_sensation": "胸口发紧，说话变快。",
            "behavior": "反复催促，语气变重。",
            "raw_text": "我说多少遍了，你必须马上写。",
        }
        conn.execute(
            """
            INSERT INTO emotion_diaries (
                id, user_id, goal_id, event_time, scene, event_description,
                parent_emotion, parent_emotion_intensity, child_emotion,
                child_emotion_intensity, automatic_thought, body_sensation,
                behavior, raw_text, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                diary_id,
                DEMO_USER_ID,
                goal_id,
                timestamp,
                diary_payload["scene"],
                diary_payload["event_description"],
                diary_payload["parent_emotion"],
                diary_payload["parent_emotion_intensity"],
                diary_payload["child_emotion"],
                diary_payload["child_emotion_intensity"],
                diary_payload["automatic_thought"],
                diary_payload["body_sensation"],
                diary_payload["behavior"],
                diary_payload["raw_text"],
                timestamp,
                timestamp,
            ),
        )

        feedback = generate_feedback(diary_payload)
        conn.execute(
            """
            INSERT INTO feedback_results (
                id, user_id, diary_id, tags_json, trigger_summary,
                pattern_summary, supportive_feedback, alternative_response,
                recommended_card_ids_json, risk_level, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("feedback"),
                DEMO_USER_ID,
                diary_id,
                json_dumps(feedback["tags"]),
                feedback["trigger_summary"],
                feedback["pattern_summary"],
                feedback["supportive_feedback"],
                feedback["alternative_response"],
                json_dumps(feedback["recommended_card_ids"]),
                feedback["risk_level"],
                timestamp,
            ),
        )

        conn.execute(
            """
            INSERT INTO checkins (
                id, user_id, card_id, diary_id, completed, emotion_before,
                emotion_after, reflection, created_at
            )
            VALUES (?, ?, ?, ?, 1, 8, 5, ?, ?)
            """,
            (
                new_id("checkin"),
                DEMO_USER_ID,
                "three_second_pause",
                diary_id,
                "暂停后语气更慢，孩子愿意说第一句话。",
                timestamp,
            ),
        )

        conn.execute(
            """
            INSERT INTO supervision_requests (
                id, user_id, diary_id, message, contact, risk_hint,
                risk_level, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'low', 'pending', ?)
            """,
            (
                new_id("supervision"),
                DEMO_USER_ID,
                diary_id,
                "想请老师看看我这次回应还能怎么调整。",
                "demo@example.com",
                "无高风险，仅请求人工建议。",
                timestamp,
            ),
        )

        conn.commit()

    print(f"Seed data created for user_id={DEMO_USER_ID}")


if __name__ == "__main__":
    seed()
