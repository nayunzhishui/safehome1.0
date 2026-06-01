"""SQLite schema for the SafeHome MVP backend."""

MVP_TABLES = [
    "users",
    "goals",
    "emotion_diaries",
    "feedback_results",
    "training_cards",
    "checkins",
    "assessment_results",
    "student_profiles",
    "records",
    "audit_logs",
    "weekly_reports",
    "supervision_requests",
]


SCHEMA_SQL = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        nickname TEXT,
        role TEXT DEFAULT 'parent',
        source TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS goals (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        scene TEXT NOT NULL,
        smart_goal TEXT NOT NULL,
        motivation TEXT,
        start_date TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS emotion_diaries (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        goal_id TEXT,
        event_time TEXT,
        scene TEXT NOT NULL,
        event_description TEXT NOT NULL,
        parent_emotion TEXT NOT NULL,
        parent_emotion_intensity INTEGER NOT NULL,
        child_emotion TEXT,
        child_emotion_intensity INTEGER,
        automatic_thought TEXT,
        body_sensation TEXT,
        behavior TEXT,
        raw_text TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS feedback_results (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        diary_id TEXT,
        tags_json TEXT NOT NULL,
        trigger_summary TEXT,
        pattern_summary TEXT,
        supportive_feedback TEXT NOT NULL,
        alternative_response TEXT,
        recommended_card_ids_json TEXT NOT NULL,
        risk_level TEXT NOT NULL DEFAULT 'low',
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS training_cards (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        title TEXT NOT NULL,
        purpose TEXT,
        steps_json TEXT NOT NULL,
        tags_json TEXT NOT NULL,
        example TEXT,
        duration_minutes INTEGER,
        enabled INTEGER NOT NULL DEFAULT 1,
        version TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS checkins (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        card_id TEXT NOT NULL,
        diary_id TEXT,
        completed INTEGER NOT NULL,
        emotion_before INTEGER,
        emotion_after INTEGER,
        reflection TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS assessment_results (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        worksheet_id TEXT NOT NULL,
        worksheet_title TEXT NOT NULL,
        category TEXT,
        answers_json TEXT NOT NULL,
        scores_json TEXT NOT NULL,
        total_score INTEGER,
        result_summary TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS student_profiles (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        anonymous_id TEXT NOT NULL,
        assessment_result_id TEXT,
        round INTEGER NOT NULL DEFAULT 1,
        source TEXT,
        scores_json TEXT NOT NULL,
        text_features_json TEXT NOT NULL,
        profile_code TEXT NOT NULL,
        profile_name TEXT NOT NULL,
        confidence REAL,
        dimensions_json TEXT NOT NULL,
        recommended_task_ids_json TEXT NOT NULL,
        risk_level TEXT NOT NULL DEFAULT 'low',
        requires_review INTEGER NOT NULL DEFAULT 0,
        boundary_notice TEXT,
        rules_version TEXT,
        export_allowed INTEGER NOT NULL DEFAULT 1,
        data_quality TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS records (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        module_type TEXT NOT NULL,
        source_id TEXT,
        data_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        export_allowed INTEGER NOT NULL DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS audit_logs (
        id TEXT PRIMARY KEY,
        actor_id TEXT,
        action TEXT NOT NULL,
        target_type TEXT,
        target_id TEXT,
        metadata_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS weekly_reports (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        week_start TEXT NOT NULL,
        week_end TEXT NOT NULL,
        frequent_scenes_json TEXT NOT NULL,
        frequent_emotions_json TEXT NOT NULL,
        common_patterns_json TEXT NOT NULL,
        completed_cards_json TEXT NOT NULL,
        next_week_suggestion TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS supervision_requests (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        diary_id TEXT,
        message TEXT NOT NULL,
        contact TEXT,
        risk_hint TEXT,
        risk_level TEXT NOT NULL DEFAULT 'low',
        status TEXT NOT NULL DEFAULT 'pending',
        supervisor_reply TEXT,
        created_at TEXT NOT NULL,
        replied_at TEXT
    )
    """,
]
