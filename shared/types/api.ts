export type ID = string;
export type ISODateTime = string;
export type ISODate = string;

export type UserRole = "parent" | "student" | "admin" | "researcher" | "supervisor";
export type GoalStatus = "active" | "done" | "paused";
export type RiskLevel = "low" | "medium" | "high";
export type SupervisionStatus = "pending" | "replied" | "closed";
export type ProfileReviewStatus = "pending" | "in_progress" | "reviewed" | "escalated" | "closed";

export interface ApiSuccess<T> {
  ok: true;
  data: T;
  request_id: ID;
}

export interface ApiError {
  ok: false;
  error: {
    code: string;
    message: string;
  };
  request_id: ID;
}

export type ApiResponse<T> = ApiSuccess<T> | ApiError;

export interface DataClaimModuleCount {
  module: string;
  label: string;
  count: number;
}

export interface DataClaimPreview {
  available: boolean;
  claim_id: string | null;
  total_records: number;
  modules: DataClaimModuleCount[];
  boundary_notice: string;
}

export interface DataClaimResult {
  claim_id: string;
  status: "claimed";
  total_records: number;
  modules: DataClaimModuleCount[];
  claimed_at?: string | null;
  already_completed: boolean;
}

export interface ResearchOperationsSnapshot {
  scope: "assigned_participants" | "all_participants";
  generated_at: string;
  notification_preferences: { accepted: number; rejected: number; consumed: number; unknown: number };
  notification_deliveries: { pending: number; sending: number; sent: number; failed: number; retry_queue: number; exhausted: number; overdue: number };
  failure_reasons: Array<{ error_code: string; retry_category?: string; count: number }>;
  backlog: { stage_feedback: number; supervision: number; risk_review: number; privacy_requests: number };
  privacy_management_available: boolean;
  boundary_notice: string;
}

export type PrivacyRequestStatus = "pending" | "processing" | "completed" | "rejected" | "cancelled";

export interface PrivacyRequest {
  id: ID;
  user_id: ID;
  request_type: "delete_my_data" | string;
  status: PrivacyRequestStatus;
  created_at: ISODateTime;
  updated_at: ISODateTime;
  already_active?: boolean;
  already_processed?: boolean;
  participant_notice?: string | null;
  execution_proof_hash?: string | null;
}

export type PrivacyHandlingScope =
  | "account_identity"
  | "participant_records"
  | "feedback_and_training"
  | "messages_and_notifications"
  | "relationship_pilot"
  | "research_outputs";

export type PrivacyReviewAction = "start_processing" | "reject" | "return_to_pending";

export interface PrivacyReviewRequest extends PrivacyRequest {
  handled_by?: ID | null;
  handled_note?: string | null;
  handling_scope?: PrivacyHandlingScope[];
  reason?: string | null;
  decision?: string | null;
  processing_started_at?: ISODateTime | null;
  handled_at?: ISODateTime | null;
  version: number;
  policy_version?: string | null;
}

export interface PrivacyScopeTableCount { table: string; count: number }
export interface PrivacyScopePreview {
  request_id: ID;
  request_version: number;
  policy_version: string;
  policy_approval_status: string;
  scope_hash: string;
  scope: PrivacyHandlingScope[];
  modules: Array<{ scope: PrivacyHandlingScope; label: string; method: string; count: number; tables: PrivacyScopeTableCount[] }>;
  total_affected: number;
  retained_categories: Array<{ key: string; label: string; method: string; legal_basis: string }>;
  external_surfaces: Array<{ surface: string; status: string; rule?: string }>;
  irreversible_notice: string;
}

export interface PrivacyExecutionRecord {
  id: ID;
  actor_id: ID;
  environment: string;
  mode: "dry_run" | "execute";
  policy_version: string;
  scope_hash: string;
  status: string;
  proof_hash?: string | null;
  started_at: ISODateTime;
  completed_at?: ISODateTime | null;
}

export interface PrivacyApprovalRecord {
  actor_id: ID;
  actor_role: UserRole;
  scope_hash: string;
  policy_version: string;
  decision: string;
  created_at: ISODateTime;
}

export interface PrivacyExecutionResult {
  execution: PrivacyExecutionRecord;
  result: { mode: string; deleted: Record<string, number>; total_deleted: number; would_affect?: number; external_surfaces: Array<{ surface: string; status: string; rule?: string }> };
  already_processed: boolean;
}

export interface PrivacyRequestAction {
  id: ID;
  actor_id: ID;
  actor_role: UserRole;
  action: "participant_cancel" | PrivacyReviewAction | string;
  from_status: PrivacyRequestStatus;
  to_status: PrivacyRequestStatus;
  scope: PrivacyHandlingScope[];
  note?: string | null;
  created_at: ISODateTime;
}

export interface PrivacyReviewDetail {
  request: PrivacyReviewRequest;
  actions: PrivacyRequestAction[];
  approvals: PrivacyApprovalRecord[];
  executions: PrivacyExecutionRecord[];
  allowed_scopes: PrivacyHandlingScope[];
  already_processed?: boolean;
  boundary_notice: string;
}

export type ResearchQueueType = "notification_failed" | "stage_feedback" | "supervision" | "risk_review" | "feedback_review" | "privacy_request";
export type ResearchWorkItemPriority = "routine" | "attention" | "urgent";
export type ResearchWorkItemStatus = "open" | "claimed" | "processing" | "waiting" | "completed" | "closed" | "dead_letter";
export type ResearchWorkItemAction =
  | "claim"
  | "renew"
  | "return"
  | "transfer"
  | "start_processing"
  | "wait"
  | "add_note"
  | "send_participant_message"
  | "complete"
  | "close"
  | "reopen"
  | "retry_notification"
  | "recover_notification";

export interface ResearchQueueItem {
  id: ID;
  work_item_id: ID;
  user_id: ID;
  title: string;
  status: string;
  created_at: ISODateTime;
  wait_minutes: number;
  priority: ResearchWorkItemPriority;
  assignee_id?: ID | null;
  lease_expires_at?: ISODateTime | null;
  due_at?: ISODateTime | null;
  version: number;
  resolution_code?: string | null;
  source_type?: string | null;
  source_id?: string | null;
  enrollment_id?: string | null;
  error_code?: string | null;
  attempt_count?: number;
  retry_category?: "retryable" | "reauthorization_required" | "template_error" | "permanent_failure" | null;
  next_attempt_at?: ISODateTime | null;
  max_attempts?: number;
  dead_lettered_at?: ISODateTime | null;
  evaluation?: FeedbackEvaluation;
}

export interface ResearchQueuePage extends ListResponse<ResearchQueueItem> {
  queue: ResearchQueueType;
  scope: "assigned_participants" | "all_participants";
  boundary_notice: string;
  sync_truncated?: boolean;
}

