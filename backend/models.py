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
    "privacy_request_actions",
    "family_links",
    "weekly_reports",
    "supervision_requests",
    "messages",
    "notification_preferences",
    "notification_deliveries",
    "research_work_items",
    "research_work_item_notes",
    "research_work_item_actions",
    "data_claims",
    "relationship_pilot_enrollments",
    "relationship_screening_reports",
    "relationship_pilot_tasks",
    "relationship_research_notes",
    "relationship_narratives",
    "relationship_longitudinal_entries",
    "relationship_hypothesis_feedback",
    "research_scope_assignments",
    "research_scope_assignment_actions",
    "research_delivery_workflows",
    "research_delivery_versions",
    "research_delivery_events",
    "feedback_ledger",
    "feedback_ledger_actions",
    "recommendation_snapshots",
    "security_control_runs",
    "security_events",
    "privacy_deletion_verifications",
    "observability_events",
    "reliable_jobs",
    "reliable_job_actions",
    "research_analysis_snapshots",
    "research_analysis_snapshot_links",
    "research_analysis_jobs",
    "research_analysis_artifacts",
    "research_analysis_events",
    "feature_flag_versions",
    "reliability_slo_snapshots",
    "reliability_drill_runs",
    "reliability_evidence_packages",
    "ux_audit_runs",
    "ux_evidence_packages",
    "operations_release_packages",
    "operations_package_reviews",
    "operations_replay_runs",
    "operations_runtime_controls",
    "operations_monitor_snapshots",
    "operations_incidents",
    "operations_incident_notifications",
    "operations_evidence_packages",
    "computation_datasets",
    "computation_authorization_snapshots",
    "computation_lineage_edges",
    "computation_deletion_tombstones",
    "computation_legal_holds",
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
        auth_epoch INTEGER NOT NULL DEFAULT 0,
        must_change_password INTEGER NOT NULL DEFAULT 0,
        credential_receipt_id TEXT,
        credential_expires_at TEXT,
        password_changed_at TEXT,
        failed_login_count INTEGER NOT NULL DEFAULT 0,
        last_failed_login_at TEXT,
        locked_until TEXT,
        status_reason TEXT,
        last_login_at TEXT,
        phone_verified_at TEXT,
        phone_source TEXT,
        merged_into_user_id TEXT,
        merged_at TEXT,
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
    CREATE TABLE IF NOT EXISTS research_scope_assignments (
        id TEXT PRIMARY KEY,
        enrollment_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        assignment_role TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        version INTEGER NOT NULL DEFAULT 1,
        idempotency_key TEXT,
        assigned_by TEXT NOT NULL,
        revoked_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_scope_assignment_actions (
        id TEXT PRIMARY KEY,
        assignment_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        action TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        request_hash TEXT NOT NULL,
        result_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_delivery_workflows (
        id TEXT PRIMARY KEY,
        enrollment_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        delivery_type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'draft',
        title TEXT NOT NULL,
        draft_json TEXT NOT NULL DEFAULT '{}',
        active_version_id TEXT,
        source_report_id TEXT,
        message_id TEXT,
        version INTEGER NOT NULL DEFAULT 0,
        create_idempotency_key TEXT NOT NULL,
        confirmed_at TEXT,
        sent_at TEXT,
        withdrawn_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(actor_id, create_idempotency_key)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_delivery_versions (
        id TEXT PRIMARY KEY,
        workflow_id TEXT NOT NULL,
        version_no INTEGER NOT NULL,
        title TEXT NOT NULL,
        content_json TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        risk_level TEXT NOT NULL DEFAULT 'low',
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(workflow_id, version_no)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_delivery_events (
        id TEXT PRIMARY KEY,
        workflow_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        action TEXT NOT NULL,
        from_status TEXT,
        to_status TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        idempotency_key TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(actor_id, idempotency_key)
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
    CREATE TABLE IF NOT EXISTS feedback_ledger (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        source_type TEXT NOT NULL,
        source_id TEXT NOT NULL,
        content_version TEXT NOT NULL,
        evaluation TEXT NOT NULL,
        reason_code TEXT,
        reason_text TEXT,
        review_status TEXT NOT NULL DEFAULT 'recorded',
        status TEXT NOT NULL DEFAULT 'active',
        supersedes_id TEXT,
        participant_status TEXT NOT NULL DEFAULT 'visible',
        withdrawn_at TEXT,
        idempotency_key TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS feedback_ledger_actions (
        id TEXT PRIMARY KEY,
        entry_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        action TEXT NOT NULL,
        from_status TEXT NOT NULL,
        to_status TEXT NOT NULL,
        replacement_entry_id TEXT,
        idempotency_key TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS recommendation_snapshots (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        source_result_id TEXT,
        strategy_version TEXT NOT NULL,
        previous_strategy_version TEXT,
        recommended_card_ids_json TEXT NOT NULL DEFAULT '[]',
        reasons_json TEXT NOT NULL DEFAULT '[]',
        status TEXT NOT NULL DEFAULT 'active',
        idempotency_key TEXT NOT NULL,
        created_at TEXT NOT NULL
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
        handling_scope_json TEXT NOT NULL DEFAULT '[]',
        decision TEXT,
        processing_started_at TEXT,
        handled_at TEXT,
        participant_notice TEXT,
        policy_version TEXT,
        execution_proof_hash TEXT,
        version INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS privacy_request_actions (
        id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        actor_role TEXT NOT NULL,
        action TEXT NOT NULL,
        from_status TEXT NOT NULL,
        to_status TEXT NOT NULL,
        scope_json TEXT NOT NULL DEFAULT '[]',
        note TEXT,
        idempotency_key TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS privacy_request_approvals (
        id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        actor_role TEXT NOT NULL,
        scope_hash TEXT NOT NULL,
        policy_version TEXT NOT NULL,
        decision TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(request_id, actor_id, scope_hash, policy_version)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS privacy_request_executions (
        id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        environment TEXT NOT NULL,
        mode TEXT NOT NULL,
        policy_version TEXT NOT NULL,
        scope_hash TEXT NOT NULL,
        preview_json TEXT NOT NULL DEFAULT '{}',
        result_json TEXT NOT NULL DEFAULT '{}',
        proof_hash TEXT,
        status TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        started_at TEXT NOT NULL,
        completed_at TEXT,
        UNIQUE(actor_id, idempotency_key)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS privacy_deletion_tombstones (
        id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL UNIQUE,
        subject_hash TEXT NOT NULL,
        replacement_user_id TEXT NOT NULL,
        policy_version TEXT NOT NULL,
        scope_json TEXT NOT NULL DEFAULT '[]',
        proof_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS content_governance_versions (
        id TEXT PRIMARY KEY,
        content_type TEXT NOT NULL,
        item_id TEXT NOT NULL,
        version TEXT NOT NULL,
        parent_version_id TEXT,
        payload_json TEXT NOT NULL,
        payload_hash TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        status TEXT NOT NULL DEFAULT 'draft',
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        submitted_at TEXT,
        published_at TEXT,
        retired_at TEXT,
        UNIQUE(content_type, item_id, version)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS content_governance_reviews (
        id TEXT PRIMARY KEY,
        version_id TEXT NOT NULL,
        discipline TEXT NOT NULL,
        decision TEXT NOT NULL,
        reviewer_id TEXT NOT NULL,
        reviewer_role TEXT NOT NULL,
        evidence_path TEXT NOT NULL,
        note TEXT,
        created_at TEXT NOT NULL,
        UNIQUE(version_id, discipline, reviewer_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS content_governance_releases (
        id TEXT PRIMARY KEY,
        version_id TEXT NOT NULL,
        content_type TEXT NOT NULL,
        item_id TEXT NOT NULL,
        payload_hash TEXT NOT NULL,
        package_json TEXT NOT NULL,
        previous_release_id TEXT,
        release_reason TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        released_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_qa_sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        mode TEXT NOT NULL DEFAULT 'research_sandbox',
        status TEXT NOT NULL DEFAULT 'active',
        synthetic_data INTEGER NOT NULL DEFAULT 1,
        context_policy TEXT NOT NULL DEFAULT 'current_session_only',
        research_use_allowed INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        deleted_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_qa_messages (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        citations_json TEXT NOT NULL DEFAULT '[]',
        model_json TEXT NOT NULL DEFAULT '{}',
        safety_json TEXT NOT NULL DEFAULT '{}',
        prompt_version TEXT NOT NULL,
        knowledge_version TEXT NOT NULL,
        token_estimate INTEGER NOT NULL DEFAULT 0,
        cost_micros INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_qa_feedback (
        id TEXT PRIMARY KEY,
        message_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        evaluation TEXT NOT NULL,
        note TEXT,
        research_use_allowed INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        UNIQUE(message_id, user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_qa_safety_events (
        id TEXT PRIMARY KEY,
        session_id TEXT,
        user_id TEXT NOT NULL,
        request_hash TEXT NOT NULL,
        category TEXT NOT NULL,
        severity TEXT NOT NULL,
        outcome TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_qa_provider_events (
        id TEXT PRIMARY KEY,
        session_id TEXT,
        user_id TEXT NOT NULL,
        provider TEXT NOT NULL,
        model_version TEXT NOT NULL,
        status TEXT NOT NULL,
        latency_ms INTEGER NOT NULL DEFAULT 0,
        token_estimate INTEGER NOT NULL DEFAULT 0,
        cost_micros INTEGER NOT NULL DEFAULT 0,
        error_code TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_qa_evaluation_runs (
        id TEXT PRIMARY KEY,
        suite_version TEXT NOT NULL,
        provider_version TEXT NOT NULL,
        knowledge_snapshot_hash TEXT NOT NULL,
        metrics_json TEXT NOT NULL,
        thresholds_json TEXT NOT NULL,
        result_json TEXT NOT NULL,
        status TEXT NOT NULL,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_qa_evaluation_reviews (
        id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        reviewer_id TEXT NOT NULL,
        decision TEXT NOT NULL,
        evidence_path TEXT NOT NULL,
        note TEXT,
        created_at TEXT NOT NULL,
        UNIQUE(run_id, reviewer_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_qa_runtime_control (
        id TEXT PRIMARY KEY,
        killed INTEGER NOT NULL DEFAULT 0,
        reason TEXT,
        changed_by TEXT,
        changed_at TEXT NOT NULL
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
        client_submission_id TEXT,
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
        client_submission_id TEXT,
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
        client_submission_id TEXT,
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
        scoring_version TEXT,
        raw_scale_json TEXT NOT NULL DEFAULT '{}',
        raw_scores_json TEXT NOT NULL DEFAULT '{}',
        transformed_scores_json TEXT NOT NULL DEFAULT '{}',
        transformation_version TEXT,
        total_score INTEGER,
        result_summary TEXT,
        profile_model_id TEXT,
        profile_cluster_id INTEGER,
        profile_pc1 REAL,
        profile_pc2 REAL,
        profile_confidence REAL,
        client_submission_id TEXT,
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
        client_submission_id TEXT,
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
        client_submission_id TEXT,
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
        delivery_id TEXT,
        delivery_version INTEGER,
        status TEXT NOT NULL DEFAULT 'unread',
        created_at TEXT NOT NULL,
        read_at TEXT,
        withdrawn_at TEXT
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
        retry_category TEXT,
        next_attempt_at TEXT,
        max_attempts INTEGER NOT NULL DEFAULT 3,
        dead_lettered_at TEXT,
        last_attempt_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_work_items (
        id TEXT PRIMARY KEY,
        queue_type TEXT NOT NULL,
        source_type TEXT NOT NULL,
        source_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        priority TEXT NOT NULL DEFAULT 'routine',
        status TEXT NOT NULL DEFAULT 'open',
        assignee_id TEXT,
        lease_expires_at TEXT,
        due_at TEXT,
        version INTEGER NOT NULL DEFAULT 0,
        resolution_code TEXT,
        closed_at TEXT,
        last_action_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(queue_type, source_type, source_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_work_item_notes (
        id TEXT PRIMARY KEY,
        work_item_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        actor_role TEXT NOT NULL,
        note_type TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_work_item_actions (
        id TEXT PRIMARY KEY,
        work_item_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        actor_role TEXT NOT NULL,
        action TEXT NOT NULL,
        from_status TEXT NOT NULL,
        to_status TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        idempotency_key TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS data_claims (
        id TEXT PRIMARY KEY,
        anonymous_id TEXT NOT NULL,
        target_user_id TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'available',
        counts_json TEXT NOT NULL DEFAULT '{}',
        idempotency_key TEXT,
        version INTEGER NOT NULL DEFAULT 0,
        claimed_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS identity_merge_workflows (
        id TEXT PRIMARY KEY,
        source_user_id TEXT NOT NULL,
        target_user_id TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'candidate',
        reason_code TEXT NOT NULL,
        requested_by TEXT NOT NULL,
        confirmed_by TEXT,
        idempotency_key TEXT NOT NULL,
        execution_idempotency_key TEXT,
        rollback_idempotency_key TEXT,
        counts_json TEXT NOT NULL DEFAULT '{}',
        verification_json TEXT NOT NULL DEFAULT '{}',
        version INTEGER NOT NULL DEFAULT 0,
        rollback_until TEXT,
        confirmed_at TEXT,
        executed_at TEXT,
        verified_at TEXT,
        rolled_back_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS identity_merge_record_links (
        id TEXT PRIMARY KEY,
        workflow_id TEXT NOT NULL,
        table_name TEXT NOT NULL,
        record_id TEXT NOT NULL,
        column_name TEXT NOT NULL,
        source_user_id TEXT NOT NULL,
        target_user_id TEXT NOT NULL,
        source_value TEXT,
        target_value TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS offline_dataset_cards (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        source_url TEXT NOT NULL,
        source_version TEXT NOT NULL,
        language TEXT NOT NULL,
        platform TEXT NOT NULL,
        population TEXT NOT NULL,
        context TEXT NOT NULL,
        license TEXT NOT NULL,
        content_rights_status TEXT NOT NULL,
        sensitivity TEXT NOT NULL,
        allowed_uses_json TEXT NOT NULL DEFAULT '[]',
        prohibited_uses_json TEXT NOT NULL DEFAULT '[]',
        artifact_sha256 TEXT,
        local_path TEXT,
        ingest_status TEXT NOT NULL,
        deletion_method TEXT NOT NULL,
        review_note TEXT,
        registry_version TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS offline_benchmark_runs (
        id TEXT PRIMARY KEY,
        benchmark_type TEXT NOT NULL,
        dataset_card_id TEXT NOT NULL,
        evidence_level TEXT NOT NULL,
        algorithm_version TEXT NOT NULL,
        parameters_json TEXT NOT NULL DEFAULT '{}',
        metrics_json TEXT NOT NULL DEFAULT '{}',
        artifact_hash TEXT NOT NULL,
        raw_text_included INTEGER NOT NULL DEFAULT 0,
        production_replacement_allowed INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS offline_benchmark_annotations (
        id TEXT PRIMARY KEY,
        dataset_card_id TEXT NOT NULL,
        case_id TEXT NOT NULL,
        annotator_id TEXT NOT NULL,
        blind_round TEXT NOT NULL DEFAULT 'round_1',
        emotion_label TEXT NOT NULL,
        valence REAL NOT NULL,
        arousal REAL NOT NULL,
        context_label TEXT NOT NULL,
        reflex_node TEXT NOT NULL,
        uncertain INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(dataset_card_id, case_id, annotator_id, blind_round)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS offline_benchmark_reviews (
        id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        reviewer_id TEXT NOT NULL,
        decision TEXT NOT NULL,
        evidence_path TEXT NOT NULL,
        notes TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS offline_benchmark_runtime_control (
        id TEXT PRIMARY KEY,
        disabled INTEGER NOT NULL DEFAULT 0,
        reason TEXT,
        changed_by TEXT,
        changed_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_methodology_versions (
        id TEXT PRIMARY KEY,
        version TEXT NOT NULL UNIQUE,
        status TEXT NOT NULL,
        registry_json TEXT NOT NULL,
        registry_hash TEXT NOT NULL,
        formal_freeze_allowed INTEGER NOT NULL DEFAULT 0,
        real_outcome_data_accessed INTEGER NOT NULL DEFAULT 0,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_methodology_checks (
        id TEXT PRIMARY KEY,
        version_id TEXT NOT NULL,
        check_type TEXT NOT NULL,
        status TEXT NOT NULL,
        results_json TEXT NOT NULL DEFAULT '{}',
        artifact_hash TEXT NOT NULL,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_methodology_simulation_runs (
        id TEXT PRIMARY KEY,
        version_id TEXT NOT NULL,
        simulation_version TEXT NOT NULL,
        parameters_json TEXT NOT NULL DEFAULT '{}',
        metrics_json TEXT NOT NULL DEFAULT '{}',
        artifact_hash TEXT NOT NULL,
        contains_real_data INTEGER NOT NULL DEFAULT 0,
        confirmatory_power_claim INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_methodology_evidence_packages (
        id TEXT PRIMARY KEY,
        version_id TEXT NOT NULL,
        package_json TEXT NOT NULL DEFAULT '{}',
        artifact_hash TEXT NOT NULL,
        status TEXT NOT NULL,
        formal_freeze_recorded INTEGER NOT NULL DEFAULT 0,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_methodology_runtime_control (
        id TEXT PRIMARY KEY,
        disabled INTEGER NOT NULL DEFAULT 0,
        reason TEXT,
        changed_by TEXT,
        changed_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS security_control_runs (
        id TEXT PRIMARY KEY,
        actor_id TEXT NOT NULL,
        registry_version TEXT NOT NULL,
        registry_hash TEXT NOT NULL,
        mode TEXT NOT NULL,
        status TEXT NOT NULL,
        summary_json TEXT NOT NULL DEFAULT '{}',
        artifact_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS security_events (
        id TEXT PRIMARY KEY,
        actor_id TEXT,
        event_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        target_type TEXT,
        target_id TEXT,
        request_id TEXT,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        status TEXT NOT NULL DEFAULT 'open',
        resolved_by TEXT,
        resolved_at TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS privacy_deletion_verifications (
        id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL,
        execution_id TEXT NOT NULL,
        subject_hash TEXT NOT NULL,
        scope_hash TEXT NOT NULL,
        verification_json TEXT NOT NULL DEFAULT '{}',
        status TEXT NOT NULL,
        verified_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS observability_events (
        id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL,
        method TEXT NOT NULL,
        path TEXT NOT NULL,
        actor_scope TEXT NOT NULL,
        module TEXT NOT NULL,
        journey TEXT NOT NULL,
        outcome TEXT NOT NULL,
        error_code TEXT,
        status_code INTEGER NOT NULL,
        latency_ms REAL NOT NULL,
        retry_count INTEGER NOT NULL DEFAULT 0,
        recovered INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reliable_jobs (
        id TEXT PRIMARY KEY,
        job_type TEXT NOT NULL,
        source_type TEXT NOT NULL,
        source_id TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        attempt_count INTEGER NOT NULL DEFAULT 0,
        max_attempts INTEGER NOT NULL DEFAULT 3,
        available_at TEXT NOT NULL,
        lease_owner TEXT,
        lease_expires_at TEXT,
        last_error_code TEXT,
        payload_hash TEXT NOT NULL,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        completed_at TEXT,
        dead_lettered_at TEXT,
        UNIQUE(job_type, idempotency_key)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reliable_job_actions (
        id TEXT PRIMARY KEY,
        job_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        action TEXT NOT NULL,
        from_status TEXT NOT NULL,
        to_status TEXT NOT NULL,
        error_code TEXT,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_analysis_snapshots (
        id TEXT PRIMARY KEY,
        participant_user_id TEXT NOT NULL,
        enrollment_id TEXT,
        purpose_code TEXT NOT NULL,
        consent_type TEXT NOT NULL,
        consent_version TEXT NOT NULL,
        authorization_status TEXT NOT NULL DEFAULT 'active',
        source_count INTEGER NOT NULL DEFAULT 0,
        snapshot_hash TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        suspended_at TEXT,
        deleted_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_analysis_snapshot_links (
        id TEXT PRIMARY KEY,
        snapshot_id TEXT NOT NULL,
        source_type TEXT NOT NULL,
        source_id TEXT NOT NULL,
        source_version TEXT,
        source_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(snapshot_id, source_type, source_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_analysis_jobs (
        id TEXT PRIMARY KEY,
        snapshot_id TEXT NOT NULL,
        analysis_type TEXT NOT NULL,
        analysis_version TEXT NOT NULL,
        resource_hash TEXT NOT NULL,
        parameters_json TEXT NOT NULL DEFAULT '{}',
        idempotency_key TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'queued',
        attempt_count INTEGER NOT NULL DEFAULT 0,
        max_attempts INTEGER NOT NULL DEFAULT 3,
        available_at TEXT NOT NULL,
        lease_owner TEXT,
        lease_expires_at TEXT,
        last_error_code TEXT,
        result_artifact_id TEXT,
        shadow_mode INTEGER NOT NULL DEFAULT 1,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        completed_at TEXT,
        canceled_at TEXT,
        expired_at TEXT,
        suspended_at TEXT,
        dead_lettered_at TEXT,
        UNIQUE(created_by, idempotency_key)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_analysis_artifacts (
        id TEXT PRIMARY KEY,
        job_id TEXT NOT NULL UNIQUE,
        snapshot_id TEXT NOT NULL,
        analysis_type TEXT NOT NULL,
        analysis_version TEXT NOT NULL,
        metrics_json TEXT NOT NULL DEFAULT '{}',
        artifact_hash TEXT NOT NULL,
        quality_status TEXT NOT NULL,
        boundary_notice TEXT NOT NULL,
        visibility TEXT NOT NULL DEFAULT 'researcher_only',
        status TEXT NOT NULL DEFAULT 'active',
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        suspended_at TEXT,
        deleted_at TEXT,
        deletion_reason_code TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_analysis_events (
        id TEXT PRIMARY KEY,
        job_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        action TEXT NOT NULL,
        from_status TEXT NOT NULL,
        to_status TEXT NOT NULL,
        error_code TEXT,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS feature_flag_versions (
        id TEXT PRIMARY KEY,
        flag_name TEXT NOT NULL,
        version INTEGER NOT NULL,
        enabled INTEGER NOT NULL,
        role_scope_json TEXT NOT NULL DEFAULT '[]',
        rollout_percent INTEGER NOT NULL DEFAULT 100,
        reason_code TEXT NOT NULL,
        previous_version INTEGER,
        changed_by TEXT NOT NULL,
        changed_at TEXT NOT NULL,
        UNIQUE(flag_name, version)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reliability_slo_snapshots (
        id TEXT PRIMARY KEY,
        environment TEXT NOT NULL,
        window_minutes INTEGER NOT NULL,
        metrics_json TEXT NOT NULL DEFAULT '{}',
        status TEXT NOT NULL,
        contains_real_participant_text INTEGER NOT NULL DEFAULT 0,
        production_slo_frozen INTEGER NOT NULL DEFAULT 0,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reliability_drill_runs (
        id TEXT PRIMARY KEY,
        scenario TEXT NOT NULL,
        status TEXT NOT NULL,
        result_json TEXT NOT NULL DEFAULT '{}',
        artifact_hash TEXT NOT NULL,
        contains_real_participant_data INTEGER NOT NULL DEFAULT 0,
        production_approval_inferred INTEGER NOT NULL DEFAULT 0,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reliability_evidence_packages (
        id TEXT PRIMARY KEY,
        status TEXT NOT NULL,
        package_json TEXT NOT NULL DEFAULT '{}',
        artifact_hash TEXT NOT NULL,
        production_release_approved INTEGER NOT NULL DEFAULT 0,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ux_audit_runs (
        id TEXT PRIMARY KEY,
        environment TEXT NOT NULL,
        platform TEXT NOT NULL,
        viewport TEXT NOT NULL,
        registry_version TEXT NOT NULL,
        results_json TEXT NOT NULL DEFAULT '{}',
        artifact_hash TEXT NOT NULL,
        status TEXT NOT NULL,
        contains_participant_text INTEGER NOT NULL DEFAULT 0,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ux_evidence_packages (
        id TEXT PRIMARY KEY,
        status TEXT NOT NULL,
        package_json TEXT NOT NULL DEFAULT '{}',
        artifact_hash TEXT NOT NULL,
        human_research_approved INTEGER NOT NULL DEFAULT 0,
        device_acceptance_approved INTEGER NOT NULL DEFAULT 0,
        release_approved INTEGER NOT NULL DEFAULT 0,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS operations_release_packages (
        id TEXT PRIMARY KEY,
        package_version TEXT NOT NULL UNIQUE,
        previous_package_id TEXT,
        risk_level TEXT NOT NULL,
        target_environment TEXT NOT NULL,
        capability_ids_json TEXT NOT NULL DEFAULT '[]',
        manifest_json TEXT NOT NULL,
        manifest_hash TEXT NOT NULL,
        artifact_count INTEGER NOT NULL,
        status TEXT NOT NULL,
        proposed_by TEXT NOT NULL,
        submitted_at TEXT,
        released_by TEXT,
        released_at TEXT,
        paused_by TEXT,
        paused_at TEXT,
        pause_reason_code TEXT,
        retired_by TEXT,
        retired_at TEXT,
        production_release_approved INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS operations_package_reviews (
        id TEXT PRIMARY KEY,
        package_id TEXT NOT NULL,
        stage TEXT NOT NULL,
        domain TEXT NOT NULL,
        decision TEXT NOT NULL,
        reviewer_id TEXT NOT NULL,
        reviewer_role TEXT NOT NULL,
        evidence_ref TEXT NOT NULL,
        note TEXT,
        created_at TEXT NOT NULL,
        UNIQUE(package_id, stage, domain, reviewer_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS operations_replay_runs (
        id TEXT PRIMARY KEY,
        package_id TEXT NOT NULL,
        suite_version TEXT NOT NULL,
        results_json TEXT NOT NULL DEFAULT '[]',
        metrics_json TEXT NOT NULL DEFAULT '{}',
        snapshot_hash TEXT NOT NULL,
        status TEXT NOT NULL,
        high_severity_regressions INTEGER NOT NULL DEFAULT 0,
        wording_diff_count INTEGER NOT NULL DEFAULT 0,
        contains_real_data INTEGER NOT NULL DEFAULT 0,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS operations_runtime_controls (
        capability_id TEXT PRIMARY KEY,
        active_package_id TEXT,
        previous_package_id TEXT,
        state TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1,
        reason_code TEXT NOT NULL,
        changed_by TEXT NOT NULL,
        changed_at TEXT NOT NULL,
        production_release_approved INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS operations_monitor_snapshots (
        id TEXT PRIMARY KEY,
        environment TEXT NOT NULL,
        window_days INTEGER NOT NULL,
        metrics_json TEXT NOT NULL DEFAULT '{}',
        thresholds_json TEXT NOT NULL DEFAULT '{}',
        drift_signals_json TEXT NOT NULL DEFAULT '[]',
        review_required INTEGER NOT NULL DEFAULT 0,
        automatic_participant_or_family_judgment INTEGER NOT NULL DEFAULT 0,
        contains_participant_text INTEGER NOT NULL DEFAULT 0,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS operations_incidents (
        id TEXT PRIMARY KEY,
        capability_id TEXT NOT NULL,
        package_id TEXT,
        incident_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        status TEXT NOT NULL,
        summary_code TEXT NOT NULL,
        evidence_refs_json TEXT NOT NULL DEFAULT '[]',
        evidence_hold_hash TEXT NOT NULL,
        capability_disabled INTEGER NOT NULL DEFAULT 1,
        notification_required INTEGER NOT NULL DEFAULT 1,
        postmortem_json TEXT NOT NULL DEFAULT '{}',
        reported_by TEXT NOT NULL,
        reported_at TEXT NOT NULL,
        postmortem_by TEXT,
        postmortem_at TEXT,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS operations_incident_notifications (
        id TEXT PRIMARY KEY,
        incident_id TEXT NOT NULL,
        recipient_role TEXT NOT NULL,
        status TEXT NOT NULL,
        attempt_count INTEGER NOT NULL DEFAULT 0,
        idempotency_key TEXT NOT NULL UNIQUE,
        last_error_code TEXT,
        next_attempt_at TEXT,
        dispatched_by TEXT,
        dispatched_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS operations_evidence_packages (
        id TEXT PRIMARY KEY,
        status TEXT NOT NULL,
        package_json TEXT NOT NULL DEFAULT '{}',
        artifact_hash TEXT NOT NULL,
        human_approved INTEGER NOT NULL DEFAULT 0,
        ethics_approved INTEGER NOT NULL DEFAULT 0,
        cloud_approved INTEGER NOT NULL DEFAULT 0,
        device_approved INTEGER NOT NULL DEFAULT 0,
        production_release_approved INTEGER NOT NULL DEFAULT 0,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS therapeutic_assessment_cases (
        id TEXT PRIMARY KEY,
        participant_user_id TEXT NOT NULL,
        enrollment_id TEXT,
        assessment_question TEXT NOT NULL,
        working_question TEXT,
        question_candidates_json TEXT NOT NULL DEFAULT '[]',
        question_quality_json TEXT NOT NULL DEFAULT '{}',
        best_guess TEXT,
        question_status TEXT NOT NULL DEFAULT 'submitted',
        candidate_decision TEXT NOT NULL DEFAULT 'unreviewed',
        question_version INTEGER NOT NULL DEFAULT 1,
        shared_scope_json TEXT NOT NULL DEFAULT '[]',
        consent_status TEXT NOT NULL,
        status TEXT NOT NULL,
        workflow_state TEXT NOT NULL DEFAULT 'draft_local',
        hypothesis_state TEXT NOT NULL DEFAULT 'observations_only',
        safety_state TEXT NOT NULL DEFAULT 'not_assessed',
        risk_level TEXT NOT NULL,
        complexity_scope TEXT NOT NULL DEFAULT 'individual_adult_low_risk',
        readiness_level TEXT NOT NULL DEFAULT 'L0',
        assigned_researcher_id TEXT,
        qualification_evidence_ref TEXT,
        supervision_evidence_ref TEXT,
        ethics_evidence_ref TEXT,
        version INTEGER NOT NULL DEFAULT 1,
        disagreement_note TEXT,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        withdrawn_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS therapeutic_assessment_feedback_versions (
        id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        version_no INTEGER NOT NULL,
        author_id TEXT NOT NULL,
        source TEXT NOT NULL,
        status TEXT NOT NULL,
        observations_json TEXT NOT NULL DEFAULT '[]',
        evidence_json TEXT NOT NULL DEFAULT '[]',
        alternatives_json TEXT NOT NULL DEFAULT '[]',
        uncertainty TEXT NOT NULL,
        next_step TEXT NOT NULL,
        human_discussion_json TEXT NOT NULL DEFAULT '[]',
        participant_content TEXT NOT NULL,
        reviewed_by TEXT,
        reviewed_at TEXT,
        sent_at TEXT,
        created_at TEXT NOT NULL,
        UNIQUE(case_id, version_no)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS therapeutic_assessment_evidence_items (
        id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        kind TEXT NOT NULL,
        content TEXT NOT NULL,
        source_origin TEXT NOT NULL,
        source_ref TEXT,
        provider_id TEXT,
        observed_at TEXT,
        context TEXT,
        method_limitations TEXT NOT NULL DEFAULT '仅适用于当前已授权资料与时间范围，不代表完整解释或诊断结论。',
        visibility_scope_json TEXT NOT NULL DEFAULT '[]',
        applicability_scope TEXT,
        question_link TEXT,
        exceptions_json TEXT NOT NULL DEFAULT '[]',
        time_window TEXT,
        supporting_evidence_json TEXT NOT NULL DEFAULT '[]',
        counter_evidence_json TEXT NOT NULL DEFAULT '[]',
        alternative_explanations_json TEXT NOT NULL DEFAULT '[]',
        falsification_criteria_json TEXT NOT NULL DEFAULT '[]',
        protective_function TEXT,
        cost TEXT,
        participant_recognition TEXT,
        uncertainty_type TEXT,
        author_id TEXT NOT NULL,
        review_status TEXT NOT NULL,
        reviewed_by TEXT,
        reviewed_at TEXT,
        version INTEGER NOT NULL DEFAULT 1,
        idempotency_key TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS therapeutic_assessment_data_items (
        id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        subject_user_id TEXT NOT NULL,
        provider_user_id TEXT NOT NULL,
        involved_user_ids_json TEXT NOT NULL DEFAULT '[]',
        controller_user_id TEXT NOT NULL,
        visibility TEXT NOT NULL,
        allowed_viewer_ids_json TEXT NOT NULL DEFAULT '[]',
        purpose TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        status TEXT NOT NULL,
        consent_version INTEGER NOT NULL DEFAULT 1,
        content_ref TEXT NOT NULL,
        content_sha256 TEXT NOT NULL,
        legal_hold_reason TEXT,
        withdrawn_at TEXT,
        version INTEGER NOT NULL DEFAULT 1,
        idempotency_key TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS therapeutic_assessment_data_consents (
        id TEXT PRIMARY KEY,
        data_item_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        action TEXT NOT NULL,
        visibility TEXT NOT NULL,
        allowed_viewer_ids_json TEXT NOT NULL DEFAULT '[]',
        purpose TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        consent_version INTEGER NOT NULL,
        idempotency_key TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS therapeutic_assessment_participant_drafts (
        id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        participant_user_id TEXT NOT NULL,
        step_id TEXT NOT NULL,
        payload_json TEXT NOT NULL DEFAULT '{}',
        client_updated_at TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        version INTEGER NOT NULL DEFAULT 1,
        idempotency_key TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(case_id, participant_user_id, step_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS therapeutic_assessment_participant_draft_events (
        id TEXT PRIMARY KEY,
        draft_id TEXT NOT NULL,
        participant_user_id TEXT NOT NULL,
        action TEXT NOT NULL,
        result_version INTEGER NOT NULL,
        idempotency_key TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(participant_user_id, idempotency_key)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS therapeutic_assessment_responsibility_chains (
        id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL UNIQUE,
        responsible_user_id TEXT NOT NULL,
        supervisor_user_id TEXT NOT NULL,
        support_channel TEXT NOT NULL,
        evidence_ref TEXT NOT NULL,
        status TEXT NOT NULL,
        queue_timeout_minutes INTEGER NOT NULL DEFAULT 30,
        version INTEGER NOT NULL DEFAULT 1,
        idempotency_key TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS therapeutic_assessment_safety_events (
        id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        signal_type TEXT NOT NULL,
        state TEXT NOT NULL,
        source_ref TEXT NOT NULL,
        reason_summary TEXT,
        detected_by TEXT NOT NULL,
        resolution_evidence_ref TEXT,
        resolved_by TEXT,
        resolved_at TEXT,
        idempotency_key TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(detected_by, idempotency_key)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS therapeutic_assessment_runtime_control (
        id TEXT PRIMARY KEY,
        killed INTEGER NOT NULL DEFAULT 0,
        reason TEXT,
        changed_by TEXT,
        changed_at TEXT NOT NULL,
        restoration_evidence_ref TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS therapeutic_assessment_researcher_workbench_drafts (
        id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        researcher_user_id TEXT NOT NULL,
        internal_notes TEXT NOT NULL DEFAULT '',
        participant_visible_draft TEXT NOT NULL DEFAULT '',
        filters_json TEXT NOT NULL DEFAULT '{}',
        selected_evidence_id TEXT,
        version INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(case_id, researcher_user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS therapeutic_assessment_researcher_workbench_draft_events (
        id TEXT PRIMARY KEY,
        draft_id TEXT NOT NULL,
        researcher_user_id TEXT NOT NULL,
        result_version INTEGER NOT NULL,
        idempotency_key TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(researcher_user_id, idempotency_key)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS therapeutic_assessment_actions (
        id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        participant_user_id TEXT NOT NULL,
        feedback_version_id TEXT,
        action_text TEXT NOT NULL,
        status TEXT NOT NULL,
        followup_note TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS therapeutic_assessment_events (
        id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        action TEXT NOT NULL,
        before_version INTEGER,
        after_version INTEGER,
        idempotency_key TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        UNIQUE(actor_id, idempotency_key)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS computation_datasets (
        id TEXT PRIMARY KEY,
        dataset_key TEXT NOT NULL,
        version TEXT NOT NULL,
        data_class TEXT NOT NULL,
        storage_layer TEXT NOT NULL,
        source_kind TEXT NOT NULL,
        rights_status TEXT NOT NULL,
        purpose TEXT NOT NULL,
        retention_until TEXT,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        UNIQUE(dataset_key, version)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS computation_authorization_snapshots (
        id TEXT PRIMARY KEY,
        dataset_id TEXT NOT NULL,
        subject_hash TEXT NOT NULL,
        consent_type TEXT NOT NULL,
        consent_version TEXT NOT NULL,
        status TEXT NOT NULL,
        captured_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS computation_lineage_edges (
        id TEXT PRIMARY KEY,
        parent_resource_type TEXT NOT NULL,
        parent_resource_id TEXT NOT NULL,
        child_resource_type TEXT NOT NULL,
        child_resource_id TEXT NOT NULL,
        transform_version TEXT NOT NULL,
        purpose TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(parent_resource_type, parent_resource_id, child_resource_type, child_resource_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS computation_deletion_tombstones (
        id TEXT PRIMARY KEY,
        subject_hash TEXT NOT NULL,
        root_resource_type TEXT NOT NULL,
        root_resource_id TEXT NOT NULL,
        reason_code TEXT NOT NULL,
        affected_resources_json TEXT NOT NULL DEFAULT '[]',
        blocked_by_legal_hold INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS computation_legal_holds (
        id TEXT PRIMARY KEY,
        scope_type TEXT NOT NULL,
        scope_id TEXT NOT NULL,
        reason_code TEXT NOT NULL,
        expires_at TEXT,
        released_at TEXT,
        created_at TEXT NOT NULL
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
    "CREATE INDEX IF NOT EXISTS idx_privacy_requests_status_updated ON privacy_requests(status, updated_at)",
    "CREATE INDEX IF NOT EXISTS idx_privacy_request_actions_request_created ON privacy_request_actions(request_id, created_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_privacy_request_actions_actor_idempotency ON privacy_request_actions(actor_id, idempotency_key)",
    "CREATE INDEX IF NOT EXISTS idx_privacy_request_approvals_request_created ON privacy_request_approvals(request_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_privacy_request_executions_request_started ON privacy_request_executions(request_id, started_at)",
    "CREATE INDEX IF NOT EXISTS idx_privacy_tombstones_subject_hash ON privacy_deletion_tombstones(subject_hash)",
    "CREATE INDEX IF NOT EXISTS idx_family_links_code_status ON family_links(bind_code, status)",
    "CREATE INDEX IF NOT EXISTS idx_assessment_worksheets_audience_enabled ON assessment_worksheets(audience_class, enabled_for_user)",
    "CREATE INDEX IF NOT EXISTS idx_messages_user_status_created ON messages(user_id, status, created_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_sender_idempotency ON messages(sender_id, idempotency_key)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_notification_preference_unique ON notification_preferences(user_id, notification_type, template_id)",
    "CREATE INDEX IF NOT EXISTS idx_notification_preference_status ON notification_preferences(consent_status, notification_type)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_notification_delivery_idempotency ON notification_deliveries(idempotency_key)",
    "CREATE INDEX IF NOT EXISTS idx_notification_delivery_user_created ON notification_deliveries(user_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_notification_delivery_retry_due ON notification_deliveries(status, retry_category, next_attempt_at)",
    "CREATE INDEX IF NOT EXISTS idx_research_work_items_queue_status_due ON research_work_items(queue_type, status, due_at)",
    "CREATE INDEX IF NOT EXISTS idx_research_work_items_assignee_lease ON research_work_items(assignee_id, lease_expires_at)",
    "CREATE INDEX IF NOT EXISTS idx_research_work_items_user_created ON research_work_items(user_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_research_work_item_notes_item_created ON research_work_item_notes(work_item_id, created_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_research_work_item_action_actor_idempotency ON research_work_item_actions(actor_id, idempotency_key)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_data_claim_anonymous_unique ON data_claims(anonymous_id)",
    "CREATE INDEX IF NOT EXISTS idx_data_claim_target_status ON data_claims(target_user_id, status, updated_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_identity_merge_request_idempotency ON identity_merge_workflows(requested_by, idempotency_key)",
    "CREATE INDEX IF NOT EXISTS idx_identity_merge_users_status ON identity_merge_workflows(source_user_id, target_user_id, status, updated_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_identity_merge_link_unique ON identity_merge_record_links(workflow_id, table_name, record_id, column_name)",
    "CREATE INDEX IF NOT EXISTS idx_identity_merge_link_workflow ON identity_merge_record_links(workflow_id, table_name)",
    "CREATE INDEX IF NOT EXISTS idx_relationship_hypothesis_report ON relationship_hypothesis_feedback(report_id, hypothesis_index)",
    "CREATE INDEX IF NOT EXISTS idx_feedback_ledger_user_created ON feedback_ledger(user_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_feedback_ledger_source ON feedback_ledger(source_type, source_id, content_version)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_feedback_ledger_user_idempotency ON feedback_ledger(user_id, idempotency_key)",
    "CREATE INDEX IF NOT EXISTS idx_feedback_actions_entry_created ON feedback_ledger_actions(entry_id, created_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_feedback_actions_user_idempotency ON feedback_ledger_actions(user_id, idempotency_key)",
    "CREATE INDEX IF NOT EXISTS idx_recommendation_snapshots_user_created ON recommendation_snapshots(user_id, created_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_recommendation_snapshots_user_idempotency ON recommendation_snapshots(user_id, idempotency_key)",
    "CREATE INDEX IF NOT EXISTS idx_content_versions_item_status ON content_governance_versions(content_type, item_id, status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_content_reviews_version_discipline ON content_governance_reviews(version_id, discipline, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_content_releases_item_status ON content_governance_releases(content_type, item_id, status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_ai_qa_sessions_user_status ON ai_qa_sessions(user_id, status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_ai_qa_messages_session_created ON ai_qa_messages(session_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_ai_qa_safety_created ON ai_qa_safety_events(category, severity, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_ai_qa_provider_created ON ai_qa_provider_events(provider, status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_ai_qa_evaluation_status_created ON ai_qa_evaluation_runs(status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_offline_dataset_ingest_status ON offline_dataset_cards(ingest_status, updated_at)",
    "CREATE INDEX IF NOT EXISTS idx_offline_benchmark_runs_type_created ON offline_benchmark_runs(benchmark_type, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_offline_benchmark_annotations_case ON offline_benchmark_annotations(dataset_card_id, case_id, blind_round)",
    "CREATE INDEX IF NOT EXISTS idx_offline_benchmark_reviews_run ON offline_benchmark_reviews(run_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_methodology_checks_version_created ON research_methodology_checks(version_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_methodology_simulations_version_created ON research_methodology_simulation_runs(version_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_methodology_evidence_version_created ON research_methodology_evidence_packages(version_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_security_runs_created ON security_control_runs(status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_security_events_status_created ON security_events(status, severity, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_privacy_verifications_request ON privacy_deletion_verifications(request_id, verified_at)",
    "CREATE INDEX IF NOT EXISTS idx_observability_journey_created ON observability_events(journey, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_observability_request ON observability_events(request_id, created_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_reliable_jobs_idempotency ON reliable_jobs(job_type, idempotency_key)",
    "CREATE INDEX IF NOT EXISTS idx_reliable_jobs_due ON reliable_jobs(status, available_at, lease_expires_at)",
    "CREATE INDEX IF NOT EXISTS idx_reliable_job_actions_job ON reliable_job_actions(job_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_research_analysis_snapshot_participant_status ON research_analysis_snapshots(participant_user_id, authorization_status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_research_analysis_snapshot_link_snapshot ON research_analysis_snapshot_links(snapshot_id, source_type)",
    "CREATE INDEX IF NOT EXISTS idx_research_analysis_job_queue ON research_analysis_jobs(status, available_at, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_research_analysis_job_snapshot ON research_analysis_jobs(snapshot_id, analysis_type, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_research_analysis_artifact_snapshot ON research_analysis_artifacts(snapshot_id, status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_research_analysis_event_job ON research_analysis_events(job_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_feature_flag_versions_name ON feature_flag_versions(flag_name, version)",
    "CREATE INDEX IF NOT EXISTS idx_reliability_slo_created ON reliability_slo_snapshots(environment, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_reliability_drills_created ON reliability_drill_runs(scenario, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_ux_audit_runs_created ON ux_audit_runs(platform, status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_ux_evidence_created ON ux_evidence_packages(status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_operations_packages_status_created ON operations_release_packages(status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_operations_reviews_package_stage ON operations_package_reviews(package_id, stage, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_operations_replays_package_created ON operations_replay_runs(package_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_operations_monitor_created ON operations_monitor_snapshots(environment, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_operations_incidents_status_created ON operations_incidents(status, severity, reported_at)",
    "CREATE INDEX IF NOT EXISTS idx_operations_notifications_due ON operations_incident_notifications(status, next_attempt_at)",
    "CREATE INDEX IF NOT EXISTS idx_operations_evidence_created ON operations_evidence_packages(status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_therapeutic_cases_participant_status ON therapeutic_assessment_cases(participant_user_id, status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_therapeutic_cases_assignee_status ON therapeutic_assessment_cases(assigned_researcher_id, status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_therapeutic_feedback_case_version ON therapeutic_assessment_feedback_versions(case_id, version_no)",
    "CREATE INDEX IF NOT EXISTS idx_therapeutic_evidence_case_kind ON therapeutic_assessment_evidence_items(case_id, kind, created_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_therapeutic_evidence_actor_idempotency ON therapeutic_assessment_evidence_items(author_id, idempotency_key)",
    "CREATE INDEX IF NOT EXISTS idx_therapeutic_data_case_status ON therapeutic_assessment_data_items(case_id, status, created_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_therapeutic_data_provider_idempotency ON therapeutic_assessment_data_items(provider_user_id, idempotency_key)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_therapeutic_consent_actor_idempotency ON therapeutic_assessment_data_consents(actor_id, idempotency_key)",
    "CREATE INDEX IF NOT EXISTS idx_therapeutic_drafts_participant_updated ON therapeutic_assessment_participant_drafts(participant_user_id, updated_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_therapeutic_drafts_actor_idempotency ON therapeutic_assessment_participant_drafts(participant_user_id, idempotency_key)",
    "CREATE INDEX IF NOT EXISTS idx_therapeutic_draft_events_draft_created ON therapeutic_assessment_participant_draft_events(draft_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_therapeutic_safety_case_state ON therapeutic_assessment_safety_events(case_id, state, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_therapeutic_actions_case_created ON therapeutic_assessment_actions(case_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_therapeutic_events_case_created ON therapeutic_assessment_events(case_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_computation_auth_dataset_subject ON computation_authorization_snapshots(dataset_id, subject_hash)",
    "CREATE INDEX IF NOT EXISTS idx_computation_lineage_parent ON computation_lineage_edges(parent_resource_type, parent_resource_id)",
    "CREATE INDEX IF NOT EXISTS idx_computation_lineage_child ON computation_lineage_edges(child_resource_type, child_resource_id)",
    "CREATE INDEX IF NOT EXISTS idx_computation_tombstone_subject ON computation_deletion_tombstones(subject_hash)",
    "CREATE INDEX IF NOT EXISTS idx_computation_holds_scope ON computation_legal_holds(scope_type, scope_id, released_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_goals_client_submission ON goals(user_id, client_submission_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_diaries_client_submission ON emotion_diaries(user_id, client_submission_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_supervision_client_submission ON supervision_requests(user_id, client_submission_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_checkins_client_submission ON checkins(user_id, client_submission_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_assessment_results_client_submission ON assessment_results(user_id, client_submission_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_parent_assessments_client_submission ON parent_assessment_submissions(user_id, client_submission_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_relationship_enrollment_assessment_unique ON relationship_pilot_enrollments(assessment_result_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_relationship_report_version_unique ON relationship_screening_reports(enrollment_id, version)",
    "CREATE INDEX IF NOT EXISTS idx_relationship_enrollment_assigned ON relationship_pilot_enrollments(assigned_researcher_id)",
    "CREATE INDEX IF NOT EXISTS idx_research_scope_actor_status ON research_scope_assignments(actor_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_research_scope_enrollment_status ON research_scope_assignments(enrollment_id, status)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_research_scope_assigner_idempotency ON research_scope_assignments(assigned_by, idempotency_key)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_research_scope_action_actor_idempotency ON research_scope_assignment_actions(actor_id, idempotency_key)",
    "CREATE INDEX IF NOT EXISTS idx_research_delivery_enrollment_status ON research_delivery_workflows(enrollment_id, status, updated_at)",
    "CREATE INDEX IF NOT EXISTS idx_research_delivery_user_status ON research_delivery_workflows(user_id, status, updated_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_research_delivery_create_idempotency ON research_delivery_workflows(actor_id, create_idempotency_key)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_research_delivery_version_unique ON research_delivery_versions(workflow_id, version_no)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_research_delivery_event_idempotency ON research_delivery_events(actor_id, idempotency_key)",
    "CREATE INDEX IF NOT EXISTS idx_messages_delivery ON messages(delivery_id, delivery_version)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_relationship_task_idempotency_unique ON relationship_pilot_tasks(user_id, idempotency_key)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_relationship_longitudinal_idempotency_unique ON relationship_longitudinal_entries(user_id, idempotency_key)",
]

IDENTITY_UNIQUE_INDEX_SQL = [
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_unique ON users(username)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_wechat_openid_unique ON users(wechat_openid)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone_hash_unique ON users(phone_hash)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_credential_receipt_unique ON users(credential_receipt_id)",
]
