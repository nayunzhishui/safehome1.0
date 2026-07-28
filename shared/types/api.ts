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
  version: number;
}

export interface DataClaimResult {
  claim_id: string;
  status: "claimed";
  total_records: number;
  modules: DataClaimModuleCount[];
  claimed_at?: string | null;
  already_completed: boolean;
  version: number;
}

export type LoginIdentityState = "unbound" | "bound_direct" | "bound_linked" | "claim_pending" | "claimed";

export interface LoginIdentityDescriptor {
  state: LoginIdentityState;
  can_unbind: boolean;
}

export interface IdentityStatus {
  user_id: ID;
  role: UserRole | "user";
  auth_epoch: number;
  identities: {
    username: LoginIdentityDescriptor;
    wechat: LoginIdentityDescriptor;
    phone: LoginIdentityDescriptor;
    anonymous: LoginIdentityDescriptor;
  };
  linked_account_count: number;
  privacy_notice: string;
  already_unbound?: boolean;
  sessions_revoked?: boolean;
}

export interface IdentityMergeWorkflow {
  id: ID;
  source_user_id: ID;
  target_user_id: ID;
  status: "candidate" | "confirmed" | "executed" | "verified" | "rolled_back";
  reason_code: string;
  version: number;
  total_records: number;
  modules: DataClaimModuleCount[];
  verification: Record<string, unknown>;
  rollback_until?: ISODateTime | null;
  confirmed_at?: ISODateTime | null;
  executed_at?: ISODateTime | null;
  verified_at?: ISODateTime | null;
  rolled_back_at?: ISODateTime | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
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

export interface ResearchParticipantSummary {
  user_id: ID;
  anonymous_id: string;
  nickname?: string | null;
  role: UserRole | "user";
  last_activity_at?: ISODateTime | null;
  assessment_count: number;
  diary_count: number;
  checkin_count: number;
  program_count: number;
  relationship_count: number;
  supervision_count: number;
  unread_message_count: number;
}

export type ResearchParticipantModuleKey =
  | "assessments" | "measurements" | "diaries" | "training" | "stage_reports"
  | "relationship_pilot" | "project_tests" | "messages" | "human_support" | "timeline";

export interface ResearchParticipantModuleDescriptor {
  key: ResearchParticipantModuleKey;
  label: string;
  count: number;
  sensitive: boolean;
}

export interface ResearchParticipantDossier {
  participant: {
    user_id: ID;
    anonymous_id: string;
    nickname?: string | null;
    role: UserRole | "user";
    status?: string;
    created_at?: ISODateTime;
    updated_at?: ISODateTime;
  };
  enrollment?: Record<string, unknown> | null;
  assignment?: Record<string, unknown> | null;
  modules: ResearchParticipantModuleDescriptor[];
  audit_summary: { related_event_count: number };
  boundary_notice: string;
}

export interface ResearchParticipantModulePage extends ListResponse<Record<string, unknown>> {
  module: ResearchParticipantModuleKey;
  module_label: string;
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
  sensitive: boolean;
  timezone: "Asia/Shanghai";
  boundary_notice: string;
}

export interface ResearchParticipantPage extends ListResponse<ResearchParticipantSummary> {
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
  scope: "assigned_participants" | "all_participants";
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
  | "research_outputs"
  | "therapeutic_assessment";

export type TherapeuticAssessmentStatus = "open" | "support_required" | "feedback_sent" | "withdrawn";
export type TherapeuticAssessmentReadiness = "L0" | "L1" | "L2" | "L3";
export type TherapeuticAssessmentWorkflowState =
  | "draft_local" | "submitted" | "pending_human_review" | "needs_more_info"
  | "not_applicable" | "feedback_ready" | "feedback_draft" | "professional_review"
  | "participant_check" | "revision_requested" | "action_selected" | "followup"
  | "safety_path" | "archived" | "withdrawn";
export type TherapeuticAssessmentHypothesisState =
  | "observations_only" | "pattern_candidate" | "human_hypothesis_draft"
  | "human_reviewed" | "participant_checked" | "revised" | "withdrawn";
export type TherapeuticAssessmentSafetyState =
  | "not_assessed" | "low_risk" | "needs_human_review" | "safety_path"
  | "stabilized" | "closed";
export type TherapeuticAssessmentStateTrack = "workflow" | "hypothesis" | "safety";
export type TherapeuticAssessmentTransitionReason =
  | "participant_choice" | "research_review" | "evidence_updated" | "risk_signal"
  | "supervision_review" | "not_applicable" | "correction" | "followup_complete"
  | "withdrawal";

export interface TherapeuticAssessmentTransitionInput {
  track: TherapeuticAssessmentStateTrack;
  target_state: string;
  expected_version: number;
  reason_code: TherapeuticAssessmentTransitionReason;
}

export type TherapeuticAssessmentEvidenceKind = "O" | "P" | "H" | "U";
export interface TherapeuticAssessmentEvidenceItem {
  id: string;
  case_id: string;
  kind: TherapeuticAssessmentEvidenceKind;
  content: string;
  source_origin: "human" | "ai" | "system";
  source_ref?: string | null;
  provider_id?: string | null;
  observed_at?: string | null;
  context?: string | null;
  method_limitations: string;
  visibility_scope: Array<"participant" | "research_team" | "supervisor">;
  applicability_scope?: string | null;
  question_link?: string | null;
  exceptions: string[];
  time_window?: string | null;
  supporting_evidence: Array<{ ref: string; source: string }>;
  counter_evidence: string[];
  alternative_explanations: string[];
  falsification_criteria: string[];
  protective_function?: string | null;
  cost?: string | null;
  participant_recognition?: "unconfirmed" | "recognized" | "partly_recognized" | "not_recognized" | null;
  uncertainty_type?: "missing" | "conflict" | "permission_denied" | "unconfirmed" | null;
  author_id: string;
  review_status: "recorded" | "candidate" | "draft" | "human_reviewed" | "changes_requested" | "participant_checked";
  version: number;
  created_at: string;
}

export interface TherapeuticAssessmentResearcherDraft {
  id?: string | null;
  case_id: string;
  researcher_user_id: string;
  internal_notes: string;
  participant_visible_draft: string;
  filters: {
    kind?: TherapeuticAssessmentEvidenceKind | "";
    review_status?: TherapeuticAssessmentEvidenceItem["review_status"] | "";
    visibility?: "participant" | "research_team" | "supervisor" | "";
  };
  selected_evidence_id?: string | null;
  version: number;
  updated_at?: string | null;
}

export interface TherapeuticAssessmentResearcherWorkbench {
  case: TherapeuticAssessmentCase;
  evidence_items: TherapeuticAssessmentEvidenceItem[];
  evidence_total: number;
  page: number;
  page_size: number;
  has_more: boolean;
  filters: TherapeuticAssessmentResearcherDraft["filters"];
  draft: TherapeuticAssessmentResearcherDraft;
}

export interface TherapeuticAssessmentDataItem {
  id: string;
  case_id: string;
  subject_user_id: string;
  provider_user_id: string;
  involved_user_ids: string[];
  controller_user_id: string;
  visibility: "private" | "professionals" | "confirmed_shared_feedback";
  allowed_viewer_ids: string[];
  purpose: "collaborative_assessment" | "human_review" | "shared_feedback";
  expires_at: string;
  status: "active" | "pending_subject_consent" | "withdrawn";
  consent_version: number;
  version: number;
  retained_under_legal_hold: boolean;
  notification_preview: string;
}

export type TherapeuticAssessmentParticipantStep =
  | "boundary"
  | "issue"
  | "recent_event"
  | "resources"
  | "sharing"
  | "summary"
  | "feedback_check"
  | "action_review";

export interface TherapeuticAssessmentParticipantDraft {
  id?: string;
  case_id: string;
  participant_user_id: string;
  step_id: TherapeuticAssessmentParticipantStep;
  payload: Record<string, unknown>;
  status: "active" | "completed" | "discarded";
  version: number;
  client_updated_at?: string | null;
  updated_at?: string | null;
}

export interface TherapeuticAssessmentSafetyStatus {
  ordinary_flow_enabled: boolean;
  needs_human_understanding_count: number;
  pause_reason?: string | null;
  participant_message: string;
  reactivation_requires_human_evidence: true;
}

export interface TherapeuticAssessmentResponsibilityChain {
  id: string;
  case_id: string;
  responsible_user_id: string;
  supervisor_user_id: string;
  support_channel: string;
  evidence_ref: string;
  status: "active" | "inactive";
  queue_timeout_minutes: number;
  version: number;
}

export interface TherapeuticAssessmentSafetyEvent {
  id: string;
  case_id: string;
  signal_type: "self_harm" | "harm_other" | "violence" | "abuse" | "coercive_control" | "acute_crisis" | "other";
  state: "needs_human_understanding" | "safety_paused" | "human_taken_over" | "resolved_by_human";
  source_ref: string;
  reason_summary?: string | null;
  created_at: string;
  resolved_at?: string | null;
}

export interface TherapeuticAssessmentServiceLevel {
  id: TherapeuticAssessmentReadiness;
  display_name: string;
  short_name: string;
  description: string;
  human_led: boolean;
  supervision_required: boolean;
  formal_ta: boolean;
  participant_feedback_allowed: boolean;
  required_evidence: string[];
}

export interface TherapeuticAssessmentServiceLevelStatus {
  schema: string;
  version: string;
  levels: TherapeuticAssessmentServiceLevel[];
  current_default: TherapeuticAssessmentServiceLevel;
  production_max_without_human_chain: TherapeuticAssessmentReadiness;
  public_terms: string[];
  boundary_notice: string;
}

export interface TherapeuticAssessmentProductionContract {
  schema: "safehome.therapeutic-assessment.production-contract.v1";
  version: string;
  service_levels: TherapeuticAssessmentReadiness[];
  competency_levels: TherapeuticAssessmentCompetencyLevel[];
  evidence_kinds: TherapeuticAssessmentEvidenceKind[];
  five_gates: Array<"minimum_input" | "permission" | "source" | "language" | "responsibility">;
  separate_dimensions: Array<"service_level" | "competency_level" | "object_permission" | "safety_state">;
  default_unknown_decision: "deny";
  legacy_case_readable: true;
  drift_detected: false;
  production_release_approved: false;
  boundary_notice: string;
}

export type TherapeuticAssessmentQueueType =
  | "review"
  | "information"
  | "feedback"
  | "risk"
  | "supervision";

export interface TherapeuticAssessmentWorkQueueItem {
  id: string;
  case_id: string;
  queue_type: TherapeuticAssessmentQueueType;
  task_code: string;
  required_competency: TherapeuticAssessmentCompetencyLevel;
  priority: "normal" | "high" | "urgent";
  status: "open" | "claimed" | "handoff_required" | "completed" | "cancelled";
  scope_snapshot: {
    case_id: string;
    complexity_scope: string;
    readiness_level: TherapeuticAssessmentReadiness;
    safety_state: string;
  };
  drafted_by?: string | null;
  assigned_user_id?: string | null;
  due_at: string;
  overdue: boolean;
  version: number;
  created_at: string;
}

export interface TherapeuticAssessmentDutyShift {
  id: string;
  user_id: string;
  supervisor_user_id: string;
  queue_types: TherapeuticAssessmentQueueType[];
  scope: Record<string, string[]>;
  starts_at: string;
  expires_at: string;
  status: "active" | "ended" | "cancelled";
  effective: boolean;
  evidence_ref: string;
  version: number;
}

export interface TherapeuticAssessmentQueueRuntime {
  id: "global";
  paused: 0 | 1;
  reason?: string | null;
  pending_count: number;
  overdue_count: number;
  unattended_urgent_count: number;
  policy_version: string;
  version: number;
  updated_at: string;
}

export type PublicationChannel =
  | "therapeutic_feedback"
  | "relationship_report"
  | "researcher_message"
  | "ai_candidate";

export interface PublicationCandidate {
  id: string;
  channel: PublicationChannel;
  subject_type: string;
  subject_id: string;
  recipient_user_id: string;
  author_id?: string | null;
  reviewed_by?: string | null;
  published_by?: string | null;
  status: "draft" | "blocked" | "approved" | "published" | "withdrawn";
  blocked_gate?: string | null;
  reason_code?: string | null;
  risk_level: "low" | "medium" | "high";
  multi_party: boolean;
  gate_summary: Record<string, "passed" | "blocked">;
  diff: {
    previous_sha256?: string | null;
    current_sha256: string;
    changed: boolean;
  };
  policy_version: string;
  version: number;
  created_at: string;
  updated_at: string;
  published_at?: string | null;
  withdrawn_at?: string | null;
}

export interface TherapeuticAssessmentFeedbackVersion {
  id: string;
  case_id: string;
  version_no: number;
  source: "human" | "ai_draft";
  status: "draft" | "reviewed" | "sent" | "withdrawn";
  feedback_layer: "layer_1" | "layer_2" | "layer_3";
  recipient_user_id?: string | null;
  letter_title: string;
  observations: string[];
  evidence: string[];
  alternatives: string[];
  uncertainty: string;
  next_step: string;
  human_discussion: string[];
  participant_content: string;
  supersedes_feedback_id?: string | null;
  reviewed_by?: string | null;
  sent_at?: string | null;
  withdrawn_at?: string | null;
  withdrawal_reason?: string | null;
  lifecycle_version: number;
  delivery_count?: number;
  deliveries?: TherapeuticAssessmentFeedbackDelivery[];
  participant_response?: TherapeuticAssessmentFeedbackResponse | null;
  participant_responses?: TherapeuticAssessmentFeedbackResponse[];
}

export type TherapeuticAssessmentFeedbackRecognition = "like" | "partly_like" | "not_like" | "need_time";

export interface TherapeuticAssessmentFeedbackResponse {
  id: string;
  feedback_id: string;
  case_id: string;
  participant_user_id: string;
  recognition: TherapeuticAssessmentFeedbackRecognition;
  disagreement_note?: string | null;
  supersedes_response_id?: string | null;
  created_at: string;
}

export interface TherapeuticAssessmentFeedbackDelivery {
  id: string;
  feedback_id: string;
  case_id: string;
  recipient_user_id: string;
  sequence_no: number;
  status: "sent" | "withdrawn";
  sent_by: string;
  sent_at: string;
  withdrawn_at?: string | null;
}

export interface TherapeuticAssessmentAction {
  id: string;
  case_id: string;
  participant_user_id: string;
  feedback_version_id?: string | null;
  action_text: string;
  purpose_text: string;
  planned_date?: string | null;
  reminder_mode: "none" | "in_app" | "wechat_subscription";
  reminder_privacy: "generic_preview" | "hidden_preview";
  stop_conditions: string[];
  setback_plan: string;
  training_card_id?: string | null;
  linked_checkin_id?: string | null;
  status: "chosen" | "completed" | "declined" | "stopped";
  followup_note?: string | null;
  version: number;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export type TherapeuticAssessmentCompetencyLevel = "T1" | "T2" | "T3";
export type TherapeuticAssessmentTaskCode =
  | "workbench_draft"
  | "evidence_organize"
  | "evidence_pattern"
  | "feedback_draft"
  | "feedback_review"
  | "quality_review"
  | "quality_incident_analysis"
  | "quality_incident_resolution"
  | "formal_assessment"
  | "minor_or_family"
  | "couple_or_multi_person";

export interface TherapeuticAssessmentAuthorization {
  id: string;
  user_id: string;
  competency_level: TherapeuticAssessmentCompetencyLevel;
  task_code: TherapeuticAssessmentTaskCode;
  scope: {
    case_ids?: string[];
    complexity_scopes?: string[];
    readiness_levels?: TherapeuticAssessmentReadiness[];
    case_scope_snapshots?: Record<
      string,
      { complexity_scope: string; readiness_level: TherapeuticAssessmentReadiness }
    >;
  };
  supervisor_user_id: string;
  evidence_ref: string;
  starts_at: string;
  expires_at: string;
  status: "active" | "review_required" | "revoked";
  status_reason?: string | null;
  version: number;
  effective: boolean;
  created_at: string;
  updated_at: string;
}

export interface TherapeuticAssessmentAuthorizationStatus {
  authorized: boolean;
  task_code: TherapeuticAssessmentTaskCode;
  reason?: string;
  authorization_id?: string;
  competency_level?: TherapeuticAssessmentCompetencyLevel;
  expires_at?: string;
}

export type TherapeuticAssessmentQualityDimension =
  | "question_quality"
  | "evidence_sufficiency"
  | "authorization"
  | "language"
  | "participant_recognition"
  | "action_fit";

export interface TherapeuticAssessmentQualityRuntime {
  paused: boolean;
  reason?: string | null;
  pending_count: number;
  overdue_count: number;
  policy_version: string;
  new_case_intake_enabled: boolean;
}

export interface TherapeuticAssessmentQualityReview {
  id: string;
  case_id: string;
  feedback_id: string;
  service_level: TherapeuticAssessmentReadiness;
  sample_reason: string;
  status: "pending" | "in_review" | "passed" | "remediation_required";
  due_at: string;
  claimed_by?: string | null;
  completed_by?: string | null;
  decision?: "pass" | "remediation_required" | null;
  dimensions: Partial<
    Record<
      TherapeuticAssessmentQualityDimension,
      { status: "pass" | "concern" | "not_applicable"; note: string; evidence_ref: string }
    >
  >;
  remediation_summary?: string | null;
  version: number;
  overdue: boolean;
  assessment_question?: string;
  participant_user_id?: string;
}

export interface TherapeuticAssessmentQualityIncident {
  id: string;
  case_id: string;
  feedback_id?: string | null;
  quality_review_id?: string | null;
  reporter_user_id: string;
  source_type: "participant_report" | "staff_report" | "quality_sample";
  category: "complaint" | "correction_request" | "withdrawal_request" | "notification_issue" | "quality_review";
  description: string;
  requested_resolution: string;
  status: "reported" | "independent_review" | "resolved";
  impact_analysis: Record<string, unknown>;
  analyzed_by?: string | null;
  resolution_action?: "no_change" | "withdraw" | "correct" | null;
  replacement_feedback_id?: string | null;
  notification_status: "pending" | "sent";
  independent_reviewer_id?: string | null;
  resolution_summary?: string | null;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface TherapeuticAssessmentCase {
  id: string;
  participant_user_id: string;
  assessment_question: string;
  working_question?: string | null;
  question_candidates: Array<{ id: string; text: string; source: string }>;
  question_quality: {
    personal_concern?: boolean;
    explorable?: boolean;
    non_blame?: boolean;
    evidence_responsive?: boolean;
    allows_uncertainty?: boolean;
  };
  best_guess?: string | null;
  best_guess_notice: string;
  question_status: "draft" | "submitted" | "paused" | "deleted";
  candidate_decision: string;
  question_version: number;
  shared_scope: string[];
  consent_status: "active" | "withdrawn";
  status: TherapeuticAssessmentStatus;
  workflow_state: TherapeuticAssessmentWorkflowState;
  hypothesis_state: TherapeuticAssessmentHypothesisState;
  safety_state: TherapeuticAssessmentSafetyState;
  risk_level: "low" | "medium" | "high";
  complexity_scope: string;
  readiness_level: TherapeuticAssessmentReadiness;
  service_level: TherapeuticAssessmentServiceLevel;
  assigned_researcher_id?: string | null;
  version: number;
  disagreement_note?: string | null;
  feedback_versions: TherapeuticAssessmentFeedbackVersion[];
  actions: TherapeuticAssessmentAction[];
  boundary_notice: string;
  efficacy_score: null;
  created_at: string;
}

export interface TherapeuticAssessmentLifecycleMetrics {
  enabled: boolean;
  process_quality: Record<string, number | string | null>;
  implementation_quality: Record<string, number | boolean>;
  harm_incidents: {
    total: number;
    open: number;
    resolved?: number;
    items?: Array<Record<string, unknown>>;
    boundary?: string;
  };
  core_continuity: {
    independent_routes: string[];
    boundary: string;
  };
  boundary_notice?: string;
}

export interface TherapeuticAssessmentLifecycle
  extends TherapeuticAssessmentLifecycleMetrics {
  case_id: string;
  case_version?: number;
  workflow_state: TherapeuticAssessmentWorkflowState;
  hypothesis_state?: TherapeuticAssessmentHypothesisState;
  safety_state?: TherapeuticAssessmentSafetyState;
  feedback_versions?: Array<Record<string, unknown>>;
  delivery_receipts?: Array<Record<string, unknown>>;
  participant_responses?: Array<Record<string, unknown>>;
  actions?: TherapeuticAssessmentAction[];
  events?: Array<{
    id: string;
    action: string;
    actor_id: string;
    before_version?: number | null;
    after_version?: number | null;
    metadata: Record<string, unknown>;
    idempotency_key: string;
    created_at: string;
  }>;
  recovery?: {
    retryable_feedback_ids: string[];
    withdrawal_propagation_ok: boolean;
    privacy_deletion_request?: Record<string, unknown> | null;
  };
}

export type TherapeuticAssessmentReleaseGateName =
  | "engineering_content"
  | "human_evidence"
  | "workforce_duty"
  | "privacy_recovery"
  | "infrastructure_release";

export interface TherapeuticAssessmentReleaseEvidence {
  id: string;
  evidence_type: string;
  artifact_ref: string;
  artifact_sha256: string;
  environment: string;
  status: "pending" | "verified" | "rejected";
  recorded_by: string;
  verified_by?: string | null;
  verified_at?: string | null;
  notes?: string | null;
  version: number;
  created_at: string;
  updated_at: string;
  qualifies_for_production: boolean;
}

export interface TherapeuticAssessmentProductionGate {
  policy_version: string;
  registry_hash: string;
  status: "blocked" | "ready_for_owner_release";
  checks: Record<
    TherapeuticAssessmentReleaseGateName,
    {
      passed: boolean;
      missing: string[];
      evidence_ids: string[];
    }
  >;
  engineering_ready: boolean;
  human_evidence_ready: boolean;
  workforce_ready: boolean;
  privacy_recovery_ready: boolean;
  infrastructure_ready: boolean;
  production_release_approved: false;
  temporary_showcase_counts_as_permission: false;
  simulated_signoffs_counted: false;
  boundary_notice: string;
  latest_run?: Record<string, unknown> | null;
  run?: Record<string, unknown>;
  already_processed?: boolean;
}

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

export interface EmotionThermometerReceipt {
  sequence_today: number;
  local_date: ISODate;
  today_intensity_avg: number;
  recent_week_intensity_avg: number | null;
  messages: string[];
  practice_available: boolean;
  boundary_notice: string;
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
  receipt?: EmotionThermometerReceipt;
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
  recommendation_strategy?: string;
  fallback_strategy_version?: string;
  cold_start?: boolean;
  replacement_card_ids?: ID[];
  ranking_explanation?: Array<{
    card_id: ID;
    rank: number;
    feedback_applied: boolean;
    participant_controlled: boolean;
  }>;
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
  today_plan_items?: TrainingPlanItem[];
  recommendation_strategy?: string;
  fallback_strategy_version?: string;
  recommendation_controls?: {
    feedback_can_change_order: boolean;
    participant_can_correct_or_withdraw_feedback: boolean;
    legacy_strategy_replay_available: boolean;
    global_rollback_flag: string;
  };
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

export type TodayJourneyState = "ready" | "paused" | "completed" | "not_due" | "recoverable_error" | "controlled";

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
  state_contract: {
    reproducible_states: TodayJourneyState[];
    loading: { client_state: "loading"; preserve_previous_action: boolean };
    failure: { state: "recoverable_error"; show_retry: boolean; never_render_as_empty: boolean };
    weak_network_recovery: { retry: "manual"; preserve_local_draft: boolean; deduplicate_submit: boolean };
  };
  controlled_capabilities: {
    therapeutic_assessment: {
      status: "governance_gate_pending" | string;
      enabled: boolean;
      entry_url?: string | null;
      notice: string;
    };
  };
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

export interface FeedbackLedgerActionInput {
  action: "withdraw" | "correct";
  idempotency_key?: string;
  replacement?: Omit<FeedbackLedgerInput, "source_type" | "source_id" | "idempotency_key">;
}

export interface FeedbackLedgerEntry extends FeedbackLedgerInput {
  id: ID;
  user_id: ID;
  review_status: "recorded" | "pending_review" | string;
  status: "active" | "superseded" | "withdrawn";
  participant_status: "visible" | "corrected" | "withdrawn" | string;
  supersedes_id?: ID | null;
  withdrawn_at?: ISODateTime | null;
  requires_human_review: boolean;
  stop_reinforcement: boolean;
  already_recorded?: boolean;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface RecommendationSnapshot {
  id: ID;
  user_id: ID;
  source_result_id: ID;
  strategy_version: "feedback_adaptive_v2" | "legacy_rule_order_v1" | string;
  previous_strategy_version?: string | null;
  recommended_card_ids: ID[];
  reasons: Array<Record<string, unknown>>;
  status: string;
  rollback_available: boolean;
  already_recorded?: boolean;
  created_at: ISODateTime;
  boundary_notice: string;
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
  scoring_version?: string | null;
  raw_scale_json?: string;
  raw_scores_json?: string;
  transformed_scores_json?: string;
  transformation_version?: string | null;
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
  raw_scale?: { ranges?: Array<{ min: number; max: number }>; mixed_scales?: boolean; worksheet_id?: ID };
  raw_scores?: Record<string, unknown>;
  transformed_scores?: Record<string, unknown>;
  score_reporting_notice?: string;
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
  client_submission_id?: string;
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
    model_input_score?: number | null;
    z_score: number;
  }>;
  raw_scores?: Record<string, number | null>;
  worksheet_raw_scores?: Record<string, number | null>;
  model_input_scores?: Record<string, number | null>;
  score_spaces_separated?: boolean;
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
  delivery_id?: ID | null;
  delivery_version?: number | null;
  withdrawn_at?: ISODateTime | null;
  is_withdrawn?: boolean;
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

export type ResearchDeliveryType = "stage_feedback" | "participant_message";
export type ResearchDeliveryStatus = "draft" | "previewed" | "confirmed" | "sent" | "withdrawn";

export interface ResearchDeliveryContent {
  body?: string;
  observation?: string;
  evidence?: string;
  next_step?: string;
  open_question?: string;
}

export interface ResearchDeliveryVersion {
  id: ID;
  workflow_id: ID;
  version_no: number;
  title: string;
  content: ResearchDeliveryContent;
  content_hash: string;
  risk_level: "low" | "medium" | "high";
  created_by: ID;
  created_at: ISODateTime;
}

export interface ResearchDeliveryWorkflow {
  id: ID;
  enrollment_id: ID;
  user_id: ID;
  actor_id: ID;
  delivery_type: ResearchDeliveryType;
  status: ResearchDeliveryStatus;
  title: string;
  content: ResearchDeliveryContent;
  active_version?: ResearchDeliveryVersion | null;
  message?: UserMessage | null;
  source_report_id?: ID | null;
  version: number;
  preview: { title: string; body: string; boundary_notice: string };
  events: Array<{ action: string; from_status?: string | null; to_status: string; created_at: ISODateTime }>;
  confirmed_at?: ISODateTime | null;
  sent_at?: ISODateTime | null;
  withdrawn_at?: ISODateTime | null;
  idempotency_replayed?: boolean;
  already_sent?: boolean;
}

export type ResearchAssignmentRole = "researcher" | "supervisor";
export type ResearchAssignmentStatus = "active" | "revoked";

export interface ResearchCapabilitySummary {
  registry_version: string;
  formal_role: UserRole;
  effective_role: UserRole;
  development_exception_active: boolean;
  development_exception_is_formal_evidence: false;
  capability_ids: string[];
}

export interface ResearchScopeAssignment {
  id: ID;
  enrollment_id: ID;
  actor_id: ID;
  assignment_role: ResearchAssignmentRole;
  status: ResearchAssignmentStatus;
  version: number;
  assigned_by: ID;
  idempotency_key?: string | null;
  revoked_at?: ISODateTime | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface ResearchScopeAssignmentInput {
  enrollment_id: ID;
  actor_id: ID;
  assignment_role: ResearchAssignmentRole;
  idempotency_key: string;
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
  client_submission_id?: string;
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
  client_submission_id?: string;
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
  document_id?: ID;
  chunk_id?: ID;
  location?: string;
  source_ref?: string;
  source_version?: string;
  rights_status?: "owned" | "licensed" | "public_domain" | "permission_recorded";
  review_status?: "approved";
  valid_from?: ISODateTime | null;
  expires_at?: ISODateTime | null;
  audiences?: string[];
  retrieval_method?: AiKnowledgeRetrievalMethod;
  scores?: {
    bm25: number;
    vector: number;
    rerank: number;
    final: number;
  };
}

export type AiKnowledgeRetrievalMethod = "bm25" | "vector" | "hybrid";

export interface AiKnowledgeDocument {
  id: ID;
  version_id: ID;
  release_id: ID;
  content_type: string;
  item_id: string;
  document_version: string;
  source_ref: string;
  source_version: string;
  rights_status: "owned" | "licensed" | "public_domain" | "permission_recorded";
  review_status: "approved";
  valid_from?: ISODateTime | null;
  expires_at?: ISODateTime | null;
  audiences: string[];
  status: "active" | "withdrawn" | "expired";
  payload_hash: string;
  package_hash?: string | null;
  indexed_at?: ISODateTime | null;
  withdrawn_at?: ISODateTime | null;
  chunk_count: number;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface AiKnowledgeCandidate {
  id: ID;
  source_url: string;
  title: string;
  source_hash: string;
  rights_status: string;
  review_status: "not_reviewed";
  status: "quarantined";
  recorded_by: ID;
  indexed: false;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface AiKnowledgeInventory {
  documents: AiKnowledgeDocument[];
  candidates: AiKnowledgeCandidate[];
  candidate_content_stored: false;
  web_candidate_auto_approval: false;
}

export interface AiKnowledgeRetrievalResult {
  citations: AiQaCitation[];
  knowledge_snapshot_hash: string;
  only_published: true;
  retrieval_method: AiKnowledgeRetrievalMethod;
  evidence_status: "sufficient" | "insufficient";
  audience: string;
}

export interface AiKnowledgeRebuildResult {
  indexed_documents: number;
  active_documents: number;
  active_chunks: number;
  rejected_documents: number;
  rejection_reasons: Record<string, number>;
  only_governed_releases: true;
  candidate_content_ingested: false;
  human_release_approval: false;
}

export interface AiKnowledgeEvaluationRun {
  id: ID;
  suite_version: string;
  retrieval_method: AiKnowledgeRetrievalMethod;
  metrics: {
    recall_at_k: number;
    citation_accuracy: number;
    no_evidence_accuracy: number;
    case_pass_rate: number;
  };
  results: Array<{
    case_id: string;
    expected_content_ids: string[];
    actual_content_ids: string[];
    citation_locations: string[];
    passed: boolean;
  }>;
  knowledge_snapshot_hash: string;
  status: "engineering_threshold_passed" | "engineering_threshold_failed";
  created_by: ID;
  created_at: ISODateTime;
  human_release_approval: false;
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

export interface AiQaStructuredOutput {
  schema_version: "safehome.ai-qa-output.v1";
  answer: string;
  citation_refs: string[];
  uncertainty: "low" | "medium" | "high";
  evidence_status: "sufficient" | "insufficient";
  boundary_notice: string;
  human_verification_required: true;
}

export interface AiQaOutputGateSummary {
  schema_version: "safehome.ai-qa-output.v1";
  gates: [
    "minimum_input",
    "permission",
    "source",
    "language",
    "responsibility",
  ];
  structured_validation: ["pydantic", "json_schema"];
  retry_allowed: false;
  fixed_degradation: true;
  grounding_method: "lexical_overlap_heuristic_v1";
  grounding_is_factuality_check: false;
  human_verification_required: true;
}

export interface AiQaSession {
  id: ID;
  user_id: ID;
  mode: "research_sandbox";
  status: "active" | "deleted";
  synthetic_data: boolean | 0 | 1;
  context_policy: "current_session_only";
  research_use_allowed: false | 0;
  use_case_id: string;
  use_case_policy_version: string;
  created_at: ISODateTime;
  updated_at: ISODateTime;
  deleted_at?: ISODateTime | null;
  messages?: AiQaMessage[];
}

export interface AiQaUseCase {
  id: string;
  title: string;
  description: string;
  input_pattern: string;
  output_contract: string;
  human_verification_required: true;
}

export interface AiQaUseCaseCatalog {
  policy_version: string;
  stage: "research_synthetic_frozen";
  allowed_use_cases: AiQaUseCase[];
  prohibited_categories: string[];
  participant_entry: {
    current_stage_enabled: false;
    development_target_recorded: boolean;
    earliest_review_task: string;
  };
  write_actions_allowed: false;
  automatic_adoption_allowed: false;
  boundary_notice: string;
}

export type AiProviderEvidenceType =
  | "service_contract"
  | "data_processing_agreement"
  | "privacy_impact_assessment"
  | "data_residency_commitment"
  | "provider_training_non_use"
  | "retention_deletion_commitment"
  | "subprocessor_register"
  | "security_audit"
  | "sla_support"
  | "content_policy_approval"
  | "pricing_snapshot"
  | "owner_approval";

export interface AiProviderContractEvidence {
  id: ID;
  provider_id: "deepseek" | "openai";
  evidence_type: AiProviderEvidenceType;
  artifact_ref: string;
  artifact_sha256: string;
  status: "pending" | "verified" | "rejected";
  recorded_by: ID;
  verified_by?: ID | null;
  verified_at?: ISODateTime | null;
  notes?: string | null;
  version: number;
  created_at: ISODateTime;
  updated_at: ISODateTime;
  qualifies_for_selection: boolean;
}

export interface AiProviderCandidate {
  id: "deepseek" | "openai";
  display_name: string;
  base_url_host: string;
  secret_env_names: string[];
  public_document_findings: Record<
    "data_region" | "training_use" | "retention_deletion" | "subprocessors" | "audit" | "sla" | "content_policy" | "price",
    string
  >;
  official_sources: Array<{
    kind: string;
    url: string;
    reviewed_at: string;
  }>;
  public_document_status: string;
  verified_evidence: AiProviderEvidenceType[];
  missing_evidence: AiProviderEvidenceType[];
  production_eligible: false;
}

export interface AiProviderSelection {
  policy_version: string;
  reviewed_at: string;
  status: "blocked_external_contract_evidence";
  selected_provider: null;
  external_provider_enabled: false;
  required_evidence: AiProviderEvidenceType[];
  outbound_policy: {
    activated: false;
    candidate_hosts: string[];
    allowlist_activation_task: "T37-C03";
    client_side_calls_allowed: false;
  };
  candidates: AiProviderCandidate[];
  continuity_plans: Record<string, unknown>;
  boundary_notice: string;
}

export interface AiQaConfig {
  service_name: string;
  participant_enabled: false;
  sandbox_enabled: boolean;
  provider: "fake" | "deepseek" | "openai";
  stage: "synthetic_research_sandbox";
  governance_status: "blocked_human_review";
  participant_eligible: false;
  gate_decisions: Record<string, { proposed: unknown; status: string }>;
  runtime_control: { killed: 0 | 1; changed_at?: ISODateTime | null };
  data_policy: {
    cross_session_memory: false;
    provider_training: false;
    real_participant_data: false;
    write_tools: false;
    formal_participant_feedback_write: false;
    synthetic_retention_days: number;
    provider_metadata_contains_raw_text: false;
  };
  provider_policy: {
    approved_providers: Array<"fake" | "deepseek" | "openai">;
    adapter_candidates: Array<"deepseek" | "openai">;
    server_selected_only: true;
    secret_source: "cloudbase_secret_or_server_environment";
    secret_values_exposed: false;
    connect_timeout_ms: number;
    read_timeout_ms: number;
    timeout_ms: number;
    max_retries: number;
    circuit_failure_threshold: number;
    budget_micros_per_day: number;
    external_provider_enabled: boolean;
    runtime_admission_reason: string;
  };
  provider_selection: {
    policy_version: string;
    status: "blocked_external_contract_evidence";
    selected_provider: null;
    external_provider_enabled: false;
    candidate_ids: Array<"deepseek" | "openai">;
  };
  input_security: {
    version: string;
    instruction_data_separated: true;
    retrieved_content_trusted: false;
    message_field_allowlist: string[];
    source_field_allowlist: string[];
    max_question_length: number;
    max_source_excerpt_length: number;
    deidentification_categories: string[];
    cross_session_memory: false;
    raw_input_persisted: false;
    default_mode: "deny";
    allowlist: ["knowledge.retrieve"];
    write_tools_allowed: false;
    arbitrary_paths_allowed: false;
    arbitrary_network_hosts_allowed: false;
  };
  output_contract: AiQaOutputGateSummary;
  use_case_policy: AiQaUseCaseCatalog;
  boundary_notice: string;
}

export interface AiQaAnswer {
  message: AiQaMessage;
  route: AiQaRoute;
  fixed_response: boolean;
  human_escalation: boolean;
  uncertainty?: "low" | "medium" | "high";
  boundary_notice: string;
  review_case_id?: ID;
}

export type AiQaReviewDecision =
  | "adopt"
  | "modify"
  | "reject"
  | "none_match";

export interface AiQaReviewCase {
  id: ID;
  message_id: ID;
  session_id: ID;
  subject_type: string;
  subject_id: ID;
  recipient_user_id: ID;
  draft_author_id: string;
  publication_candidate_id?: ID | null;
  candidate_text: string;
  candidate_sha256: string;
  citations: AiQaCitation[];
  gate_violations: string[];
  scope: {
    object_scope?: string;
    risk_level?: string;
    involves_minor?: boolean;
    multi_party?: boolean;
    mechanism_explanation?: boolean;
  };
  source_snapshot_hash: string;
  required_task_code: string;
  required_competency: "T2" | "T3";
  status: "pending_review" | "adopted" | "modified" | "rejected" | "none_match";
  final_text?: string | null;
  final_sha256?: string | null;
  reviewed_by?: ID | null;
  published_by?: ID | null;
  formal_feedback_written: false;
  diff: { changed: boolean; similarity: number | null };
  version: number;
  created_at: ISODateTime;
  updated_at: ISODateTime;
  reviewed_at?: ISODateTime | null;
}

export interface AiQaReviewDecisionInput {
  decision: AiQaReviewDecision;
  expected_version: number;
  final_text?: string;
  rationale?: string;
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

export interface AffectModelCandidate {
  id: string;
  kind: "rule_lexicon" | "linear_calibrated" | "chinese_pretrained";
  name: string;
  version: string;
  execution_status:
    | "runnable_synthetic_engineering_only"
    | "blocked_artifact_and_rights_review";
  calibration: string;
  production_eligible: false;
  block_reasons?: string[];
}

export interface AffectModelCandidateRegistry {
  version: string;
  status: string;
  random_seed: 37;
  dataset_id: ID;
  split_policy: {
    version: string;
    train_percent: 70;
    validation_percent: 15;
    test_percent: 15;
    same_group_cross_split_allowed: false;
  };
  feature_contract: {
    version: string;
    normalization: string;
    raw_text_persisted_in_run: false;
    identity_features_allowed: false;
  };
  abstention_policy: {
    minimum_text_length: number;
    linear_probability_threshold: number;
    linear_threshold_candidates: number[];
    reasons: string[];
    outcome: "unknown_human_review";
  };
  probability_display_policy: "not_clinical_confidence";
  production_replacement_allowed: false;
  candidates: AffectModelCandidate[];
  model_card: {
    intended_use: string;
    out_of_scope: string[];
    known_limitations: string[];
    release_gate: string;
  };
}

export interface GroupNetworkAnalysisPolicy {
  version: string;
  status: string;
  research_questions: Array<{ id: string; description: string; causal: false }>;
  node_definition: string;
  edge_definition: string;
  window_definition: {
    minimum_days: number;
    maximum_days: number;
    maximum_windows_per_run: number;
  };
  missingness_definition: string;
  boundary_variants: Array<
    "approved_cohort" | "observed_nodes" | "active_nodes"
  >;
  minimum_privacy_thresholds: {
    nodes: number;
    edges_per_window: number;
    community_size: number;
    maximum_missing_edge_rate: number;
  };
  participant_visible: false;
  individual_metrics_allowed: false;
  training_model: false;
  causal_inference_allowed: false;
  family_quality_inference_allowed: false;
  production_group_data_allowed: false;
  real_data_gate: string[];
  boundary_notice: string;
}

export interface GroupNetworkAnalysisInput {
  schema?: string;
  version?: string;
  contains_real_data: false;
  data_class: "synthetic";
  output_mode: "group_aggregate";
  research_question_id: "group_interaction_structure_over_time";
  expected_missing_edge_rate: number;
  nodes: Array<{
    id: string;
    approved_cohort: boolean;
    observed: boolean;
    active: boolean;
  }>;
  windows: Array<{
    id: string;
    start_date: string;
    end_date: string;
    edges: Array<{ source: string; target: string; weight: number }>;
  }>;
  fixture_hash?: string;
  boundary_notice?: string;
}

export interface GroupNetworkAggregateMetrics {
  node_count: number;
  edge_count: number;
  density: number;
  weighted_strength_distribution: Record<string, number | null>;
  component_count: number;
  community_size_distribution: Record<string, number | null>;
  suppressed_small_community_count: number;
}

export interface GroupNetworkAnalysisReport {
  suppressed: boolean;
  suppression_reason: "minimum_privacy_threshold_not_met" | null;
  aggregate_metrics: GroupNetworkAggregateMetrics | null;
  boundary_sensitivity: Array<{
    boundary: string;
    metrics: GroupNetworkAggregateMetrics;
  }>;
  missingness_sensitivity: Array<{
    removed_edge_rate: number;
    metrics: GroupNetworkAggregateMetrics;
  }>;
  temporal_change: Record<string, unknown>;
  individual_metrics_included: false;
  node_identifiers_included: false;
  training_model: false;
  causal_inference: false;
  family_quality_inference: false;
  participant_visible: false;
  analysis_digest?: string;
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
  benchmark_type:
    | "affect_lexicon"
    | "affect_candidate_comparison"
    | "network_algorithms"
    | "network_group_descriptive";
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

export interface OfflineModelVersion {
  id: ID;
  candidate_id: string;
  model_version: string;
  registry_version: string;
  lexicon_hash: string;
  threshold_hash: string;
  feature_version: string;
  code_commit: string;
  dataset_id: ID;
  dataset_hash: string;
  schema_version: string;
  asset_manifest_hash: string;
  limitations: string[];
  status: "registered_shadow_only";
  created_by: ID;
  created_at: ISODateTime;
}

export interface OfflineModelShadowRun {
  id: ID;
  model_version_id: ID;
  parent_run_id?: ID | null;
  input_snapshot_hash: string;
  artifact_hash: string;
  status: "completed_shadow_only";
  raw_text_included: 0;
  participant_effect_allowed: 0;
  sample_count: number;
  coverage_rate: number;
  unknown_count: number;
  review_queue_count: number;
  limitations: string[];
  model_version: string;
  boundary_notice: string;
  created_by: ID;
  created_at: ISODateTime;
}

export interface OfflineModelReviewQueueItem {
  id: ID;
  shadow_run_id: ID;
  case_id: string;
  reason:
    | "text_too_short"
    | "out_of_domain_no_emotion_cue"
    | "conflicting_emotion_cues"
    | "low_model_confidence";
  status: "pending";
  raw_text_included: 0;
  created_at: ISODateTime;
}

export interface OfflineModelRuntimeControl {
  id: "global";
  mode: "shadow" | "readonly_degraded" | "off";
  active_model_version_id?: ID | null;
  active_threshold_hash?: string | null;
  version: number;
  reason: string;
  changed_by: ID;
  changed_at?: ISODateTime | null;
}

export interface OfflineModelMonitorRun {
  id: ID;
  scenario: string;
  model_version_id?: ID | null;
  metrics: Record<string, number>;
  triggers: Array<{
    metric: string;
    value: number;
    level: "yellow" | "red";
    threshold: number;
  }>;
  gate_status: "green" | "yellow_review" | "red_stopped";
  artifact_hash: string;
  contains_real_data: 0;
  created_by: ID;
  created_at: ISODateTime;
}

export interface OfflineModelMonitoringStatus {
  policy_version: string;
  runtime_control: OfflineModelRuntimeControl;
  recent_runs: OfflineModelMonitorRun[];
  participant_feedback_dependency: false;
  training_card_dependency: false;
  group_difference_interpretation: "aggregate_model_performance_only_not_individual_psychology";
  boundary_notice: string;
}

export interface OfflineModelReleaseGateCheck {
  gate_id: string;
  passed: boolean;
  source: "machine_contract" | "external_evidence";
  evidence_count: number;
}

export interface OfflineModelReleaseGateRun {
  id: ID;
  status: "blocked_external_gates" | "ready_for_separate_release_decision";
  checks: OfflineModelReleaseGateCheck[];
  blockers: string[];
  artifact_hash: string;
  runtime_activation_allowed: false;
  production_release_approved: false;
  generated_by: ID;
  generated_at: ISODateTime;
}

export interface OfflineModelReleaseGateStatus {
  policy_version: string;
  latest?: OfflineModelReleaseGateRun | null;
  evidence: Record<string, Array<{
    id: ID;
    gate_id: string;
    evidence_hash: string;
    evidence_type: string;
    signer_name: string;
    source_environment: string;
    simulated_agent: false;
    recorded_at: ISODateTime;
  }>>;
  runtime_activation_allowed: false;
  production_release_approved: false;
  boundary_notice: string;
}

export interface OfflineAgreementSummary {
  complete_double_annotated_cases: number;
  required_cases: 200;
  distinct_annotators: number;
  emotion_cohen_kappa: number | null;
  exact_multilabel_agreement: number | null;
  mean_valence_gap: number | null;
  mean_arousal_gap: number | null;
  label_distribution: Record<string, number>;
  missing_annotation_slots: number;
  disagreement_matrix: Record<string, Record<string, number>>;
  pending_adjudication_cases: number;
  adjudicated_cases: number;
  agreement_thresholds: {
    emotion_cohen_kappa: number;
    maximum_mean_valence_gap: number;
    maximum_mean_arousal_gap: number;
    minimum_complete_cases: number;
  };
  human_gold_release_eligible: boolean;
  human_gold_released: false;
  limitations: string[];
  boundary_notice: string;
}

export interface OfflineBlindCase {
  id: ID;
  text: string;
  synthetic: true;
  already_annotated: boolean;
}

export type OfflineEmotionLabel =
  | "anxiety"
  | "fear"
  | "anger"
  | "irritation"
  | "sadness"
  | "helplessness"
  | "guilt"
  | "shame"
  | "calm"
  | "positive"
  | "unknown"
  | "unmapped";

export interface OfflineAnnotationInput {
  emotion_labels: OfflineEmotionLabel[];
  intensity: 0 | 1 | 2 | 3 | 4;
  polarity_status: "affirmed" | "negated" | "uncertain";
  valence: number;
  arousal: number;
  context: string;
  reflex_node: string;
  evidence_excerpt?: string;
  rationale?: string;
  needs_human_understanding?: boolean;
  human_review_reason?: string;
}

export interface OfflineAnnotationGovernance {
  version: string;
  active_dataset_id: ID;
  active_data_class: "synthetic";
  purpose: string;
  minimum_necessary_fields: string[];
  identity_fields_hidden: string[];
  deidentification: {
    group_key_storage: string;
    raw_group_key_persisted: false;
    annotator_identity_visible_to_peer: false;
    free_text_export_allowed: false;
  };
  retention: Record<string, number | boolean>;
  split_policy: Record<string, string | number | boolean | string[]>;
  annotation_policy: Record<string, string | number | boolean>;
  real_data_gate: { allowed: false; required_evidence: string[]; automatic_approval_allowed: false; fallback: "synthetic_only" };
}

export interface OfflineAdjudicationQueueItem {
  case_id: ID;
  text: string;
  annotations: Array<{
    slot: "A" | "B";
    annotation_id: ID;
    emotion_labels: OfflineEmotionLabel[];
    intensity: number;
    polarity_status: "affirmed" | "negated" | "uncertain";
    evidence_excerpt?: string | null;
    rationale?: string | null;
    needs_human_understanding: boolean;
    human_review_reason?: string | null;
    manual_version: string;
  }>;
  annotator_identity_included: false;
  model_prediction_included: false;
}

export interface OfflineSplitReport {
  policy_version: string;
  group_key_persisted: false;
  group_hash_persisted: true;
  split_group_counts: Record<"train" | "validation" | "test", number>;
  cross_split_group_leakage: Array<{ dataset_card_id: ID; group_hash: string; splits: string[] }>;
  passed: boolean;
}

export interface ResearchMethodologyPublicStatus {
  status: "draft_before_freeze";
  formal_freeze_recorded: false;
  confirmatory_analysis_allowed: false;
  real_outcome_data_accessed: false;
  workbench_enabled: boolean;
  boundary_notice: string;
}

export interface ResearchMethodologyConfig extends ResearchMethodologyPublicStatus {
  registry_version: string;
  measure_count: number;
  product_line_count: number;
  unresolved_blocker_count: number;
  runtime_control: { disabled: 0 | 1; changed_at?: ISODateTime | null };
}

export interface ResearchMethodologyRegistry {
  version: string;
  status: "draft_before_freeze";
  real_outcome_data_accessed: false;
  formal_freeze_allowed: false;
  confirmatory_analysis_allowed: false;
  product_lines: Array<Record<string, unknown> & { id: string; primary_question: string; prohibited_interpretation: string }>;
  participant_flow_states: string[];
  measures: Array<Record<string, unknown> & { measure_id: string; display_name: string; item_count: number; freeze_status: "draft_before_freeze" }>;
  metrics: Array<Record<string, unknown> & { id: string; numerator_event: string; denominator_event: string; deduplication: string; window: string }>;
  missingness_plan: Record<string, unknown>;
  longitudinal_plan: Record<string, unknown>;
  analysis_sequence: Record<string, unknown>;
  simulation_plan: Record<string, unknown>;
  reporting_standards: Array<Record<string, unknown> & { id: string; status: string; official_url: string; accessed_on: string }>;
  signature_requirements: Array<{ role: string; status: "pending_human_signature"; evidence_required: string }>;
  unresolved_blockers: string[];
  boundary_notice: string;
}

export interface ResearchMethodologyVersion {
  id: ID;
  version: string;
  status: "draft_before_freeze";
  registry_hash: string;
  formal_freeze_allowed: 0;
  real_outcome_data_accessed: 0;
  registry: ResearchMethodologyRegistry;
  created_by: ID;
  created_at: ISODateTime;
}

export interface ResearchMethodologyCheck {
  id: ID;
  version_id: ID;
  artifact_hash: string;
  hard_checks: Record<string, boolean>;
  hard_check_passed: boolean;
  formal_freeze_ready: false;
  formal_freeze_recorded: false;
  real_outcome_rows_read: 0;
  status: string;
}

export interface ResearchMethodologySimulation {
  id: ID;
  version_id: ID;
  artifact_hash: string;
  parameters: Record<string, unknown>;
  metrics: Record<string, unknown> & { contains_real_data: false; confirmatory_power_claim: false };
  status: string;
}

export interface ResearchMethodologyEvidence {
  checks: Array<Record<string, unknown>>;
  simulations: Array<Record<string, unknown>>;
  packages: Array<Record<string, unknown>>;
}

export interface SecurityAuthorizationOperation {
  operation_id: string;
  method: string;
  path: string;
  object_type: string;
  action: "create" | "read" | "update" | "send" | "export" | "delete";
  object_scope: string;
  allowed_roles: string[];
  denied_roles: string[];
  legacy_admin_token: boolean;
  showcase_read_bypass: boolean;
  idempotency: { supported?: boolean; required?: boolean; header?: string | null };
}

export interface SecurityRegistry {
  version: string;
  status: "engineering_controls_ready_formal_acceptance_blocked";
  asset_inventory: Array<Record<string, string>>;
  authorization_matrix: SecurityAuthorizationOperation[];
  authorization_summary: { operation_count: number; showcase_bypass_operation_count: number; formal_permission_acceptance_passed: false; reason: string };
  web_miniprogram_threats: Array<Record<string, string>>;
  ai_threats: Array<Record<string, string>>;
  identity_controls: Record<string, unknown>;
  privacy_deletion_proof: Record<string, unknown>;
  temporary_showcase_exception: { enabled: true; risk_id: string; scope: string[]; stop_condition: string; accepted_for_formal_permission_testing: false };
  automated_scans: string[];
  external_gates: string[];
}

export interface SecurityScanResult {
  id?: ID;
  mode: "local_static_redacted";
  hard_checks_passed: boolean;
  blockers: string[];
  warnings: string[];
  checks: Array<Record<string, unknown> & { id: string; status: string; severity: string }>;
  artifact_hash: string;
  secret_values_returned: false;
  production_approval_inferred: false;
}

export interface SecurityWorkbench {
  registry: SecurityRegistry;
  registry_hash: string;
  runs: Array<Record<string, unknown>>;
  events: Array<Record<string, unknown>>;
  deletion_verifications: Array<Record<string, unknown>>;
  scan_execution_enabled: boolean;
  formal_permission_acceptance_passed: false;
}

export interface SecurityPublicStatus {
  status: string;
  engineering_controls_ready: true;
  formal_permission_acceptance_passed: false;
  temporary_showcase_exception_enabled: boolean;
  operation_count: number;
  participant_ai_enabled: false;
  boundary_notice: string;
}

export interface ReliabilityPublicStatus {
  status: string;
  workbench_enabled: boolean;
  production_slo_frozen: false;
  gradual_release_enabled: false;
  fault_injection_enabled: boolean;
  boundary_notice: string;
}

export interface ReliabilityJourney {
  journey_id: string;
  label: string;
  paths: string[];
}

export interface ReliabilityRegistry {
  version: string;
  status: string;
  journeys: ReliabilityJourney[];
  trace_fields: string[];
  sensitive_fields_forbidden: string[];
  job_adapters: Array<{ job_type: string; [key: string]: unknown }>;
  feature_flags: Array<{ name: string; default_enabled: boolean; role_scope: string[] }>;
  fault_scenarios: Array<{ scenario: string; expected: string }>;
  production_slo: { status: "pending_test_cloud_observation"; thresholds: null };
  external_gates: string[];
  production_release: { approved: false; automatic_signature_allowed: false; temporary_showcase_exception_accepted: false };
}

export interface ReliabilityJob {
  id: ID;
  job_type: string;
  source_type: string;
  source_id: string;
  idempotency_key: string;
  status: "pending" | "leased" | "retrying" | "completed" | "dead_letter";
  attempt_count: number;
  max_attempts: number;
  available_at: ISODateTime;
  last_error_code?: string | null;
  updated_at: ISODateTime;
}

export interface ReliabilityFeatureFlag {
  id: ID;
  flag_name: string;
  version: number;
  enabled: boolean;
  role_scope: string[];
  rollout_percent: number;
  reason_code: string;
  changed_at: ISODateTime;
}

export interface ReliabilitySloSnapshot {
  id: ID;
  environment: "local_synthetic" | "test_cloud_evidence_pending";
  window_minutes: number;
  metrics: Record<string, { requests: number; success_rate: number; error_rate: number; retry_rate: number; recovery_rate: number; latency_p50_ms: number; latency_p95_ms: number }>;
  status: "local_evidence_only";
  production_slo_frozen: false;
  created_at: ISODateTime;
}

export interface ReliabilityWorkbench {
  registry: ReliabilityRegistry;
  task36_integration: Task36ReliabilitySecurityRegistry;
  recent_events: Array<Record<string, unknown>>;
  jobs: ReliabilityJob[];
  feature_flags: ReliabilityFeatureFlag[];
  slo_snapshots: ReliabilitySloSnapshot[];
  drill_runs: Array<Record<string, unknown>>;
  evidence_packages: Array<Record<string, unknown>>;
  production_slo_frozen: false;
  gradual_release_enabled: false;
}

export interface Task36ReliabilitySecurityJourney {
  id: string;
  engine: string;
  idempotency: boolean;
  concurrency: string;
  retry: string;
  dead_letter: boolean;
  manual_recovery: boolean;
  object_scope: string;
  deletion_scope: string;
}

export interface Task36ReliabilitySecurityRegistry {
  schema: "safehome.task36.reliability_security.v1";
  version: string;
  status: string;
  production_defaults: Record<string, boolean>;
  journeys: Task36ReliabilitySecurityJourney[];
  alert_rules: Array<Record<string, string>>;
  forbidden_evidence_fields: string[];
  external_gates: string[];
  formal_permission_acceptance_passed: false;
  temporary_showcase_exception_is_evidence: false;
  production_release_approved: false;
}

export type UXGateStatus = "passed" | "failed" | "manual_required" | "not_run";

export interface UXPageCoverageEntry {
  platform: "web" | "miniprogram";
  path: string;
  title: string;
  workspace: string;
  goal: string;
  primary_action: string;
  data_source: string;
  states: string[];
  roles: string[];
  sensitivity: "low" | "medium" | "high" | "critical";
  owner: string;
  draft_required: boolean;
}

export interface UXExperienceRegistry {
  version: string;
  status: string;
  participant_information_architecture: string[];
  researcher_information_architecture: string[];
  home_layout_guard: { preserve_existing_blocks: boolean; today_step_after: string; today_step_before: string };
  design_tokens: Record<string, string[]>;
  automated_gates: string[];
  form_resilience: string[];
  pages: UXPageCoverageEntry[];
  external_gates: Array<{ gate: string; status: string }>;
  boundary_notice: string;
}

export interface UXAuditRun {
  id: ID;
  environment: "local_automated" | "test_cloud_evidence_pending";
  platform: "web" | "miniprogram" | "cross_platform";
  viewport: string;
  registry_version: string;
  results: Record<string, { status: UXGateStatus; checked: number; issues: number; artifact: string }>;
  artifact_hash: string;
  status: string;
  contains_participant_text: false;
  created_by: ID;
  created_at: ISODateTime;
}

export interface UXGovernancePublicStatus {
  status: string;
  registry_version: string;
  miniprogram_page_count: number;
  web_route_count: number;
  automated_gate_count: number;
  human_device_acceptance_approved: false;
  formative_research_approved: false;
  release_approved: false;
  boundary_notice: string;
}

export interface UXGovernanceWorkbench {
  registry: UXExperienceRegistry;
  audit_runs: UXAuditRun[];
  evidence_packages: Array<Record<string, unknown>>;
  external_gates: Array<{ gate: string; status: string }>;
  human_device_acceptance_approved: false;
  formative_research_approved: false;
  release_approved: false;
}

export interface OperationsCapability {
  id: string;
  title: string;
  intended_use: string;
  owner: { accountable_role: string; named_owner_status: string };
  dependencies: string[];
  data: { object_scopes: string[]; sensitivity: string; participant_text_allowed_in_governance_records: false };
  open_roles: string[];
  feature_flags: string[];
  version: string;
  tests: string[];
  rollback: string;
  governance_status: string;
  technical_implementation_complete: boolean;
  production_release_approved: false;
  operation_ids: string[];
}

export interface OperationsCapabilityRegistry {
  version: string;
  status: string;
  operation_count: number;
  capability_count: number;
  capabilities: OperationsCapability[];
  external_gates: string[];
  temporary_showcase_exception: { retained: true; formal_permission_acceptance: false; production_release_blocker: true };
  treatment_assessment: { synthetic_l0_allowed: true; real_participant_release_allowed: false; blocked_by: string[] };
  production_release_approved: false;
  boundary_notice: string;
}

export interface OperationsReplayRun {
  id: ID;
  package_id: ID;
  suite_version: string;
  metrics: { total: number; passed: number; failed: number; high_severity_regressions: number; behavior_diff_count?: number; wording_diff_count: number };
  snapshot_hash: string;
  status: string;
  high_severity_regressions: number;
  wording_diff_count: number;
  contains_real_data: false;
  created_at: ISODateTime;
}

export interface OperationsPackageReview {
  id: ID;
  stage: "review" | "approval";
  domain: string;
  decision: string;
  reviewer_id: ID;
  reviewer_role: string;
  evidence_ref: string;
  created_at: ISODateTime;
}

export interface OperationsReleasePackage {
  id: ID;
  package_version: string;
  previous_package_id?: ID | null;
  risk_level: "low" | "medium" | "high";
  target_environment: "local_synthetic" | "production_candidate";
  capability_ids: string[];
  manifest_hash: string;
  artifact_count: number;
  status: string;
  proposed_by: ID;
  submitted_at?: ISODateTime | null;
  released_by?: ID | null;
  released_at?: ISODateTime | null;
  production_release_approved: false;
  reviews?: OperationsPackageReview[];
  approvals?: OperationsPackageReview[];
  replay_runs?: OperationsReplayRun[];
}

export interface OperationsMonitoringSnapshot {
  id: ID;
  environment: string;
  window_days: number;
  metrics: Record<string, number | null | Record<string, number>>;
  thresholds: Record<string, number>;
  drift_signals: Array<{ metric: string; direction: string; value: number; threshold: number; action: "human_review_required" }>;
  review_required: boolean;
  automatic_participant_or_family_judgment: false;
  contains_participant_text: false;
  interpretation?: string;
  created_at: ISODateTime;
}

export interface OperationsIncidentNotification {
  id: ID;
  recipient_role: string;
  status: "queued" | "retry_queued" | "dispatched";
  attempt_count: number;
  created_at: ISODateTime;
}

export interface OperationsIncident {
  id: ID;
  capability_id: string;
  package_id?: ID | null;
  incident_type: "unauthorized_access" | "data_leak" | "severe_adverse_event" | "ai_safety_failure";
  severity: "high" | "critical";
  status: string;
  summary_code: string;
  evidence_hold_hash: string;
  capability_disabled: true;
  notifications: OperationsIncidentNotification[];
  postmortem?: Record<string, unknown>;
  reported_at: ISODateTime;
}

export interface OperationsPublicStatus {
  status: string;
  registry_version: string;
  capability_count: number;
  active_package_count: number;
  open_incident_count: number;
  temporary_showcase_exception_retained: true;
  formal_permission_acceptance: false;
  production_release_approved: false;
  boundary_notice: string;
}

export interface OperationsGovernanceWorkbench {
  registry: OperationsCapabilityRegistry;
  asset_cards: { cards: Array<{ id: string; card_type: "dataset" | "rule" | "model"; current_status: string }> };
  packages: OperationsReleasePackage[];
  runtime_controls: Array<Record<string, unknown>>;
  monitor_snapshots: OperationsMonitoringSnapshot[];
  incidents: OperationsIncident[];
  evidence_packages: Array<Record<string, unknown>>;
  production_release_approved: false;
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

export type ResearchAnalysisType = "affect_aggregate" | "semantic_network" | "family_topology";
export type ResearchAnalysisJobStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "canceled"
  | "expired"
  | "suspended";

export interface ResearchAnalysisSnapshot {
  id: ID;
  enrollment_id: ID;
  purpose_code: string;
  consent_type: string;
  consent_version: string;
  authorization_status: "active" | "suspended" | "expired";
  source_count: number;
  snapshot_hash: string;
  expires_at: ISODateTime;
  raw_text_included: false;
}

export interface ResearchAnalysisArtifact {
  id: ID;
  job_id: ID;
  snapshot_id: ID;
  analysis_type: ResearchAnalysisType;
  analysis_version: string;
  metrics: {
    coverage_rate: number;
    unknown_rate: number;
    sample_size: number;
    quality_status: "sufficient" | "limited" | "insufficient";
    result?: Record<string, unknown>;
    warnings?: string[];
  };
  artifact_hash: string;
  quality_status: "sufficient" | "limited" | "insufficient";
  boundary_notice: string;
  visibility: "researcher_only";
  status: "active" | "suspended" | "deleted";
  raw_text_included: false;
}

export interface ResearchAnalysisJob {
  id: ID;
  snapshot_id: ID;
  analysis_type: ResearchAnalysisType;
  analysis_version: string;
  resource_hash: string;
  parameters: Record<string, unknown>;
  status: ResearchAnalysisJobStatus;
  attempt_count: number;
  max_attempts: number;
  available_at: ISODateTime;
  last_error_code?: string | null;
  result_artifact_id?: ID | null;
  shadow_mode: true;
  created_by: ID;
  created_at: ISODateTime;
  updated_at: ISODateTime;
  dead_lettered_at?: ISODateTime | null;
  artifact?: ResearchAnalysisArtifact | null;
  boundary_notice?: string;
  raw_text_included?: false;
}

export interface ResearchAnalysisJobList {
  items: ResearchAnalysisJob[];
  count: number;
  raw_text_included: false;
  boundary_notice: string;
}

export interface ResearchAnalysisCatalogPipeline {
  analysis_type: ResearchAnalysisType;
  label: string;
  analysis_version: string;
  resource_hash: string;
  data_mode: "project_owned_synthetic_only";
  real_participant_processing_enabled: false;
  minimum_sample: number;
  maximum_graph_nodes: number;
  maximum_graph_edges: number;
  status: "engineering_shadow_ready";
}

export interface ResearchAnalysisCatalog {
  catalog_version: string;
  fixture_id: string;
  pipelines: ResearchAnalysisCatalogPipeline[];
  external_datasets_downloaded: false;
  production_training_enabled: false;
  real_participant_processing_enabled: false;
  human_rights_review_status: "pending";
  resilience_summary: {
    idempotency: boolean;
    concurrency: string;
    retry: string;
    dead_letter: boolean;
    manual_recovery: boolean;
    derived_deletion: string;
    production_release_approved: false;
  };
  boundary_notice: string;
}

export type ComputationEntityType =
  | "Observation"
  | "DerivedFeature"
  | "ModelRun"
  | "AnalysisArtifact"
  | "Citation"
  | "HumanReview";

export interface ComputationContractPublicStatus {
  contract_version: "safehome.computation.v1";
  entity_types: ComputationEntityType[];
  required_input_fields: string[];
  governed_output_fields: string[];
  legacy_readable: true;
  writes_enabled: false;
  boundary_notice: string;
}
