import { API_ENDPOINTS, DEFAULT_USER_ID } from "../../../../shared/constants/api";
import type {
  ApiResponse,
  AssessmentResult,
  CardRecommendResponse,
  Checkin,
  CheckinInput,
  ConsentInput,
  ConsentRecord,
  EmotionDiary,
  EmotionDiaryInput,
  FeedbackGenerateInput,
  FeedbackResult,
  Goal,
  GoalInput,
  ListResponse,
  ModelInfo,
  ParentAssessmentInput,
  ParentAssessmentPayload,
  ParentAssessmentResult,
  ProfileVisuals,
  ProfileReview,
  ProfileReviewInput,
  RiskCheckResult,
  RiskReviewInput,
  RiskReviewRecord,
  StudentProfileInput,
  StudentAssessmentPayload,
  StudentProfileRecord,
  StudentProfileResult,
  SupervisionInput,
  SupervisionRequest,
  TrainingCard,
  WeeklyReport,
} from "../../../../shared/types/api";

export interface SafeHomeApiClientOptions {
  baseUrl?: string;
  defaultUserId?: string;
}

export class SafeHomeApiError extends Error {
  code: string;
  status: number;

  constructor(message: string, code: string, status: number) {
    super(message);
    this.name = "SafeHomeApiError";
    this.code = code;
    this.status = status;
  }
}

export class SafeHomeApiClient {
  private readonly baseUrl: string;
  private readonly defaultUserId: string;

  constructor(options: SafeHomeApiClientOptions = {}) {
    this.baseUrl = options.baseUrl ?? import.meta.env.VITE_SAFEHOME_API_BASE_URL ?? "http://127.0.0.1:5050";
    this.defaultUserId = options.defaultUserId ?? DEFAULT_USER_ID;
  }

  async healthz(): Promise<{ ok: true; service: string }> {
    return this.requestRaw(API_ENDPOINTS.healthz);
  }

  createGoal(input: GoalInput): Promise<Goal> {
    return this.requestData<Goal>(API_ENDPOINTS.goals, {
      method: "POST",
      body: this.withDefaultUser(input),
    });
  }

  listGoals(params: { user_id?: string; status?: string } = {}): Promise<ListResponse<Goal>> {
    return this.requestData<ListResponse<Goal>>(this.withQuery(API_ENDPOINTS.goals, params));
  }

  createConsent(input: ConsentInput): Promise<ConsentRecord> {
    return this.requestData<ConsentRecord>(API_ENDPOINTS.consent, {
      method: "POST",
      body: this.withDefaultUser(input),
    });
  }

  listConsentRecords(params: { user_id?: string } = {}): Promise<ListResponse<ConsentRecord>> {
    return this.requestData<ListResponse<ConsentRecord>>(this.withQuery(API_ENDPOINTS.consent, params));
  }

  createDiary(input: EmotionDiaryInput): Promise<EmotionDiary> {
    return this.requestData<EmotionDiary>(API_ENDPOINTS.diaries, {
      method: "POST",
      body: this.withDefaultUser(input),
    });
  }

  listDiaries(params: { user_id?: string; limit?: number } = {}): Promise<ListResponse<EmotionDiary>> {
    return this.requestData<ListResponse<EmotionDiary>>(this.withQuery(API_ENDPOINTS.diaries, params));
  }

  generateFeedback(input: FeedbackGenerateInput): Promise<FeedbackResult> {
    return this.requestData<FeedbackResult>(API_ENDPOINTS.feedbackGenerate, {
      method: "POST",
      body: this.withDefaultUser(input),
    });
  }

  createProfile(input: StudentProfileInput): Promise<StudentProfileResult> {
    return this.requestData<StudentProfileResult>(API_ENDPOINTS.profile, {
      method: "POST",
      body: this.withDefaultUser(input),
    });
  }

