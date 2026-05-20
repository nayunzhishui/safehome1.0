export type ID = string;
export type ISODateTime = string;
export type ISODate = string;

export type UserRole = "parent" | "student" | "admin";
export type GoalStatus = "active" | "done" | "paused";
export type RiskLevel = "low" | "medium" | "high";
export type SupervisionStatus = "pending" | "replied" | "closed";

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
  risk_level: RiskLevel;
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
  enabled: boolean;
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
