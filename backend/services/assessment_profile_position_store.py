"""Persist normalized assessment profile positions."""


def profile_cluster_value(position: dict | None) -> int | None:
    cluster_id = (position or {}).get("cluster_id")
    if cluster_id is None or cluster_id == "":
        return None
    try:
        return int(cluster_id)
    except (TypeError, ValueError):
        return None


def backfill_profile_position(conn, result_id: str, position: dict) -> None:
    position_data = position.get("position") or {}
    conn.execute(
        """
        UPDATE assessment_results SET
            profile_model_id = ?,
            profile_cluster_id = ?,
            profile_pc1 = ?,
            profile_pc2 = ?,
            profile_confidence = ?
        WHERE id = ?
        """,
        (
            position.get("model_id"),
            profile_cluster_value(position_data),
            position_data.get("pc1"),
            position_data.get("pc2"),
            position_data.get("confidence"),
            result_id,
        ),
    )