  listProfileResults(params: { user_id?: string; round?: number; limit?: number } = {}): Promise<ListResponse<StudentProfileRecord>> {
    return this.requestData<ListResponse<StudentProfileRecord>>(this.withQuery(API_ENDPOINTS.profileResults, params));
  }

  getProfileResult(id: string): Promise<StudentProfileRecord> {
    return this.requestData<StudentProfileRecord>(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}`);
  }

  listProfileReviews(id: string): Promise<ListResponse<ProfileReview>> {
    return this.requestData<ListResponse<ProfileReview>>(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/reviews`);
  }

  createProfileReview(id: string, input: ProfileReviewInput): Promise<ProfileReview> {
    return this.requestData<ProfileReview>(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/review`, {
      method: "POST",
      body: input,
    });
  }

  checkRisk(input: { text?: string; free_text?: string; raw_text?: string; source?: string }): Promise<RiskCheckResult> {
    return this.requestData<RiskCheckResult>(API_ENDPOINTS.riskCheck, {
      method: "POST",
      body: input,
    });
  }

  listRiskReviews(params: { status?: string; limit?: number } = {}): Promise<ListResponse<RiskReviewRecord>> {
    return this.requestData<ListResponse<RiskReviewRecord>>(this.withQuery(API_ENDPOINTS.riskReview, params));
  }

  updateRiskReview(id: string, input: RiskReviewInput): Promise<RiskReviewRecord> {
    return this.requestData<RiskReviewRecord>(`${API_ENDPOINTS.riskReview}/${encodeURIComponent(id)}/review`, {
      method: "POST",
      body: input,
    });
  }

  getModelInfo(): Promise<ModelInfo> {
    return this.requestData<ModelInfo>(API_ENDPOINTS.modelInfo);
  }

  getStudentAssessment(): Promise<StudentAssessmentPayload> {
    return this.requestData<StudentAssessmentPayload>(API_ENDPOINTS.studentAssessment);
  }

  getProfileVisuals(id: string): Promise<ProfileVisuals> {
    return this.requestData<ProfileVisuals>(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/visuals`);
  }

  createProfileFollowup(
    id: string,
    input: { round_no?: number; fit?: string; task_done?: string; state_score?: number; text?: string },
  ): Promise<Record<string, unknown>> {
    return this.requestData<Record<string, unknown>>(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/followups`, {
      method: "POST",
      body: input,
    });
  }

  createProfileSandplay(
    id: string,
    input: { task_title?: string; scene: Record<string, unknown>; reflection_text?: string },
  ): Promise<Record<string, unknown>> {
    return this.requestData<Record<string, unknown>>(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/sandplay`, {
      method: "POST",
      body: input,
    });
  }

  getParentAssessment(): Promise<ParentAssessmentPayload> {
    return this.requestData<ParentAssessmentPayload>(API_ENDPOINTS.parentAssessment);
  }

  createParentAssessment(input: ParentAssessmentInput): Promise<ParentAssessmentResult> {
    return this.requestData<ParentAssessmentResult>(API_ENDPOINTS.parentAssessments, {
      method: "POST",
      body: this.withDefaultUser(input),
    });
  }

  getParentAssessmentResult(id: string): Promise<ParentAssessmentResult> {
    return this.requestData<ParentAssessmentResult>(`${API_ENDPOINTS.parentAssessments}/${encodeURIComponent(id)}`);
  }

  createParentReportAction(id: string, actionKey: string): Promise<Record<string, unknown>> {
    return this.requestData<Record<string, unknown>>(`${API_ENDPOINTS.parentAssessments}/${encodeURIComponent(id)}/actions`, {
      method: "POST",
      body: { action_key: actionKey },
    });
  }

  listCards(): Promise<ListResponse<TrainingCard>> {
    return this.requestData<ListResponse<TrainingCard>>(API_ENDPOINTS.cards);
  }

  recommendCards(params: { tags?: string[]; limit?: number } = {}): Promise<CardRecommendResponse> {
    return this.requestData<CardRecommendResponse>(
      this.withQuery(API_ENDPOINTS.cardsRecommend, {
        tags: params.tags?.join(","),
        limit: params.limit,
      }),
    );
  }

  listAssessmentResults(params: { user_id?: string; limit?: number } = {}): Promise<ListResponse<AssessmentResult>> {
    return this.requestData<ListResponse<AssessmentResult>>(this.withQuery(API_ENDPOINTS.assessmentResults, params));
  }

  createCheckin(input: CheckinInput): Promise<Checkin> {
    return this.requestData<Checkin>(API_ENDPOINTS.checkins, {
      method: "POST",
      body: this.withDefaultUser(input),
    });
  }

  listCheckins(params: { user_id?: string; limit?: number } = {}): Promise<ListResponse<Checkin>> {
    return this.requestData<ListResponse<Checkin>>(this.withQuery(API_ENDPOINTS.checkins, params));
  }

  getWeeklyReport(params: { user_id?: string; week_start?: string } = {}): Promise<WeeklyReport> {
    return this.requestData<WeeklyReport>(this.withQuery(API_ENDPOINTS.weeklyReport, params));
  }

  createSupervision(input: SupervisionInput): Promise<SupervisionRequest> {
    return this.requestData<SupervisionRequest>(API_ENDPOINTS.supervision, {
      method: "POST",
      body: this.withDefaultUser(input),
    });
  }

  buildAdminExportUrl(params: { type?: string; user_id?: string; module_type?: string; confirm_high_risk?: boolean } = {}): string {
    return this.absoluteUrl(this.withQuery(API_ENDPOINTS.adminExport, params));
  }

  async downloadAdminExport(params: {
    type?: string;
    user_id?: string;
    module_type?: string;
    confirm_high_risk?: boolean;
    adminToken: string;
  }): Promise<Blob> {
    const response = await fetch(
      this.absoluteUrl(
        this.withQuery(API_ENDPOINTS.adminExport, {
          type: params.type,
          user_id: params.user_id,
          module_type: params.module_type,
          confirm_high_risk: params.confirm_high_risk ? "true" : undefined,
        }),
      ),
      {
        headers: { "X-Admin-Token": params.adminToken },
      },
    );

    if (!response.ok) {
      let message = "导出失败";
      try {
        const payload = (await response.json()) as ApiResponse<unknown>;
        if (!payload.ok) {
          message = payload.error.message;
        }
      } catch {
        message = `导出失败：HTTP ${response.status}`;
      }
      throw new SafeHomeApiError(message, "export_error", response.status);
    }

    return response.blob();
  }

  private withDefaultUser<T extends { user_id?: string }>(input: T): T {
    return { ...input, user_id: input.user_id ?? this.defaultUserId };
  }

  private withQuery(path: string, params: Record<string, string | number | boolean | undefined>): string {
    const search = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== "") {
        search.set(key, String(value));
      }
    });
    const query = search.toString();
    return query ? `${path}?${query}` : path;
  }

  private absoluteUrl(path: string): string {
    return `${this.baseUrl}${path}`;
  }

  private async requestData<T>(
    path: string,
    options: { method?: "GET" | "POST"; body?: unknown } = {},
  ): Promise<T> {
    const payload = await this.requestRaw<ApiResponse<T>>(path, options);
    if (!payload.ok) {
      throw new SafeHomeApiError(payload.error.message, payload.error.code, 200);
    }
    return payload.data;
  }

  private async requestRaw<T>(
    path: string,
    options: { method?: "GET" | "POST"; body?: unknown } = {},
  ): Promise<T> {
    const response = await fetch(this.absoluteUrl(path), {
      method: options.method ?? "GET",
      headers: { "Content-Type": "application/json" },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new SafeHomeApiError(payload?.error?.message ?? "请求失败", payload?.error?.code ?? "http_error", response.status);
    }
    return payload as T;
  }
}

export const safeHomeApi = new SafeHomeApiClient();
