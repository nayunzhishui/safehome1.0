export const API_BASE_PATH = "/api";

export const DEFAULT_USER_ID = "demo-parent";

export const API_ENDPOINTS = {
  healthz: "/healthz",
  goals: "/api/goals",
  diaries: "/api/diaries",
  feedbackGenerate: "/api/feedback/generate",
  cards: "/api/cards",
  cardsRecommend: "/api/cards/recommend",
  assessments: "/api/assessments",
  assessmentResults: "/api/assessment-results",
  consent: "/api/consent",
  studentAssessment: "/api/student-assessment",
  profile: "/api/profile",
  profileResults: "/api/profile-results",
  parentAssessment: "/api/parent-assessment",
  parentAssessments: "/api/parent-assessments",
  riskCheck: "/api/risk/check",
  riskReview: "/api/risk-review",
  modelInfo: "/api/model/info",
  checkins: "/api/checkins",
  weeklyReport: "/api/weekly-report",
  supervision: "/api/supervision",
  adminExport: "/api/admin/export",
} as const;

export const GOAL_STATUSES = ["active", "done", "paused"] as const;

export const RISK_LEVELS = ["low", "medium", "high"] as const;

export const SUPERVISION_STATUSES = ["pending", "replied", "closed"] as const;

export const FEEDBACK_TAGS = [
  "judgmental_language",
  "high_demand_language",
  "negative_attribution",
  "repeated_urging",
  "catastrophic_prediction",
] as const;

export const COMMON_PARENT_SCENES = [
  "作业拖延",
  "考试成绩",
  "睡前冲突",
  "手机使用",
  "亲子沟通",
] as const;

export const COMMON_PARENT_EMOTIONS = [
  "着急",
  "生气",
  "担心",
  "失望",
  "无力",
  "内疚",
] as const;

export const ADMIN_EXPORT_TYPES = [
  "goals",
  "diaries",
  "feedback",
  "checkins",
  "assessments",
  "profile",
  "student_profiles",
  "records",
  "student_followups",
  "sandplay",
  "parent_assessments",
  "raw_wide",
  "long",
  "codebook",
  "reports",
  "supervision",
  "cards",
] as const;

export const ETHICS_COPY = {
  nonDiagnostic: "本系统反馈仅用于自我理解和亲子沟通练习，不构成临床诊断。",
  supportiveBoundary: "反馈聚焦具体场景、情绪和可练习动作，不评价家长或孩子的人格。",
  highRisk: "如出现自伤、自杀、暴力或严重安全风险，请优先联系线下专业人员或紧急支持。",
} as const;
