"""SQLite schema for the SafeHome MVP backend."""

MVP_TABLES = [
    "users",
    "schema_migrations",
    "goals",
    "emotion_diaries",
    "emotion_thermometer",
    "feedback_results",
    "training_cards",
    "checkins",
    "assessment_worksheets",
    "assessment_results",
    "student_profiles",
    "profile_reviews",
    "student_profile_followups",
    "student_sandplay_entries",
    "parent_assessment_submissions",
    "parent_report_actions",
    "records",
    "audit_logs",
    "privacy_requests",
    "family_links",
    "weekly_reports",
    "supervision_requests",
    "messages",
    "notification_preferences",
    "notification_deliveries",
    "relationship_pilot_enrollments",
    "relationship_screening_reports",
    "relationship_pilot_tasks",
    "relationship_research_notes",
    "relationship_narratives",
    "relationship_longitudinal_entries",
    "relationship_hypothesis_feedback",
]


SCHEMA_SQL = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        nickname TEXT,
        role TEXT DEFAULT 'parent',
        source TEXT,
        username TEXT,
        phone_or_email TEXT,
        password_hash TEXT,
        anonymous_id TEXT,
        wechat_openid TEXT,
        phone_hash TEXT,
        avatar_url TEXT,
        status TEXT DEFAULT 'active',
        last_login_at TEXT,
        phone_verified_at TEXT,
        phone_source TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS relationship_pilot_enrollments (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        assessment_result_id TEXT NOT NULL,
        worksheet_id TEXT NOT NULL,
        profile_model_id TEXT,
        profile_cluster_id INTEGER,
        dimensions_json TEXT NOT NULL DEFAULT '[]',
        radar_features_json TEXT NOT NULL DEFAULT '[]',
        profile_json TEXT NOT NULL DEFAULT '{}',
        consent_scope TEXT NOT NULL,
        assigned_researcher_id TEXT,
        status TEXT NOT NULL DEFAULT 'enrolled',
        review_status TEXT NOT NULL DEFAULT 'pending_review',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS relationship_screening_reports (
        id TEXT PRIMARY KEY,
        enrollment_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        assessment_result_id TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending_review',
        version TEXT NOT NULL,
        report_json TEXT NOT NULL,
        confirmed_by TEXT,
        confirmed_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS relationship_pilot_tasks (
        id TEXT PRIMARY KEY,
        enrollment_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        task_type TEXT NOT NULL,
        drawing_data_json TEXT NOT NULL DEFAULT '{}',
        narration TEXT,
        answers_json TEXT NOT NULL DEFAULT '{}',
        material_consent INTEGER NOT NULL DEFAULT 0,
        risk_level TEXT NOT NULL DEFAULT 'low',
        review_status TEXT NOT NULL DEFAULT 'pending_review',
        idempotency_key TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS relationship_research_notes (
        id TEXT PRIMARY KEY,
        enrollment_id TEXT NOT NULL,
        researcher_id TEXT NOT NULL,
        note TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS relationship_narratives (
        id TEXT PRIMARY KEY,
        enrollment_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        draft_json TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'draft',
        confirmed_by TEXT,
        confirmed_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS relationship_longitudinal_entries (
        id TEXT PRIMARY KEY,
        enrollment_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        entry_type TEXT NOT NULL,
        measures_json TEXT NOT NULL DEFAULT '{}',
        narratives_json TEXT NOT NULL DEFAULT '{}',
        event_at TEXT,
        risk_level TEXT NOT NULL DEFAULT 'low',
        review_status TEXT NOT NULL DEFAULT 'recorded',
        idempotency_key TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS relationship_hypothesis_feedback (
        id TEXT PRIMARY KEY,
        report_id TEXT NOT NULL,
        enrollment_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        hypothesis_index INTEGER NOT NULL,
        response TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(report_id, user_id, hypothesis_index)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS privacy_requests (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        request_type TEXT NOT NULL,
        reason TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        handled_by TEXT,
        handled_note TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS family_links (
        id TEXT PRIMARY KEY,
        parent_user_id TEXT NOT NULL,
        student_user_id TEXT,
        bind_code TEXT NOT NULL,
        relation_label TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        expires_at TEXT,
        attempt_count INTEGER NOT NULL DEFAULT 0,
        last_attempt_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        confirmed_at TEXT,
        revoked_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        applied_at TEXT NOT NULL
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
    CREATE TABLE IF NOT EXISTS emotion_thermometer (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        intensity_level INTEGER NOT NULL,
        valence_level INTEGER,
        arousal_level INTEGER,
        control_level INTEGER,
        emotion_label TEXT,
        brief_text TEXT,
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
        helpfulness_rating TEXT,
        skip_reason TEXT,
        source_recommendation_id TEXT,
        before_thermometer_id TEXT,
        after_thermometer_id TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS assessment_worksheets (
        id TEXT PRIMARY KEY,
        display_title TEXT NOT NULL,
        source_title TEXT,
        source_file TEXT,
        category TEXT,
        audience_class TEXT,
        reflex_node TEXT,
        questions_json TEXT NOT NULL DEFAULT '[]',
        dimensions_json TEXT NOT NULL DEFAULT '[]',
        dimension_score_method TEXT NOT NULL DEFAULT 'sum',
        scoring_notes_json TEXT NOT NULL DEFAULT '{}',
        search_keywords_json TEXT NOT NULL DEFAULT '[]',
        boundary_notice TEXT,
        result_disclaimer TEXT,
        instructions TEXT,
        sensitive_category TEXT NOT NULL DEFAULT 'none',
        profile_model_id TEXT,
        enabled_for_user INTEGER NOT NULL DEFAULT 1,
        review_status TEXT NOT NULL DEFAULT 'approved',
        review_note TEXT,
        source_version TEXT,
        source_type TEXT,
        audience TEXT,
        audience_class_detail TEXT,
        recommended_card_ids_json TEXT NOT NULL DEFAULT '[]',
        sections_json TEXT NOT NULL DEFAULT '[]',
        scoring TEXT,
        pages INTEGER,
        _meta_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
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
        profile_model_id TEXT,
        profile_cluster_id INTEGER,
        profile_pc1 REAL,
        profile_pc2 REAL,
        profile_confidence REAL,
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
        model_version TEXT,
        model_type TEXT,
        cluster_id INTEGER,
        pc1 REAL,
        pc2 REAL,
        nearest_distance REAL,
        second_distance REAL,
        report_json TEXT NOT NULL DEFAULT '{}',
        visuals_json TEXT NOT NULL DEFAULT '{}',
        legacy_source_id TEXT,
        legacy_source_table TEXT,
        export_allowed INTEGER NOT NULL DEFAULT 1,
        data_quality TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS student_profile_followups (
        id TEXT PRIMARY KEY,
        profile_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        round_no INTEGER NOT NULL,
        fit TEXT,
        task_done TEXT,
        state_score INTEGER,
        text TEXT,
        keywords_json TEXT NOT NULL DEFAULT '[]',
        created_at TEXT NOT NULL,
        export_allowed INTEGER NOT NULL DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS student_sandplay_entries (
        id TEXT PRIMARY KEY,
        profile_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        task_title TEXT,
        scene_json TEXT NOT NULL,
        reflection_text TEXT,
        summary_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        export_allowed INTEGER NOT NULL DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS parent_assessment_submissions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        anonymous_id TEXT NOT NULL,
        participant_code TEXT,
        research_consent INTEGER NOT NULL DEFAULT 0,
        study_batch TEXT,
        source_channel TEXT,
        questionnaire_version TEXT,
        scoring_version TEXT,
        answers_json TEXT NOT NULL,
        scores_json TEXT NOT NULL,
        profile_key TEXT,
        report_json TEXT NOT NULL,
        started_at TEXT,
        completed_at TEXT,
        duration_seconds INTEGER NOT NULL DEFAULT 0,
        quality_flags_json TEXT NOT NULL DEFAULT '{}',
        legacy_source_id TEXT,
        legacy_source_table TEXT,
        export_allowed INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS parent_report_actions (
        id TEXT PRIMARY KEY,
        submission_id TEXT NOT NULL,
        action_key TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS profile_reviews (
        id TEXT PRIMARY KEY,
        profile_id TEXT NOT NULL,
        reviewer_id TEXT,
        review_status TEXT NOT NULL DEFAULT 'reviewed',
        review_decision TEXT,
        note TEXT,
        action_summary TEXT,
        visible_to_student INTEGER NOT NULL DEFAULT 0,
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
    CREATE TABLE IF NOT EXISTS consent_records (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        consent_type TEXT NOT NULL,
        consent_version TEXT NOT NULL,
        agreed INTEGER NOT NULL,
        agreed_at TEXT NOT NULL,
        revoked_at TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS risk_review_records (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        source_type TEXT NOT NULL,
        source_id TEXT NOT NULL,
        risk_level TEXT NOT NULL,
        matched_categories_json TEXT NOT NULL DEFAULT '[]',
        review_status TEXT NOT NULL DEFAULT 'pending',
        reviewer_id TEXT,
        review_note TEXT,
        action_taken TEXT,
        closed_reason TEXT,
        reviewed_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
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
        assessment_summary_json TEXT NOT NULL DEFAULT '{}',
        thermometer_summary_json TEXT NOT NULL DEFAULT '{}',
        training_effectiveness_summary_json TEXT NOT NULL DEFAULT '{}',
        next_week_suggestion TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS supervision_requests (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        diary_id TEXT,
        source_type TEXT,
        source_id TEXT,
        source_title TEXT,
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
    """
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        sender_id TEXT,
        sender_role TEXT,
        message_type TEXT NOT NULL,
        title TEXT NOT NULL,
        body TEXT,
        source_type TEXT,
        source_id TEXT,
        idempotency_key TEXT,
        status TEXT NOT NULL DEFAULT 'unread',
        created_at TEXT NOT NULL,
        read_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS notification_preferences (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        channel TEXT NOT NULL,
        notification_type TEXT NOT NULL,
        template_id TEXT NOT NULL,
        subscription_mode TEXT NOT NULL DEFAULT 'once',
        consent_status TEXT NOT NULL DEFAULT 'unknown',
        consent_source TEXT,
        consented_at TEXT,
        last_prompted_at TEXT,
        revoked_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS notification_deliveries (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        preference_id TEXT,
        notification_type TEXT NOT NULL,
        template_id TEXT NOT NULL,
        schedule_key TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        attempt_count INTEGER NOT NULL DEFAULT 0,
        scheduled_for TEXT NOT NULL,
        sent_at TEXT,
        provider_message_id TEXT,
        error_code TEXT,
        error_message TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
]


INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_emotion_diaries_user_created ON emotion_diaries(user_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_emotion_thermometer_user_created ON emotion_thermometer(user_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
    "CREATE INDEX IF NOT EXISTS idx_users_wechat_openid ON users(wechat_openid)",
    "CREATE INDEX IF NOT EXISTS idx_users_phone_hash ON users(phone_hash)",
    "CREATE INDEX IF NOT EXISTS idx_feedback_results_user_created ON feedback_results(user_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_assessment_results_user_created ON assessment_results(user_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_assessment_results_profile_model ON assessment_results(profile_model_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_student_profiles_user_created ON student_profiles(user_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_student_profiles_risk_created ON student_profiles(risk_level, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_risk_review_status_created ON risk_review_records(review_status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_action_created ON audit_logs(action, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_records_module_created ON records(module_type, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_records_user_module_source_created ON records(user_id, module_type, source_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_privacy_requests_user_created ON privacy_requests(user_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_family_links_code_status ON family_links(bind_code, status)",
    "CREATE INDEX IF NOT EXISTS idx_assessment_worksheets_audience_enabled ON assessment_worksheets(audience_class, enabled_for_user)",
    "CREATE INDEX IF NOT EXISTS idx_messages_user_status_created ON messages(user_id, status, created_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_sender_idempotency ON messages(sender_id, idempotency_key)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_notification_preference_unique ON notification_preferences(user_id, notification_type, template_id)",
    "CREATE INDEX IF NOT EXISTS idx_notification_preference_status ON notification_preferences(consent_status, notification_type)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_notification_delivery_idempotency ON notification_deliveries(idempotency_key)",
    "CREATE INDEX IF NOT EXISTS idx_notification_delivery_user_created ON notification_deliveries(user_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_relationship_hypothesis_report ON relationship_hypothesis_feedback(report_id, hypothesis_index)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_relationship_enrollment_assessment_unique ON relationship_pilot_enrollments(assessment_result_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_relationship_report_version_unique ON relationship_screening_reports(enrollment_id, version)",
    "CREATE INDEX IF NOT EXISTS idx_relationship_enrollment_assigned ON relationship_pilot_enrollments(assigned_researcher_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_relationship_task_idempotency_unique ON relationship_pilot_tasks(user_id, idempotency_key)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_relationship_longitudinal_idempotency_unique ON relationship_longitudinal_entries(user_id, idempotency_key)",
]

IDENTITY_UNIQUE_INDEX_SQL = [
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_unique ON users(username)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_wechat_openid_unique ON users(wechat_openid)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone_hash_unique ON users(phone_hash)",
]
