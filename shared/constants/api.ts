export const API_BASE_PATH = "/api";

export const MOCK_USER_ID = "mock-parent";

export const API_ENDPOINTS = {
  healthz: "/healthz",
  readyz: "/readyz",
  goals: "/api/goals",
  diaries: "/api/diaries",
  emotionThermometer: "/api/emotion-thermometer",
  emotionThermometerDay: "/api/emotion-thermometer/day",
  feedbackGenerate: "/api/feedback/generate",
  cards: "/api/cards",
  cardsRecommend: "/api/cards/recommend",
  trainingPlan: "/api/training-plan",
  journeyToday: "/api/journey/today",
  feedbackLedger: "/api/feedback-ledger",
  feedbackLedgerSummary: "/api/feedback-ledger/summary",
  trainingPlanAssignment: "/api/training-plan/assignment",
  notificationConfig: "/api/notifications/config",
  notificationConsent: "/api/notifications/consent",
  courses: "/api/courses",
  courseDetailBase: "/api/courses/:id",
  programs: "/api/programs",
  programDetailBase: "/api/programs/:id",
  assessments: "/api/assessments",
  assessmentResults: "/api/assessment-results",
  assessmentProfilePositionBase: "/api/assessment-results/:id/profile-position",
  consent: "/api/consent",
  studentAssessment: "/api/student-assessment",
  profile: "/api/profile",
  profileStats: "/api/profile/stats",
  progressSummary: "/api/progress-summary",
  profileTrend: "/api/profile-trend",
  trainingEffectiveness: "/api/training-effectiveness",
  textAnalysisSummary: "/api/text-analysis/summary",
  showcaseAccess: "/api/showcase-access",
  profileResults: "/api/profile-results",
  messages: "/api/messages",
  messagesReadAll: "/api/messages/read-all",
  parentAssessment: "/api/parent-assessment",
  parentAssessments: "/api/parent-assessments",
  riskCheck: "/api/risk/check",
  riskReview: "/api/risk-review",
  modelInfo: "/api/model/info",
  checkins: "/api/checkins",
  weeklyReport: "/api/weekly-report",
  growthOverview: "/api/growth/overview",
  supervision: "/api/supervision",
  adminExport: "/api/admin/export",
  privacyConsentStatus: "/api/privacy/consent-status",
  privacyRevokeConsent: "/api/privacy/revoke-consent",
  privacyDeleteMyData: "/api/privacy/delete-my-data",
  privacyRequests: "/api/privacy/requests",
  privacyAdminRequests: "/api/privacy/admin/requests",
  privacyExportMyData: "/api/privacy/export-my-data",
  authRegister: "/api/auth/register",
  authLogin: "/api/auth/login",
  authCapabilities: "/api/auth/capabilities",
  authWechatLogin: "/api/auth/wechat-login",
  authPhoneLogin: "/api/auth/phone-login",
  authBindPhone: "/api/auth/bind-phone",
  authLogout: "/api/auth/logout",
  authMe: "/api/auth/me",
  authDataClaimPreview: "/api/auth/data-claim-preview",
  authDataClaim: "/api/auth/data-claim",
  contentReviewUpdate: "/api/content-review/update",
  contentGovernanceInventory: "/api/content-review/inventory",
  contentGovernanceVersions: "/api/content-review/versions",
  contentGovernanceReplay: "/api/content-review/replay",
  contentGovernanceActive: "/api/content-review/active",
  aiQaConfig: "/api/ai-qa/config",
  aiQaSessions: "/api/ai-qa/sessions",
  aiQaEvaluation: "/api/ai-qa/evaluation",
  aiQaReviewEvidence: "/api/ai-qa/review/evidence",
  aiQaKillSwitch: "/api/ai-qa/kill-switch",
  offlineBenchmarks: "/api/research/benchmarks",
  researchMethodology: "/api/research/methodology",
  securityControls: "/api/security",
  reliability: "/api/reliability",
  adminWorksheets: "/api/admin/worksheets",
  adminAssessmentResults: "/api/admin/assessment-results",
  familyCreateBindCode: "/api/family/create-bind-code",
  familyBindStudent: "/api/family/bind-student",
  familyMembers: "/api/family/members",
  familyUnbind: "/api/family/unbind",
  relationshipPilot: "/api/relationship-pilot",
  researchParticipants: "/api/research/participants",
  researchOperations: "/api/research/operations",
  researchQueues: "/api/research/queues",
  researchWorkItems: "/api/research/work-items",
  researchWorkItemMetrics: "/api/research/work-items/metrics",
  productEvents: "/api/product-events",
} as const;

export const API_ERROR_CODES = {
  unauthorized: "unauthorized",
  forbidden: "forbidden",
  notFound: "not_found",
  missingUserId: "missing_user_id",
  invalidDate: "invalid_date",
  invalidIntensityLevel: "invalid_intensity_level",
  briefTextTooLong: "brief_text_too_long",
  reviewRequired: "review_required",
  contentValidationFailed: "content_validation_failed",
  internalError: "internal_error",
} as const;

export const GOAL_STATUSES = ["active", "done", "paused"] as const;

export const RISK_LEVELS = ["low", "medium", "high"] as const;

export const ASSESSMENT_AUDIENCE_CLASSES = ["student", "parent", "adult", "family"] as const;

export const ASSESSMENT_REFLEX_NODES = [
  "integrated_profile",
  "awareness",
  "reaction",
  "acceptance",
  "fusion",
  "transformation",
  "behavior",
  "resource",
  "outcome",
  "reflection",
  "motivation",
  "relationship_support",
] as const;

export const ASSESSMENT_SENSITIVE_CATEGORIES = [
  "none",
  "screening_or_health",
  "personality",
  "parenting_stress",
  "health_lifestyle",
  "wellbeing",
  "relationship_exploration",
] as const;

export const SUPERVISION_STATUSES = ["pending", "replied", "closed"] as const;

export const PRIVACY_REQUEST_STATUSES = ["pending", "processing", "completed", "rejected", "cancelled"] as const;

export const PRIVACY_HANDLING_SCOPES = [
  "account_identity",
  "participant_records",
  "feedback_and_training",
  "messages_and_notifications",
  "relationship_pilot",
  "research_outputs",
] as const;

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
