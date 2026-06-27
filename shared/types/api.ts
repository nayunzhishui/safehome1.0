export type ID = string;
export type ISODateTime = string;
export type ISODate = string;

export type UserRole = "parent" | "student" | "admin";
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
  nickname?: string | null;
  role: UserRole;
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
  training_recommendation_rules?: TrainingRecommendationRule[];
}

export interface AssessmentListItem {
  id: ID;
  source_file: string;
  source_title: string;
  display_title: string;
  category: string;
  pages: number;
  instructions: string;
  source_version: string;
  source_type?: string;
  review_status?: string;
  enabled_for_user?: boolean;
  review_note?: string;
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
  created_at: ISODateTime;
  answers?: AssessmentAnswer[];
  scores?: Record<string, number | null>;
  recommended_card_ids?: ID[];
}

export interface AssessmentResultInput {
  user_id?: ID;
  nickname?: string;
  worksheet_id: ID;
  answers: AssessmentAnswer[];
  result_summary?: string;
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
}