export interface ResearchWorkItem {
  id: ID;
  queue_type: ResearchQueueType;
  source_type: string;
  source_id: ID;
  user_id: ID;
  priority: ResearchWorkItemPriority;
  status: ResearchWorkItemStatus;
  assignee_id?: ID | null;
  lease_expires_at?: ISODateTime | null;
  due_at?: ISODateTime | null;
  version: number;
  resolution_code?: string | null;
  closed_at?: ISODateTime | null;
  last_action_at?: ISODateTime | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface ResearchWorkItemNote {
  id: ID;
  actor_id: ID;
  actor_role: UserRole;
  note_type: "internal" | "handling";
  content: string;
  created_at: ISODateTime;
}

export interface ResearchWorkItemActionRecord {
  id: ID;
  actor_id: ID;
  actor_role: UserRole | "system";
  action: ResearchWorkItemAction;
  from_status: ResearchWorkItemStatus;
  to_status: ResearchWorkItemStatus;
  created_at: ISODateTime;
}

export interface ResearchWorkItemDetail {
  work_item: ResearchWorkItem;
  source: { source_type: string; source_id: ID; user_id: ID; read_only: true };
  notes: ResearchWorkItemNote[];
  actions: ResearchWorkItemActionRecord[];
  boundary_notice: string;
}

export interface ResearchWorkItemActionInput {
  action: ResearchWorkItemAction;
  expected_version: number;
  idempotency_key: string;
  note?: string;
  assignee_id?: ID;
  title?: string;
  body?: string;
  resolution_code?: string;
}

export interface ResearchWorkItemActionResult {
  work_item: ResearchWorkItem;
  already_processed: boolean;
  message_id?: ID;
}

export interface ResearchWorkItemMetrics {
  scope: "assigned_participants" | "all_participants";
  generated_at: ISODateTime;
  window_days: number;
  totals: Record<ResearchWorkItemStatus, number>;
  sla: { overdue: number; expired_leases: number };
  close_reasons: Array<{ resolution_code: string; count: number }>;
  workload: Array<{ actor_id: ID; actor_role: UserRole | "system"; action: ResearchWorkItemAction; count: number }>;
  trend: Array<{ day: ISODate; opened: number; closed: number }>;
  sync_truncation?: Partial<Record<ResearchQueueType, boolean>>;
  quality_boundary: string;
}

export interface User {
  id: ID;
  username?: string | null;
  nickname?: string | null;
  role: UserRole;
  anonymous_id?: string | null;
  avatar_url?: string | null;
  status?: string | null;
  source?: string | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export type ConsentType =
  | "user_agreement"
  | "privacy_policy"
  | "non_diagnostic_notice"
  | "research_authorization"
  | "contact_permission";

export interface ConsentRecord {
  id: ID;
  user_id: ID;
  consent_type: ConsentType;
  consent_version: string;
  agreed: number;
  agreed_at: ISODateTime;
  revoked_at?: ISODateTime | null;
  created_at: ISODateTime;
}

export interface ConsentInput {
  user_id?: ID;
  consent_type: ConsentType;
  consent_version?: string;
  agreed: boolean;
}

export type RiskReviewStatus = "pending" | "reviewed" | "follow_up_needed" | "transferred" | "closed";

export interface RiskReviewRecord {
  id: ID;
  user_id: ID;
  source_type: "feedback" | "student_profile" | string;
  source_id: ID;
  risk_level: RiskLevel;
  matched_categories_json: string;
  review_status: RiskReviewStatus;
  reviewer_id?: string | null;
  review_note?: string | null;
  reviewed_at?: ISODateTime | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface RiskReviewInput {
  reviewer_id?: string;
  review_status: RiskReviewStatus;
  review_note?: string;
  note?: string;
}

export interface Goal {
  id: ID;
  user_id: ID;
  scene: string;
  smart_goal: string;
  motivation?: string | null;
  start_date?: ISODate | null;
  status: GoalStatus;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface GoalInput {
  user_id?: ID;
  nickname?: string;
  scene: string;
  smart_goal: string;
  motivation?: string;
  start_date?: ISODate;
  status?: GoalStatus;
}

export interface EmotionDiary {
  id: ID;
  user_id: ID;
  goal_id?: ID | null;
  event_time?: ISODateTime | null;
  scene: string;
  event_description: string;
  parent_emotion: string;
  parent_emotion_intensity: number;
  child_emotion?: string | null;
  child_emotion_intensity?: number | null;
  automatic_thought?: string | null;
  body_sensation?: string | null;
  behavior?: string | null;
  raw_text?: string | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface EmotionDiaryInput {
  user_id?: ID;
  nickname?: string;
  goal_id?: ID;
  event_time?: ISODateTime;
  scene: string;
  event_description: string;
  parent_emotion: string;
  parent_emotion_intensity?: number;
  child_emotion?: string;
  child_emotion_intensity?: number;
  automatic_thought?: string;
  body_sensation?: string;
  behavior?: string;
  raw_text?: string;
}

export interface EmotionThermometerRecord {
  id: ID;
  user_id: ID;
  intensity_level: number;
  valence_level?: number | null;
  arousal_level?: number | null;
  control_level?: number | null;
  emotion_label?: string | null;
  brief_text?: string | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface AuthSession {
  token: string;
  user: User;
  dev_fallback?: boolean;
  identity_source?: "cloudbase_header" | "jscode2session" | "development_fallback" | string;
  phone_bound?: boolean;
  phone_masked?: string;
}

export interface AuthCapabilityStatus {
  available: boolean;
  mode?: "cloudbase_identity" | "jscode2session" | "cloudbase_access_token" | "wechat_access_token" | "not_configured" | string;
}

export interface AuthCapabilities {
  account_password: AuthCapabilityStatus;
  wechat_login: AuthCapabilityStatus;
  phone_login: AuthCapabilityStatus;
  privacy_notice: string;
}

export interface EmotionThermometerInput {
  user_id?: ID;
  nickname?: string;
  intensity_level: number;
  valence_level?: number;
  arousal_level?: number;
  control_level?: number;
  emotion_label?: string;
  brief_text?: string;
  created_at?: ISODateTime;
}

export interface EmotionThermometerDayResponse {
  user_id: ID;
  date: ISODate;
  items: EmotionThermometerRecord[];
  summary: {
    count: number;
    min: number | null;
    max: number | null;
    avg: number | null;
  };
  boundary_notice: string;
}

export interface FeedbackResult {
  id: ID;
  diary_id?: ID | null;
  tags: string[];
  labels: string[];
  trigger_summary: string;
  pattern_summary: string;
  supportive_feedback: string;
  alternative_response: string;
  recommended_card_ids: ID[];
  training_recommendation_rules?: TrainingRecommendationRule[];
  risk_level: RiskLevel;
  risk?: RiskCheckResult;
}

export interface FeedbackGenerateInput {
  user_id?: ID;
  diary_id?: ID;
  event_description?: string;
  automatic_thought?: string;
  behavior?: string;
  raw_text?: string;
}

export interface TrainingCard {
  id: ID;
  type: string;
  title: string;
  purpose: string;
  tags: string[];
  steps: string[];
  example: string;
  duration_minutes: number;
  theory_source?: string;
  target_skill?: string;
  suitable_for?: string[];
  not_suitable_for?: string[];
  reflection_questions?: string[];
  review_status?: string;
  reviewer_note?: string;
  enabled: boolean;
  user_facing_title?: string;
  mechanism_code?: string;
  target_constructs?: string[];
  indications?: string[];
  contraindications?: string[];
  minimum_dose?: {
    single_session_minutes: number;
    suggested_frequency: string;
    initial_cycle_days: number;
  };
  completion_criteria?: string;
  progression_criteria?: string;
  stop_rules?: string[];
  fidelity_check?: string[];
  outcome_links?: string[];
  evidence_level?: string;
  safety_level?: "standard" | "controlled";
  release_policy?: "shared_choice_candidate" | "manual_context_required";
  governance_review_status?: string;
}

export interface TrainingPlanCard {
  id: ID;
  title: string;
  type?: string | null;
  duration_minutes?: number | null;
  mechanism_code?: string | null;
  safety_level?: "standard" | "controlled" | null;
  release_policy?: "shared_choice_candidate" | "manual_context_required" | null;
}

export interface TrainingPlanItem {
  source_type: "assessment_dimension" | "profile_cluster";
  source_result_id: ID;
  source_worksheet: {
    id: ID;
    title: string;
  };
  source_worksheet_id?: ID;
  source_worksheet_title?: string;
  source_dimension?: string | null;
  source_profile_name?: string | null;
  dimension?: string | null;
  cluster_id?: number | string | null;
  cluster_name?: string | null;
  card_ids: ID[];
  cards: TrainingPlanCard[];
  reason: string;
  recommendation_reason?: string;
  next_step?: string;
  evidence_summary?: string;
  boundary_notice: string;
}

export interface TrainingPlanAssignment {
  id: ID;
  user_id: ID;
  phase: "start" | "practice" | "consolidate";
  cadence: "daily" | "every_other_day" | "three_per_week" | "weekly";
  status: "active" | "paused" | "completed";
  start_date: ISODate;
  goal_text: string;
  agreement_status: "self_selected" | "pending_researcher_review" | "researcher_confirmed";
  boundary_notice: string;
  created_at?: ISODateTime;
  updated_at?: ISODateTime;
}

export type NotificationConsentStatus = "unknown" | "accepted" | "rejected" | "banned" | "consumed";

export interface NotificationPreference {
  id: ID;
  channel: "wechat_subscribe";
  notification_type: "training_due" | string;
  template_id: string;
  subscription_mode: "once" | "long_term";
  consent_status: NotificationConsentStatus;
  consented_at?: ISODateTime | null;
  last_prompted_at?: ISODateTime | null;
  revoked_at?: ISODateTime | null;
  updated_at: ISODateTime;
}

export interface NotificationCapability {
  available: boolean;
  notification_type: "training_due" | string;
  template_id?: string | null;
  subscription_mode: "once" | "long_term";
  send_enabled: boolean;
  prompt_timing: "after_cadence_saved" | string;
  notice: string;
  preference?: NotificationPreference | null;
}

export interface TrainingPlan {
  user_id: ID;
  has_assessment: boolean;
  assignment?: TrainingPlanAssignment | null;
  has_recent_checkin?: boolean;
  last_completed_card_ids?: ID[];
  completed_card_ids?: ID[];
  recently_completed_card_ids?: ID[];
  latest_result?: Record<string, unknown> | null;
  plan_items: TrainingPlanItem[];
  empty_state?: {
    title: string;
    description: string;
    url: string;
  } | null;
  next_action?: {
    title: string;
    description: string;
    url: string;
  } | null;
  boundary_notice: string;
}

export type TodayJourneyState = "ready" | "paused" | "completed" | "not_due";

export interface TodayJourneyAction {
  type:
    | "read_feedback"
    | "read_message"
    | "training_paused"
    | "training_stage_completed"
    | "today_completed"
    | "practice_due"
    | "start_assessment"
    | "start_diary"
    | "set_training_cadence"
    | "training_not_due"
    | string;
  title: string;
  description: string;
  button_label: string;
  url: string;
  source_type: string;
  source_id?: ID | null;
  estimated_minutes?: number | null;
}

export interface TodayJourney {
  user_id: ID;
  state: TodayJourneyState;
  primary_action: TodayJourneyAction;
  secondary_action?: TodayJourneyAction | null;
  generated_at: ISODateTime;
  boundary_notice: string;
}

export type FeedbackEvaluation = "matches" | "partly_matches" | "does_not_match" | "uncomfortable";
export type FeedbackSourceType = "instant_feedback" | "stage_report" | "training_recommendation" | "message";

export interface FeedbackLedgerInput {
  source_type: FeedbackSourceType;
  source_id: ID;
  content_version: string;
  evaluation: FeedbackEvaluation;
  reason_code?: string;
  reason_text?: string;
  idempotency_key?: string;
}

export interface FeedbackLedgerEntry extends FeedbackLedgerInput {
  id: ID;
  user_id: ID;
  review_status: "recorded" | "pending_review" | string;
  status: "active" | "superseded";
  requires_human_review: boolean;
  stop_reinforcement: boolean;
  already_recorded?: boolean;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface FeedbackLedgerSummary {
  user_id: ID;
  evaluation_counts: Record<FeedbackEvaluation, number>;
  source_counts: Record<string, number>;
  pending_review_count: number;
  legacy_sources: Record<string, Array<{ evaluation: string; count: number }>>;
  boundary_notice: string;
}

export interface GrowthOverviewSections {
  activity: {
    available: boolean;
    record_count: number;
    practice_count: number;
  };
  assessments: {
    available: boolean;
    record_count: number;
    group_count: number;
    repeat_group_count: number;
  };
  relationship: {
    available: boolean;
    enrollment_count: number;
    task_count: number;
    longitudinal_count: number;
    report_count: number;
    latest_enrollment_id?: ID | null;
    status?: string | null;
    review_status?: string | null;
  };
  researcher_feedback: {
    available: boolean;
    count: number;
    unread_count: number;
    latest?: { id: ID; title?: string | null; created_at: ISODateTime } | null;
  };
}

export interface GrowthOverview {
  summary: {
    record_count: number;
    practice_count: number;
    feedback_count: number;
    next_step: string;
  };
  sections: GrowthOverviewSections;
  thermometer: Array<{
    id: ID;
    intensity_level: number;
    emotion_label?: string | null;
    created_at: ISODateTime;
  }>;
  assessment_groups: Array<{
    worksheet_id: ID;
    title: string;
    items: Array<{ id: ID; title: string; value?: number | null; created_at: ISODateTime }>;
  }>;
  timeline: Array<{
    id: ID;
    type: string;
    type_label: string;
    title: string;
    summary: string;
    created_at: ISODateTime;
  }>;
  boundary_notice: string;
}

export interface ProgressSummary {
  user_id: ID;
  range: "7d" | "14d" | "30d" | string;
  days: number;
  start_date: ISODate;
  end_date: ISODate;
  stability_status: "insufficient" | "fluctuating" | "converging" | "stable" | "low_confidence" | string;
  summary_text: string;
  assessment: {
    count: number;
    latest?: { id: ID; title?: string | null; created_at?: ISODateTime | null } | null;
    repeated_worksheets: Array<{
      worksheet_id: ID;
      title: string;
      count: number;
      latest_score?: number | null;
      previous_score?: number | null;
      score_delta?: number | null;
      dimension_trends: Array<{
        key: string;
        label: string;
        latest_score: number;
        previous_score: number;
        score_delta: number;
      }>;
    }>;
  };
  thermometer: {
    count: number;
    avg: number | null;
    min: number | null;
    max: number | null;
    trend_text: string;
  };
  checkins: {
    count: number;
    completed_count: number;
    top_cards: Array<[ID, number]>;
    average_emotion_delta: number | null;
    helpfulness_counts?: Array<[string, number]>;
    skip_reasons?: Array<[string, number]>;
    effectiveness_text?: string;
  };
  diaries: {
    count: number;
    frequent_scenes: Array<[string, number]>;
    frequent_emotions: Array<[string, number]>;
  };
  next_action: string;
  boundary_notice: string;
}

export interface ProfileTrendResponse {
  user_id: ID;
  range: string;
  assessment: ProgressSummary["assessment"];
  thermometer: ProgressSummary["thermometer"];
  stability_status: ProgressSummary["stability_status"];
  summary_text: string;
  boundary_notice: string;
}

export interface TrainingEffectivenessResponse {
  user_id: ID;
  range: string;
  checkins: ProgressSummary["checkins"];
  per_card_effectiveness?: Array<{
    card_id: ID;
    sample_count: number;
    thermometer_pair_count: number;
    average_intensity_delta: number;
    helpful_rate: number;
    sample_note: string;
  }>;
  next_action: string;
  boundary_notice: string;
}

export interface CourseSection {
  title: string;
  body: string;
}

export interface CourseSummary {
  id: ID;
  title: string;
  theme: string;
  scene: string;
  duration_minutes: number;
  section_count: number;
  first_section_title?: string;
  curriculum_node?: string;
  learning_objectives?: string[];
  review_status?: string;
  relation_to_cards_or_programs: ID[];
  boundary_notice: string;
}

export interface Course extends CourseSummary {
  enabled?: boolean;
  sections: CourseSection[];
  core_concept?: string;
  common_misconceptions?: Array<{ statement: string; correction: string }>;
  worked_example?: string;
  counter_example?: string;
  knowledge_checks?: Array<{
    id: ID;
    prompt: string;
    options: Array<{ value: string; label: string }>;
    correct_value: string;
    feedback_correct: string;
    feedback_incorrect: string;
  }>;
  guided_practice?: { card_id: ID; instruction: string };
  transfer_task?: string;
  reflection_prompts?: string[];
  booster_plan?: { review_after_days: number; prompt: string; next_course_id?: ID | null };
  audience_adaptation?: Record<string, string>;
}

export interface CourseListResponse {
  version: string;
  boundary_notice: string;
  items: CourseSummary[];
  pathways?: Array<{
    id: ID;
    title: string;
    audiences: string[];
    review_status: string;
    boundary_notice: string;
    nodes: Array<{ code: string; title: string; course_ids: ID[]; status: string }>;
  }>;
}

export interface CourseDetailResponse {
  version: string;
  course: Course;
}

export interface TextAnalysisOutputStatus {
  available: boolean;
  filename: string;
  raw_text_included: false;
  quality_status?: "valid" | "empty" | "insufficient_data" | "stale" | "validation_failed" | "privacy_blocked";
  privacy_gate_passed?: boolean;
  reason?: string;
  record_count?: number;
  analysis_version?: string;
  generated_at?: ISODateTime;
  [key: string]: unknown;
}

export interface TextAnalysisSummaryResponse {
  items: {
    features: TextAnalysisOutputStatus;
    semantic_network: TextAnalysisOutputStatus;
    family_topology: TextAnalysisOutputStatus;
    summary: TextAnalysisOutputStatus;
  };
  actor_id: ID;
  raw_text_included: false;
  boundary_notice: string;
}

export interface ProgramSession {
  session_no: number;
  title: string;
  objective: string;
  duration_minutes: number;
  steps: string[];
  writing_prompt?: string;
  reflection_questions: string[];
  disclaimer: string;
  completion_criteria?: string;
  stop_rule?: string;
}

export interface ProgramMeasurementPoint {
  key: string;
  label: string;
  description: string;
}

export interface ProgramMeasurementPlanSummary {
  status: "draft_requires_research_review" | "pilot_approved";
  measurement_point_labels: string[];
  requires_manual_review: boolean;
}

export interface ProgramMeasurementPlan {
  status: "draft_requires_research_review" | "pilot_approved";
  baseline_worksheet_ids: ID[];
  post_worksheet_ids: ID[];
  pending_manual_measure_ids?: ID[];
  measurement_points: ProgramMeasurementPoint[];
  primary_outcomes: string[];
  manual_review_items: string[];
  boundary_notice: string;
}

export interface ProgramSummary {
  id: ID;
  title: string;
  target_constructs: string[];
  audience: string;
  theory_source: string;
  review_status: string;
  protocol_version?: string;
  preview_only?: boolean;
  minimum_dose?: { planned_sessions: number; minimum_completed_sessions: number; session_interval_days: string };
  completion_definition?: string;
  boundary_notice: string;
  session_count: number;
  first_session_title?: string;
  measurement_plan?: ProgramMeasurementPlanSummary | ProgramMeasurementPlan;
}

export interface Program extends ProgramSummary {
  enabled?: boolean;
  recommended_card_ids?: ID[];
  sessions: ProgramSession[];
  inclusion_criteria?: string[];
  exclusion_criteria?: string[];
  pause_criteria?: string[];
  exit_criteria?: string[];
  safety_gate?: string;
  adverse_response_plan?: string;
  protocol_deviation_rule?: string;
  neutral_alternative?: string;
  interpretation_boundary?: string;
  clinical_boundary?: string;
  recommendation_sources?: Array<"program_default" | "user_choice" | "researcher_adjusted">;
  approval?: Record<string, { status: string; reviewer: string; reviewed_at: string; evidence_path: string }>;
}

export interface ProgramListResponse {
  version: string;
  boundary_notice: string;
  items: ProgramSummary[];
}

export interface ProgramDetailResponse {
  version: string;
  program: Program;
}

export interface ContentReviewUpdateInput {
  content_type: string;
  item_id: ID;
  review_status?: string;
  enabled_for_user?: boolean;
}

export interface ContentReviewUpdateResult {
  content_type: string;
  item_id: ID;
  review_status?: string;
  enabled_for_user?: boolean;
  filename: string;
}

export interface AssessmentOption {
  label: string;
  value: string;
  score?: number;
}

export interface AssessmentQuestion {
  id: ID;
  prompt: string;
  type: "text" | "scale";
  required?: boolean;
  dimension?: string;
  reverse_scored?: boolean;
  options?: AssessmentOption[];
}

export interface AssessmentSection {
  title: string;
  content: string;
}

export interface TrainingRecommendationRule {
  rule_id: ID;
  source_type: "assessment" | "diary";
  trigger_condition: Record<string, unknown>;
  theme: string[];
  recommended_card_ids: ID[];
  card_roles?: Array<{ card_id: ID; role: string }>;
  reason: string;
  today_suggestion: string;
  long_term_suggestion?: string;
  not_suitable_when: string;
  boundary_notice: string;
  review_status: string;
}

export interface AssessmentWorksheet {
  id: ID;
  source_file: string;
  source_title: string;
  display_title: string;
  category: string;
  audience?: string;
  audience_class?: string;
  reflex_node?: string;
  search_keywords?: string[];
  sensitive_category?: string;
  pages: number;
  instructions: string;
  sections: AssessmentSection[];
  questions: AssessmentQuestion[];
  scoring: string;
  recommended_card_ids: ID[];
  source_version: string;
  source_type?: string;
  review_status?: string;
  enabled_for_user?: boolean;
  review_note?: string;
  boundary_notice?: string;
  result_disclaimer?: string;
  profile_model_id?: string | null;
  training_recommendation_rules?: TrainingRecommendationRule[];
}

export interface AssessmentListItem {
  id: ID;
  source_file: string;
  source_title: string;
  display_title: string;
  category: string;
  audience?: string;
  audience_class?: string;
  reflex_node?: string;
  search_keywords?: string[];
  sensitive_category?: string;
  pages: number;
  instructions: string;
  source_version: string;
  source_type?: string;
  review_status?: string;
  enabled_for_user?: boolean;
  review_note?: string;
  boundary_notice?: string;
  result_disclaimer?: string;
  profile_model_id?: string | null;
  question_count: number;
  is_reference: boolean;
}

export interface AssessmentAnswer {
  question_id: ID;
  prompt: string;
  value: string;
  score?: number;
}

export interface AssessmentResult {
  id: ID;
  user_id: ID;
  worksheet_id: ID;
  worksheet_title: string;
  category?: string | null;
  answers_json: string;
  scores_json: string;
  total_score?: number | null;
  result_summary?: string | null;
  profile_model_id?: string | null;
  profile_cluster_id?: number | null;
  profile_pc1?: number | null;
  profile_pc2?: number | null;
  profile_confidence?: number | null;
  created_at: ISODateTime;
  answers?: AssessmentAnswer[];
  scores?: Record<string, unknown>;
  recommended_card_ids?: ID[];
  risk?: RiskCheckResult | null;
  boundary_notice?: string | null;
  result_disclaimer?: string | null;
}

export interface AssessmentResultInput {
  user_id?: ID;
  nickname?: string;
  worksheet_id: ID;
  answers: AssessmentAnswer[];
  result_summary?: string;
}

export interface AssessmentProfileCluster {
  cluster_id: number;
  profile_id?: string;
  profile_name: string;
  display_name?: string;
  n: number;
  percent: number;
  pca_centroid?: { pc1?: number | null; pc2?: number | null };
  supportive_explanation?: string;
  dimension_means?: Record<string, number>;
  dimension_z?: Record<string, number>;
  suggested_assessment_questions?: string[];
  recommended_project_tasks?: string[];
  recommended_card_ids?: ID[];
  card_reason?: string;
}

export interface AssessmentProfilePosition {
  available: boolean;
  reason?: string;
  model_id?: string;
  group_id?: string;
  standard_scale_name?: string;
  scale_id?: string;
  worksheet_id?: ID;
  research_dir?: string;
  source_dataset?: string;
  n_cases?: number;
  n_features?: number;
  chosen_k?: number;
  position?: {
    pc1?: number | null;
    pc2?: number | null;
    cluster_id?: number | null;
    profile_id?: string | null;
    profile_name?: string | null;
    display_name?: string | null;
    nearest_distance?: number | null;
    second_distance?: number | null;
    confidence?: number;
    posterior?: number;
    normalized_entropy?: number | null;
    mahalanobis_distance?: number;
    assignment_version?: string;
    interpretation_status?: "usable" | "low_confidence" | "outlier" | "pending_approval";
    can_use_interpretation?: boolean;
  };
  interpretation?: {
    status: "usable" | "low_confidence" | "outlier" | "pending_approval";
    can_use_interpretation: boolean;
    message: string;
    distance_threshold?: number | null;
    min_posterior?: number;
    max_entropy?: number;
    max_mahalanobis?: number;
  };
  clusters?: AssessmentProfileCluster[];
  radar_support?: {
    dimensions?: Array<{ code: string; label?: string }>;
  };
  feature_summary?: {
    answered_features: number;
    missing_features: number;
    total_features: number;
    missing_feature_ids?: string[];
    data_quality: "complete" | "partial";
  };
  feature_profile?: Array<{
    feature_id: string;
    label: string;
    raw_score?: number | null;
    z_score: number;
  }>;
  raw_scores?: Record<string, number | null>;
  z_scores?: Record<string, number>;
  explanation?: string;
  strength_note?: string;
  small_step?: string;
  suggested_assessment_questions?: string[];
  recommended_project_tasks?: string[];
  boundary_notice?: string;
}

export type ContentGovernanceStatus = "registered" | "draft" | "pending_review" | "rejected" | "approved" | "published" | "paused" | "retired";
export type ContentReviewDiscipline = "research" | "psychology" | "ethics" | "content";

export interface ContentGovernanceMetadata {
  source: string;
  source_version: string;
  copyright_status: "owned" | "licensed" | "public_domain" | "permission_recorded" | "unverified";
  age_scope: string;
  audience: string;
  change_summary: string;
  governance_status?: string;
}

export interface ContentGovernanceReview {
  id: ID;
  version_id: ID;
  discipline: ContentReviewDiscipline;
  decision: "approved" | "rejected";
  reviewer_id: ID;
  reviewer_role: string;
  evidence_path: string;
  note?: string;
  created_at: string;
}

export interface ContentGovernanceValidation {
  ok: boolean;
  errors: Array<Record<string, unknown>>;
  warnings: Array<Record<string, unknown>>;
  payload_hash_valid: boolean;
}

export interface ContentGovernanceVersion {
  id: ID;
  content_type: string;
  item_id: ID;
  version: string;
  parent_version_id?: ID | null;
  payload_hash: string;
  payload: Record<string, unknown> | string;
  metadata: ContentGovernanceMetadata;
  status: ContentGovernanceStatus;
  created_by: ID;
  created_at: string;
  updated_at: string;
  reviews?: ContentGovernanceReview[];
  releases?: Array<Record<string, unknown>>;
  validation?: ContentGovernanceValidation;
  dependency_impact?: { has_dependencies: boolean; impacts: Array<Record<string, unknown>> };
}

export interface ContentGovernanceInventoryItem {
  content_type: string;
  item_id: ID;
  source_file: string;
  source_version: string;
  active_hash: string;
  governed_version?: { id: ID; version: string; status: string; payload_hash: string } | null;
}

export interface ContentGovernanceDraftInput {
  content_type: string;
  item_id: ID;
  version: string;
  parent_version_id?: ID;
  payload: Record<string, unknown> | string;
  metadata: ContentGovernanceMetadata;
}

export interface ContentGovernanceDiff {
  version_id: ID;
  baseline: string;
  changed: boolean;
  diff: string[];
  truncated: boolean;
}

export interface ContentReplayCase {
  case_id: string;
  text: string;
  emotion?: string;
  behavior?: string;
  expected?: Record<string, unknown>;
}

export interface ContentReplayResult {
  summary: { total: number; passed: number; failed: number };
  replay_hash: string;
  evidence_level: "synthetic_only";
  contains_real_data: false;
  results: Array<Record<string, unknown>>;
}

export interface AdminWorksheet extends AssessmentWorksheet {
  created_at?: ISODateTime;
  updated_at?: ISODateTime;
}

export type AdminWorksheetInput = Partial<AdminWorksheet> & {
  id?: ID;
  display_title?: string;
};

export interface UserMessage {
  id: ID;
  user_id: ID;
  message_type: "system" | "supervision_feedback" | string;
  title: string;
  body?: string | null;
  source_type?: string | null;
  source_id?: string | null;
  sender_role?: "researcher" | "supervisor" | "admin" | string | null;
  status: "unread" | "read" | string;
  is_unread?: boolean;
  created_at: ISODateTime;
  read_at?: ISODateTime | null;
}

export interface UserMessageList {
  items: UserMessage[];
  count: number;
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
  unread_count: number;
}

export interface ResearcherMessageInput {
  enrollment_id: ID;
  title: string;
  body: string;
  message_type?: "researcher_message" | "relationship_stage_feedback";
  idempotency_key?: string;
}

export type {
  FourLayerProfile,
  HypothesisFeedback,
  RadarFeature,
  RelationshipDimension,
  RelationshipGrowth,
  RelationshipPilotEnrollment,
  RelationshipPilotTask,
  RelationshipScreeningReport,
} from "./relationship-pilot.generated";

export interface ProfileStats {
  user_id: ID;
  streak_days: number;
  weekly_record_count: number;
  weekly_diary_count: number;
  weekly_checkin_count: number;
  weekly_assessment_count: number;
  assessment_completed_count: number;
  unfinished_assessment_count: number;
  unread_message_count: number;
  week_start: string;
  week_end: string;
  boundary_notice: string;
}

export interface ProfileDimension {
  key: string;
  label: string;
  level: string;
  summary: string;
}

export interface RiskMatchedCategory {
  id: string;
  label: string;
  risk_level: RiskLevel;
  matched_keywords: string[];
  safe_response?: string;
}

export interface RiskCheckResult {
  source: string;
  risk_level: RiskLevel;
  matched_categories: RiskMatchedCategory[];
  requires_review: boolean;
  allow_auto_feedback: boolean;
  allow_recommended_training_cards: boolean;
  export_raw_text_by_default: boolean;
  safe_response: string;
  boundary_notice: string;
}

export interface StudentProfileScores {
  test_anxiety: number;
  iu_score: number;
  self_compassion: number;
  fear_score?: number;
  f_score?: number;
}

export interface StudentProfileInput {
  user_id?: ID;
  nickname?: string;
  assessment_result_id?: ID;
  round?: number;
  scores?: StudentProfileScores;
  answers?: Record<string, string | number>;
  text_answers?: Record<string, string>;
  support_resource?: string;
  free_text?: string;
}

export interface ProfileVisuals {
  radar: Array<{ label: string; value: number; max: number }>;
  pca: {
    user: { pc1?: number | null; pc2?: number | null; cluster_id?: number | null; profile_code?: string | null };
    points: Array<{ cluster_id: number; profile_id: string; pc1: number; pc2: number }>;
    clusters: Array<Record<string, unknown>>;
  };
  trends: Array<{ round: number; label: string; state_score?: number | null; profile_confidence?: number | null }>;
  keywords?: Array<{ word: string; count: number }>;
}

export interface StudentProfileReport {
  role: string;
  summary: string;
  mechanism: string;
  first_task: string;
  integrative_path?: Record<string, string>;
  next_questions?: string[];
  escalation?: string;
  metrics?: Array<{ label: string; value: string }>;
  keywords?: Array<{ word: string; count: number }>;
  sandplay_task?: SandplayTask;
}

export interface SandplaySymbol {
  type: string;
  label: string;
  mark: string;
  category: string;
}

export interface SandplayTask {
  title: string;
  prompt: string;
  focus: string;
  reflection_questions: string[];
  safety_note?: string;
  boundary_notice?: string;
  symbols?: SandplaySymbol[];
}

export interface StudentProfileResult {
  assessment_result_id?: ID;
  student_profile_id?: ID;
  saved_to_assessment_results?: boolean;
  saved_to_student_profiles?: boolean;
  profile_code: string;
  profile_name: string;
  confidence: number;
  cluster_id?: number | null;
  pc1?: number | null;
  pc2?: number | null;
  dimensions: ProfileDimension[];
  supportive_explanation: string;
  strength_note: string;
  small_step: string;
  recommended_card_ids: ID[];
  risk_level: RiskLevel;
  requires_review: boolean;
  allow_auto_feedback: boolean;
  model_version: string;
  model_type?: string;
  rules_version: string;
  boundary_notice: string;
  report?: StudentProfileReport;
  visuals?: ProfileVisuals;
  sandplay_task?: SandplayTask;
  created_at: ISODateTime;
}

export interface StudentProfileRecord {
  id: ID;
  user_id: ID;
  anonymous_id: string;
  assessment_result_id?: ID | null;
  round: number;
  source?: string | null;
  scores_json: string;
  text_features_json: string;
  profile_code: string;
  profile_name: string;
  confidence?: number | null;
  dimensions_json: string;
  recommended_task_ids_json: string;
  risk_level: RiskLevel;
  requires_review: 0 | 1;
  boundary_notice?: string | null;
  rules_version?: string | null;
  model_version?: string | null;
  model_type?: string | null;
  cluster_id?: number | null;
  pc1?: number | null;
  pc2?: number | null;
  report_json?: string | null;
  visuals_json?: string | null;
  report?: StudentProfileReport;
  visuals?: ProfileVisuals;
  scores?: Record<string, unknown>;
  dimensions?: ProfileDimension[];
  recommended_task_ids?: string[];
  export_allowed: 0 | 1;
  data_quality?: string | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
  latest_review?: ProfileReview | null;
}

export interface ProfileReview {
  id: ID;
  profile_id: ID;
  reviewer_id?: ID | null;
  review_status: ProfileReviewStatus;
  review_decision?: string | null;
  note?: string | null;
  action_summary?: string | null;
  visible_to_student: 0 | 1;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface ProfileReviewInput {
  reviewer_id?: ID;
  review_status?: ProfileReviewStatus;
  review_decision?: string;
  note?: string;
  action_summary?: string;
  visible_to_student?: boolean;
}

export interface ModelInfoProfile {
  profile_code: string;
  profile_name: string;
  enabled: boolean;
  risk_level: RiskLevel;
}

export interface ModelInfo {
  model_version: string;
  model_type?: string;
  rules_version: string;
  n_cases?: number;
  features?: string[];
  available_profiles: ModelInfoProfile[];
  boundary_notice: string;
}

export interface ScaleLikertOption {
  value: number;
  label: string;
}

export interface ScaleItem {
  item_code: string;
  display_order: number;
  text: string;
  dimension?: string;
  feature?: string;
  reverse_scored?: boolean;
}

export interface ScaleDefinition {
  scale_code: string;
  name: string;
  short_name: string;
  score_direction: string;
  items: ScaleItem[];
}

export interface StudentAssessmentPayload {
  version: string;
  model_version: string;
  likert: ScaleLikertOption[];
  scales: ScaleDefinition[];
  open_questions: Array<{ item_code: string; label: string; max_length: number }>;
  boundary_notice: string;
}

export interface ParentAssessmentPayload {
  scales: {
    version: string;
    likert: ScaleLikertOption[];
    scales: ScaleDefinition[];
  };
  questions: {
    version: string;
    questions: Array<{
      id: string;
      text: string;
      type: "choice" | "textarea";
      required?: boolean;
      max_length?: number;
      options?: Array<{ value: string; label: string }>;
    }>;
  };
  boundary_notice: string;
}

export interface ParentAssessmentInput {
  user_id?: ID;
  nickname?: string;
  participant_code?: string;
  research_consent?: boolean;
  study_batch?: string;
  source_channel?: string;
  started_at?: ISODateTime;
  completed_at?: ISODateTime;
  answers: Record<string, string | number>;
  question_answers?: Record<string, string>;
}

export interface ParentAssessmentResult {
  id: ID;
  user_id: ID;
  anonymous_id: string;
  participant_code?: string | null;
  profile_key: string;
  report_url?: string;
  report: {
    profile_key: string;
    role: string;
    summary: string;
    empathy: string;
    strength: string;
    action_title: string;
    action: string;
    course: string;
    metrics: Array<{ label: string; value: string }>;
    boundary_notice: string;
  };
  scores: Record<string, unknown>;
  quality_flags: Record<string, unknown>;
  created_at: ISODateTime;
}

export interface Checkin {
  id: ID;
  user_id: ID;
  card_id: ID;
  diary_id?: ID | null;
  completed: 0 | 1;
  emotion_before?: number | null;
  emotion_after?: number | null;
  reflection?: string | null;
  helpfulness_rating?: string | number | null;
  skip_reason?: string | null;
  source_recommendation_id?: ID | null;
  card_title?: string;
  card_duration_minutes?: number | null;
  card_safety_level?: string | null;
  created_at: ISODateTime;
}

export interface CheckinInput {
  user_id?: ID;
  nickname?: string;
  card_id: ID;
  diary_id?: ID;
  completed?: boolean;
  emotion_before?: number;
  emotion_after?: number;
  reflection?: string;
}

export interface WeeklyReport {
  id: ID;
  user_id: ID;
  week_start: ISODate;
  week_end: ISODate;
  frequent_scenes: Array<[string, number]>;
  frequent_emotions: Array<[string, number]>;
  common_patterns: Array<[string, number]>;
  completed_cards: ID[];
  assessment_summary?: {
    count: number;
    worksheet_names: Array<[string, number]>;
    dimension_summaries: Array<{
      key: string;
      label: string;
      count: number;
      latest_score: number;
      previous_score?: number | null;
      score_delta?: number | null;
      direction: string;
    }>;
    profile_position_count: number;
    requires_review_count: number;
    recommended_card_ids: ID[];
  };
  radar_support?: {
    dimensions?: Array<{ code: string; mean?: number; std?: number }>;
    value_source?: string;
  };
  suggested_assessment_questions?: string[];
  recommended_project_tasks?: string[];
  thermometer_summary?: {
    count: number;
    avg_intensity: number | null;
    min_intensity: number | null;
    max_intensity: number | null;
    avg_valence?: number | null;
    avg_arousal?: number | null;
    avg_control?: number | null;
    intensity_trend: string;
    trend_text: string;
  };
  training_effectiveness_summary?: {
    checkins?: ProgressSummary["checkins"];
    per_card_effectiveness?: TrainingEffectivenessResponse["per_card_effectiveness"];
    next_action?: string;
  };
  profile_trend?: {
    profile_count: number;
    latest_round: number;
    profile_names: Array<[string, number]>;
    requires_review_count: number;
    high_risk_count: number;
  };
  next_week_suggestion: string;
}

export interface SupervisionRequest {
  id: ID;
  user_id: ID;
  diary_id?: ID | null;
  message: string;
  contact?: string | null;
  risk_hint?: string | null;
  risk_level: RiskLevel;
  status: SupervisionStatus;
  supervisor_reply?: string | null;
  created_at: ISODateTime;
  replied_at?: ISODateTime | null;
}

export interface SupervisionInput {
  user_id?: ID;
  nickname?: string;
  diary_id?: ID;
  message: string;
  contact?: string;
  risk_hint?: string;
  risk_level?: RiskLevel;
}

export interface ListResponse<T> {
  items: T[];
  page?: number;
  page_size?: number;
  total?: number;
  has_more?: boolean;
}

export interface CardRecommendResponse {
  items: TrainingCard[];
  matched_tags: string[];
}

export type AiQaRoute =
  | "answered"
  | "risk_fixed"
  | "blocked_scope"
  | "blocked_privacy"
  | "blocked_injection"
  | "no_sources"
  | "postcheck_degraded"
  | "provider_degraded";

export interface AiQaCitation {
  content_type: string;
  content_id: string;
  title: string;
  version_id: ID;
  content_version: string;
  release_id: ID;
  payload_hash: string;
  excerpt: string;
  governance_status: "published";
  package_hash?: string | null;
}

export interface AiQaMessage {
  id: ID;
  session_id: ID;
  user_id: ID;
  role: "user" | "assistant";
  content: string;
  citations: AiQaCitation[];
  model: Record<string, unknown>;
  safety: { route?: AiQaRoute; human_escalation?: boolean; [key: string]: unknown };
  prompt_version: string;
  knowledge_version: string;
  token_estimate: number;
  cost_micros: number;
  created_at: ISODateTime;
}

export interface AiQaSession {
  id: ID;
  user_id: ID;
  mode: "research_sandbox";
  status: "active" | "deleted";
  synthetic_data: boolean | 0 | 1;
  context_policy: "current_session_only";
  research_use_allowed: false | 0;
  created_at: ISODateTime;
  updated_at: ISODateTime;
  deleted_at?: ISODateTime | null;
  messages?: AiQaMessage[];
}

export interface AiQaConfig {
  service_name: string;
  participant_enabled: false;
  sandbox_enabled: boolean;
  provider: "fake";
  stage: "synthetic_research_sandbox";
  governance_status: "blocked_human_review";
  participant_eligible: false;
  gate_decisions: Record<string, { proposed: unknown; status: string }>;
  runtime_control: { killed: 0 | 1; changed_at?: ISODateTime | null };
  data_policy: { cross_session_memory: false; provider_training: false; real_participant_data: false; write_tools: false };
  boundary_notice: string;
}

export interface AiQaAnswer {
  message: AiQaMessage;
  route: AiQaRoute;
  fixed_response: boolean;
  human_escalation: boolean;
  boundary_notice: string;
}

export interface AiQaEvaluationRun {
  id: ID;
  suite_version: string;
  provider_version: string;
  knowledge_snapshot_hash: string;
  metrics: {
    total: number;
    passed: number;
    failed: number;
    route_accuracy: number;
    critical_failures: number;
    citation_coverage: number;
    diagnostic_violations: number;
    human_escalation_rate: number;
  };
  thresholds: Record<string, number>;
  results: Array<{ case_id: string; category: string; expected_route: AiQaRoute; actual_route: AiQaRoute; passed: boolean; provider_called?: boolean; citation_present?: boolean }>;
  status: "engineering_threshold_passed" | "engineering_threshold_failed";
  created_by: ID;
  created_at: ISODateTime;
}

export interface AiQaEvaluationReview {
  id: ID;
  run_id: ID;
  reviewer_id: ID;
  decision: "approved_for_next_internal_stage" | "changes_required" | "stop";
  evidence_path: string;
  note?: string | null;
  created_at: ISODateTime;
}

export interface AiQaReviewEvidence {
  runs: Array<Omit<AiQaEvaluationRun, "results" | "created_at"> & { created_at?: ISODateTime }>;
  reviews: AiQaEvaluationReview[];
  safety_events: Array<Record<string, unknown>>;
  provider_events: Array<Record<string, unknown>>;
  raw_prompts_included: false;
  actor_scope: "own" | "all_internal";
}

export interface OfflineBenchmarkConfig {
  enabled: boolean;
  external_ingest_enabled: false;
  production_replacement_allowed: false;
  registry_version: string;
  registry_status: string;
  annotation_status: string;
  synthetic_case_count: 240;
  runtime_control: { disabled: 0 | 1; changed_at?: ISODateTime | null };
  boundary_notice: string;
}

export interface OfflineDatasetCard {
  id: ID;
  name: string;
  source_url: string;
  source_version: string;
  language: string;
  platform: string;
  population: string;
  context: string;
  license: string;
  content_rights_status: string;
  sensitivity: string;
  allowed_uses: string[];
  prohibited_uses: string[];
  artifact_sha256?: string | null;
  local_path?: string | null;
  ingest_status: string;
  deletion_method: string;
  review_note?: string | null;
  registry_version: string;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface OfflineBenchmarkRun {
  id: ID;
  benchmark_type: "affect_lexicon" | "network_algorithms";
  dataset_card_id: ID;
  evidence_level: "synthetic_engineering_only";
  algorithm_version: string;
  parameters: Record<string, unknown>;
  metrics: Record<string, unknown>;
  artifact_hash: string;
  raw_text_included: 0;
  production_replacement_allowed: 0;
  status: "engineering_threshold_passed" | "engineering_review_required";
  created_by: ID;
  created_at: ISODateTime;
}

export interface OfflineAgreementSummary {
  complete_double_annotated_cases: number;
  required_cases: 200;
  distinct_annotators: number;
  emotion_cohen_kappa: number | null;
  mean_valence_gap: number | null;
  mean_arousal_gap: number | null;
  agreement_thresholds: {
    emotion_cohen_kappa: number;
    maximum_mean_valence_gap: number;
    maximum_mean_arousal_gap: number;
    minimum_complete_cases: number;
  };
  human_gold_release_eligible: boolean;
  human_gold_released: false;
  boundary_notice: string;
}

export interface OfflineBlindCase {
  id: ID;
  text: string;
  synthetic: true;
  already_annotated: boolean;
}

export interface AssessmentListResponse {
  version: string;
  boundary_notice: string;
  items: AssessmentListItem[];
  groups?: Array<{
    key: string;
    count: number;
    nodes: Array<{ key: string; count: number }>;
  }>;
}
