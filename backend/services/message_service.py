"""Small helpers for user-facing in-app messages."""

from database import new_id, now_iso, row_to_dict


def create_message(
    conn,
    user_id: str,
    title: str,
    body: str | None = None,
    message_type: str = "system",
    source_type: str | None = None,
    source_id: str | None = None,
    sender_id: str | None = None,
    sender_role: str | None = None,
    idempotency_key: str | None = None,
) -> dict:
    message_id = new_id("msg")
    timestamp = now_iso()
    conn.execute(
        """
        INSERT INTO messages (
            id, user_id, sender_id, sender_role, message_type, title, body,
            source_type, source_id, idempotency_key, status, created_at, read_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'unread', ?, NULL)
        """,
        (message_id, user_id, sender_id, sender_role, message_type, title, body, source_type, source_id, idempotency_key, timestamp),
    )
    row = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
    return row_to_dict(row) or {"id": message_id, "user_id": user_id}
