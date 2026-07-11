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
}

export interface ApiError {
  ok: false;
  error: {
    code: string;
    message: string;
  };
}

export type ApiResponse<T> = ApiSuccess<T> | ApiError;

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

export interface TrainingPlan {
  user_id: ID;
  has_assessment: boolean;
  assignment?: TrainingPlanAssignment | null;
  has_recent_checkin?: boolean;
  last_completed_card_ids?: ID[];
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
  status: "unread" | "read" | string;
  is_unread?: boolean;
  created_at: ISODateTime;
  read_at?: ISODateTime | null;
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
}

export interface CardRecommendResponse {
  items: TrainingCard[];
  matched_tags: string[];
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
