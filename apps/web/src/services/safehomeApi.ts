import { API_ENDPOINTS } from "../../../../shared/constants/api";
import type {
  ApiResponse,
  AdminWorksheet,
  AdminWorksheetInput,
  AssessmentProfilePosition,
  AssessmentListItem,
  AssessmentResult,
  AssessmentResultInput,
  AssessmentWorksheet,
  CardRecommendResponse,
  Checkin,
  CheckinInput,
  ConsentInput,
  ConsentRecord,
  ContentReviewUpdateInput,
  ContentReviewUpdateResult,
  ContentGovernanceDiff,
  ContentGovernanceDraftInput,
  ContentGovernanceInventoryItem,
  ContentGovernanceVersion,
  ContentReplayCase,
  ContentReplayResult,
  ContentReviewDiscipline,
  DataClaimPreview,
  DataClaimResult,
  EmotionDiary,
  EmotionDiaryInput,
  FeedbackGenerateInput,
  FeedbackLedgerEntry,
  FeedbackLedgerInput,
  FeedbackLedgerSummary,
  FeedbackResult,
  Goal,
  GoalInput,
  GrowthOverview,
  ListResponse,
  ModelInfo,
  ParentAssessmentInput,
  ParentAssessmentPayload,
  ParentAssessmentResult,
  PrivacyRequest,
  PrivacyExecutionResult,
  PrivacyScopePreview,
  PrivacyHandlingScope,
  PrivacyReviewAction,
  PrivacyReviewDetail,
  PrivacyReviewRequest,
  ProfileVisuals,
  RelationshipPilotEnrollment,
  RelationshipScreeningReport,
  ResearchOperationsSnapshot,
  ResearchQueuePage,
  ResearchQueueType,
  ResearchWorkItemActionInput,
  ResearchWorkItemActionResult,
  ResearchWorkItemDetail,
  ResearchWorkItemMetrics,
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
  TodayJourney,
  UserMessage,
  WeeklyReport,
} from "../../../../shared/types/api";
import { getStoredAdminToken } from "./adminToken";
import type { AuthUser } from "./authState";
import { getStoredAuthUser, getToken } from "./authState";
import { clearAnonymousUserId, getAnonymousUserId } from "./userIdentity";

export interface SafeHomeApiClientOptions {
  baseUrl?: string;
  defaultUserId?: string;
}

export interface ResearchParticipantSummary {
  user_id: string;
  nickname?: string | null;
  role: string;
  last_activity_at?: string | null;
  assessment_count: number;
  diary_count: number;
  checkin_count: number;
  program_count: number;
  relationship_count: number;
  supervision_count: number;
  unread_message_count: number;
}

export interface ResearchParticipantDossier {
  participant: {
    user_id: string;
    nickname?: string | null;
    role: string;
    created_at?: string;
    updated_at?: string;
  };
  modules: Record<string, Array<Record<string, unknown>>>;
  audit_summary: { related_event_count: number };
  boundary_notice: string;
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

export function formatSafeHomeError(error: unknown, fallback: string): string {
  if (error instanceof SafeHomeApiError && error.status === 401 && error.code === "admin_unauthorized") {
    return "后台令牌缺失或无效。请使用当前部署环境提供的后台令牌。";
  }
  return error instanceof Error ? error.message : fallback;
}

export class SafeHomeApiClient {
  private readonly baseUrl: string;
  private readonly defaultUserId: string;

  constructor(options: SafeHomeApiClientOptions = {}) {
    this.baseUrl = options.baseUrl ?? import.meta.env.VITE_SAFEHOME_API_BASE_URL ?? "http://127.0.0.1:5050";
    this.defaultUserId = options.defaultUserId ?? getAnonymousUserId();
  }

  async healthz(): Promise<{ ok: true; service: string }> {
    return this.requestRaw(API_ENDPOINTS.healthz);
  }

  getShowcaseAccess(): Promise<{
    enabled: boolean;
    read_only_role_bypass: boolean;
    open_programs: boolean;
    open_training_cards: boolean;
    notice: string;
  }> {
    return this.requestData(API_ENDPOINTS.showcaseAccess);
  }

  getTextAnalysisSummary(): Promise<{
    items: Record<string, Record<string, unknown>>;
    raw_text_included: boolean;
    boundary_notice: string;
  }> {
    return this.requestData(API_ENDPOINTS.textAnalysisSummary);
  }

  async login(creds: { username: string; password: string }): Promise<{ token: string; user: AuthUser }> {
    const data = await this.requestData<{ token: string; user: AuthUser }>(API_ENDPOINTS.authLogin, {
      method: "POST",
      body: { ...creds, anonymous_id: this.defaultUserId },
    });
    clearAnonymousUserId();
    return data;
  }

  async register(creds: {
    username: string;
    password: string;
    role?: string;
    nickname?: string;
  }): Promise<{ token: string; user: AuthUser }> {
    const data = await this.requestData<{ token: string; user: AuthUser }>(API_ENDPOINTS.authRegister, {
      method: "POST",
      body: { ...creds, anonymous_id: this.defaultUserId },
    });
    clearAnonymousUserId();
    return data;
  }

  async getCurrentUser(): Promise<AuthUser> {
    const data = await this.requestData<{ user: AuthUser }>(API_ENDPOINTS.authMe);
    return data.user;
  }

  getDataClaimPreview(): Promise<DataClaimPreview> {
    return this.requestData<DataClaimPreview>(API_ENDPOINTS.authDataClaimPreview);
  }

  getTodayJourney(params: { user_id?: string } = {}): Promise<TodayJourney> {
    return this.requestData<TodayJourney>(this.withQuery(API_ENDPOINTS.journeyToday, this.withDefaultUserParam(params)));
  }

  getGrowthOverview(params: { user_id?: string } = {}): Promise<GrowthOverview> {
    return this.requestData<GrowthOverview>(this.withQuery(API_ENDPOINTS.growthOverview, this.withDefaultUserParam(params)));
  }

  createFeedbackLedgerEntry(input: FeedbackLedgerInput): Promise<FeedbackLedgerEntry> {
    return this.requestData<FeedbackLedgerEntry>(API_ENDPOINTS.feedbackLedger, {
      method: "POST",
      body: input,
    });
  }

  listFeedbackLedgerEntries(params: { source_type?: string; source_id?: string } = {}): Promise<ListResponse<FeedbackLedgerEntry>> {
    return this.requestData<ListResponse<FeedbackLedgerEntry>>(this.withQuery(API_ENDPOINTS.feedbackLedger, params));
  }

  getFeedbackLedgerSummary(userId: string): Promise<FeedbackLedgerSummary> {
    return this.requestData<FeedbackLedgerSummary>(this.withQuery(API_ENDPOINTS.feedbackLedgerSummary, { user_id: userId }));
  }

  claimAnonymousData(claimId: string): Promise<DataClaimResult> {
    return this.requestData<DataClaimResult>(API_ENDPOINTS.authDataClaim, {
      method: "POST",
      body: { claim_id: claimId, confirm: true },
    });
  }

  createGoal(input: GoalInput): Promise<Goal> {
    return this.requestData<Goal>(API_ENDPOINTS.goals, {
      method: "POST",
      body: this.withDefaultUser(input),
    });
  }

  listGoals(params: { user_id?: string; status?: string } = {}): Promise<ListResponse<Goal>> {
    return this.requestData<ListResponse<Goal>>(this.withQuery(API_ENDPOINTS.goals, this.withDefaultUserParam(params)));
  }

  createConsent(input: ConsentInput): Promise<ConsentRecord> {
    return this.requestData<ConsentRecord>(API_ENDPOINTS.consent, {
      method: "POST",
      body: this.withDefaultUser(input),
    });
  }

  listConsentRecords(params: { user_id?: string } = {}): Promise<ListResponse<ConsentRecord>> {
    return this.requestData<ListResponse<ConsentRecord>>(this.withQuery(API_ENDPOINTS.consent, this.withDefaultUserParam(params)));
  }

  createDiary(input: EmotionDiaryInput): Promise<EmotionDiary> {
    return this.requestData<EmotionDiary>(API_ENDPOINTS.diaries, {
      method: "POST",
      body: this.withDefaultUser(input),
    });
  }

  listDiaries(params: { user_id?: string; limit?: number } = {}, adminToken?: string): Promise<ListResponse<EmotionDiary>> {
    const query = adminToken ? params : this.withDefaultUserParam(params);
    return this.requestData<ListResponse<EmotionDiary>>(this.withQuery(API_ENDPOINTS.diaries, query), {
      headers: this.adminHeaders(adminToken),
    });
  }

  generateFeedback(input: FeedbackGenerateInput, adminToken?: string): Promise<FeedbackResult> {
    return this.requestData<FeedbackResult>(API_ENDPOINTS.feedbackGenerate, {
      method: "POST",
      body: this.withDefaultUser(input),
      headers: this.adminHeaders(adminToken),
    });
  }

  createProfile(input: StudentProfileInput): Promise<StudentProfileResult> {
    return this.requestData<StudentProfileResult>(API_ENDPOINTS.profile, {
      method: "POST",
      body: this.withDefaultUser(input),
    });
  }

  listProfileResults(
    params: { user_id?: string; round?: number; limit?: number } = {},
    adminToken?: string,
  ): Promise<ListResponse<StudentProfileRecord>> {
    return this.requestData<ListResponse<StudentProfileRecord>>(this.withQuery(API_ENDPOINTS.profileResults, params), {
      headers: this.adminHeaders(adminToken),
    });
  }

  getProfileResult(id: string, adminToken?: string): Promise<StudentProfileRecord> {
    if (adminToken) {
      return this.requestData<StudentProfileRecord>(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}`, {
        headers: this.adminHeaders(adminToken),
      });
    }
    return this.requestData<StudentProfileRecord>(
      this.withQuery(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}`, this.withDefaultUserParam({})),
    );
  }

  listProfileReviews(id: string, adminToken?: string): Promise<ListResponse<ProfileReview>> {
    return this.requestData<ListResponse<ProfileReview>>(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/reviews`, {
      headers: this.adminHeaders(adminToken),
    });
  }

  createProfileReview(id: string, input: ProfileReviewInput, adminToken?: string): Promise<ProfileReview> {
    return this.requestData<ProfileReview>(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/review`, {
      method: "POST",
      body: input,
      headers: this.adminHeaders(adminToken),
    });
  }

  checkRisk(input: { text?: string; free_text?: string; raw_text?: string; source?: string }): Promise<RiskCheckResult> {
    return this.requestData<RiskCheckResult>(API_ENDPOINTS.riskCheck, {
      method: "POST",
      body: input,
    });
  }

  listRiskReviews(params: { status?: string; limit?: number } = {}, adminToken?: string): Promise<ListResponse<RiskReviewRecord>> {
    return this.requestData<ListResponse<RiskReviewRecord>>(this.withQuery(API_ENDPOINTS.riskReview, params), {
      headers: this.adminHeaders(adminToken),
    });
  }

  updateRiskReview(id: string, input: RiskReviewInput, adminToken?: string): Promise<RiskReviewRecord> {
    return this.requestData<RiskReviewRecord>(`${API_ENDPOINTS.riskReview}/${encodeURIComponent(id)}/review`, {
      method: "POST",
      body: input,
      headers: this.adminHeaders(adminToken),
    });
  }

  getModelInfo(): Promise<ModelInfo> {
    return this.requestData<ModelInfo>(API_ENDPOINTS.modelInfo);
  }

  getStudentAssessment(): Promise<StudentAssessmentPayload> {
    return this.requestData<StudentAssessmentPayload>(API_ENDPOINTS.studentAssessment);
  }

  getProfileVisuals(id: string): Promise<ProfileVisuals> {
    return this.requestData<ProfileVisuals>(
      this.withQuery(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/visuals`, this.withDefaultUserParam({})),
    );
  }

  createProfileFollowup(
    id: string,
    input: { round_no?: number; fit?: string; task_done?: string; state_score?: number; text?: string },
  ): Promise<Record<string, unknown>> {
    return this.requestData<Record<string, unknown>>(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/followups`, {
      method: "POST",
      body: this.withDefaultUser(input),
    });
  }

  createProfileSandplay(
    id: string,
    input: { task_title?: string; scene: Record<string, unknown>; reflection_text?: string },
  ): Promise<Record<string, unknown>> {
    return this.requestData<Record<string, unknown>>(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/sandplay`, {
      method: "POST",
      body: this.withDefaultUser(input),
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
    return this.requestData<ParentAssessmentResult>(
      this.withQuery(`${API_ENDPOINTS.parentAssessments}/${encodeURIComponent(id)}`, this.withDefaultUserParam({})),
    );
  }

  createParentReportAction(id: string, actionKey: string): Promise<Record<string, unknown>> {
    return this.requestData<Record<string, unknown>>(`${API_ENDPOINTS.parentAssessments}/${encodeURIComponent(id)}/actions`, {
      method: "POST",
      body: this.withDefaultUser({ action_key: actionKey }),
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

  listAssessmentResults(params: { user_id?: string; page?: number; page_size?: number; limit?: number } = {}): Promise<ListResponse<AssessmentResult>> {
    return this.requestData<ListResponse<AssessmentResult>>(this.withQuery(API_ENDPOINTS.assessmentResults, this.withDefaultUserParam(params)));
  }

  listAdminAssessmentResults(
    params: { worksheet_id?: string; profile_model_id?: string; limit?: number } = {},
    adminToken?: string,
  ): Promise<ListResponse<AssessmentResult>> {
    return this.requestData<ListResponse<AssessmentResult>>(this.withQuery(API_ENDPOINTS.adminAssessmentResults, params), {
      headers: this.adminHeaders(adminToken),
    });
  }

  getAssessmentProfilePosition(
    id: string,
    params: { user_id?: string; model_id?: string } = {},
  ): Promise<AssessmentProfilePosition> {
    return this.requestData<AssessmentProfilePosition>(
      this.withQuery(`${API_ENDPOINTS.assessmentResults}/${encodeURIComponent(id)}/profile-position`, this.withDefaultUserParam(params)),
    );
  }

  listAssessments(params: { audience_class?: string; q?: string } = {}): Promise<ListResponse<AssessmentListItem> & { boundary_notice?: string }> {
    return this.requestData(this.withQuery(API_ENDPOINTS.assessments, params));
  }

  getAssessment(id: string): Promise<AssessmentWorksheet> {
    return this.requestData(`${API_ENDPOINTS.assessments}/${encodeURIComponent(id)}`);
  }

  createAssessmentResult(input: AssessmentResultInput): Promise<AssessmentResult> {
    return this.requestData(API_ENDPOINTS.assessmentResults, { method: "POST", body: input });
  }

  getRelationshipResearchDashboard(adminToken?: string): Promise<ListResponse<RelationshipPilotEnrollment> & { boundary_notice?: string }> {
    return this.requestData(`${API_ENDPOINTS.relationshipPilot}/researcher/dashboard`, {
      headers: this.adminHeaders(adminToken),
    });
  }

  listResearchParticipants(
    params: { q?: string; limit?: number } = {},
    adminToken?: string,
  ): Promise<ListResponse<ResearchParticipantSummary> & { scope: string; boundary_notice: string }> {
    return this.requestData(this.withQuery(API_ENDPOINTS.researchParticipants, params), {
      headers: this.adminHeaders(adminToken),
    });
  }

  getResearchParticipant(userId: string, adminToken?: string): Promise<ResearchParticipantDossier> {
    return this.requestData(`${API_ENDPOINTS.researchParticipants}/${encodeURIComponent(userId)}`, {
      headers: this.adminHeaders(adminToken),
    });
  }

  getResearchOperations(adminToken?: string): Promise<ResearchOperationsSnapshot> {
    return this.requestData(API_ENDPOINTS.researchOperations, {
      headers: this.adminHeaders(adminToken),
    });
  }

  getResearchQueue(
    queue: ResearchQueueType,
    params: { page?: number; page_size?: number } = {},
    adminToken?: string,
  ): Promise<ResearchQueuePage> {
    return this.requestData(this.withQuery(API_ENDPOINTS.researchQueues, { queue, ...params }), {
      headers: this.adminHeaders(adminToken),
    });
  }

  getResearchWorkItem(workItemId: string, adminToken?: string): Promise<ResearchWorkItemDetail> {
    return this.requestData(`${API_ENDPOINTS.researchWorkItems}/${encodeURIComponent(workItemId)}`, {
      headers: this.adminHeaders(adminToken),
    });
  }

  actOnResearchWorkItem(
    workItemId: string,
    input: ResearchWorkItemActionInput,
    adminToken?: string,
  ): Promise<ResearchWorkItemActionResult> {
    return this.requestData(`${API_ENDPOINTS.researchWorkItems}/${encodeURIComponent(workItemId)}/actions`, {
      method: "POST",
      headers: { ...this.adminHeaders(adminToken), "Idempotency-Key": input.idempotency_key },
      body: input,
    });
  }

  getResearchWorkItemMetrics(windowDays = 7, adminToken?: string): Promise<ResearchWorkItemMetrics> {
    return this.requestData(this.withQuery(API_ENDPOINTS.researchWorkItemMetrics, { window_days: windowDays }), {
      headers: this.adminHeaders(adminToken),
    });
  }

  listPrivacyRequests(params: { page?: number; page_size?: number; user_id?: string } = {}): Promise<ListResponse<PrivacyRequest>> {
    return this.requestData(this.withQuery(API_ENDPOINTS.privacyRequests, params));
  }

  cancelPrivacyRequest(requestId: string, reason: string, idempotencyKey: string): Promise<PrivacyRequest> {
    return this.requestData(`${API_ENDPOINTS.privacyRequests}/${encodeURIComponent(requestId)}/cancel`, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: { reason },
    });
  }

  appealPrivacyRequest(requestId: string, reason: string, idempotencyKey: string): Promise<PrivacyRequest> {
    return this.requestData(`${API_ENDPOINTS.privacyRequests}/${encodeURIComponent(requestId)}/appeal`, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: { reason },
    });
  }

  listPrivacyRequestsForReview(
    params: { status?: string; page?: number; page_size?: number } = {},
    adminToken?: string,
  ): Promise<ListResponse<PrivacyReviewRequest> & { boundary_notice: string }> {
    return this.requestData(this.withQuery(API_ENDPOINTS.privacyAdminRequests, params), {
      headers: this.adminHeaders(adminToken),
    });
  }

  getPrivacyRequestForReview(requestId: string, adminToken?: string): Promise<PrivacyReviewDetail> {
    return this.requestData(`${API_ENDPOINTS.privacyAdminRequests}/${encodeURIComponent(requestId)}`, {
      headers: this.adminHeaders(adminToken),
    });
  }

  transitionPrivacyRequest(
    requestId: string,
    input: { action: PrivacyReviewAction; scope: PrivacyHandlingScope[]; note: string; idempotency_key: string },
    adminToken?: string,
  ): Promise<PrivacyReviewDetail> {
    return this.requestData(`${API_ENDPOINTS.privacyAdminRequests}/${encodeURIComponent(requestId)}/transition`, {
      method: "POST",
      headers: { ...this.adminHeaders(adminToken), "Idempotency-Key": input.idempotency_key },
      body: input,
    });
  }

  previewPrivacyRequest(requestId: string, adminToken?: string): Promise<PrivacyScopePreview> {
    return this.requestData(`${API_ENDPOINTS.privacyAdminRequests}/${encodeURIComponent(requestId)}/preview`, {
      headers: this.adminHeaders(adminToken),
    });
  }

  approvePrivacyExecution(requestId: string, input: { scope_hash: string; policy_version: string; idempotency_key: string }, adminToken?: string) {
    return this.requestData(`${API_ENDPOINTS.privacyAdminRequests}/${encodeURIComponent(requestId)}/approvals`, {
      method: "POST",
      headers: { ...this.adminHeaders(adminToken), "Idempotency-Key": input.idempotency_key },
      body: input,
    });
  }

  executePrivacyRequest(requestId: string, input: { dry_run: boolean; expected_version: number; idempotency_key: string }, adminToken?: string): Promise<PrivacyExecutionResult> {
    return this.requestData(`${API_ENDPOINTS.privacyAdminRequests}/${encodeURIComponent(requestId)}/execute`, {
      method: "POST",
      headers: { ...this.adminHeaders(adminToken), "Idempotency-Key": input.idempotency_key },
      body: input,
    });
  }

  getRelationshipEnrollment(id: string, adminToken?: string): Promise<RelationshipPilotEnrollment> {
    return this.requestData(`${API_ENDPOINTS.relationshipPilot}/enrollments/${encodeURIComponent(id)}`, {
      headers: this.adminHeaders(adminToken),
    });
  }

  getRelationshipReport(id: string, adminToken?: string): Promise<RelationshipScreeningReport> {
    return this.requestData(`${API_ENDPOINTS.relationshipPilot}/reports/${encodeURIComponent(id)}`, {
      headers: this.adminHeaders(adminToken),
    });
  }

  confirmRelationshipReport(id: string, adminToken?: string): Promise<RelationshipScreeningReport> {
    return this.requestData(`${API_ENDPOINTS.relationshipPilot}/reports/${encodeURIComponent(id)}/confirm`, {
      method: "POST",
      headers: this.adminHeaders(adminToken),
    });
  }

  updateRelationshipReport(
    id: string,
    input: {
      version: string;
      profile_description?: string;
      personalized_interpretation?: string;
      suggested_assessment_questions?: string[];
      recommended_project_tasks?: string[];
      boundary_notice?: string;
    },
    adminToken?: string,
  ): Promise<RelationshipScreeningReport> {
    return this.requestData(`${API_ENDPOINTS.relationshipPilot}/reports/${encodeURIComponent(id)}`, {
      method: "PATCH",
      body: input,
      headers: this.adminHeaders(adminToken),
    });
  }

  sendRelationshipReport(id: string, adminToken?: string): Promise<UserMessage> {
    return this.requestData(`${API_ENDPOINTS.relationshipPilot}/reports/${encodeURIComponent(id)}/send`, {
      method: "POST",
      headers: this.adminHeaders(adminToken),
    });
  }

  createRelationshipResearchNote(id: string, note: string, adminToken?: string): Promise<Record<string, unknown>> {
    return this.requestData(`${API_ENDPOINTS.relationshipPilot}/enrollments/${encodeURIComponent(id)}/notes`, {
      method: "POST",
      body: { note },
      headers: this.adminHeaders(adminToken),
    });
  }

  createCheckin(input: CheckinInput): Promise<Checkin> {
    return this.requestData<Checkin>(API_ENDPOINTS.checkins, {
      method: "POST",
      body: this.withDefaultUser(input),
    });
  }

  listCheckins(params: { user_id?: string; completed?: boolean; page?: number; page_size?: number; limit?: number } = {}): Promise<ListResponse<Checkin>> {
    return this.requestData<ListResponse<Checkin>>(this.withQuery(API_ENDPOINTS.checkins, this.withDefaultUserParam(params)));
  }

  getWeeklyReport(params: { user_id?: string; week_start?: string } = {}): Promise<WeeklyReport> {
    return this.requestData<WeeklyReport>(this.withQuery(API_ENDPOINTS.weeklyReport, this.withDefaultUserParam(params)));
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

  updateContentReview(input: ContentReviewUpdateInput, adminToken?: string): Promise<ContentReviewUpdateResult> {
    return this.requestData<ContentReviewUpdateResult>(API_ENDPOINTS.contentReviewUpdate, {
      method: "POST",
      body: input,
      headers: this.adminHeaders(adminToken),
    });
  }

  listAdminWorksheets(adminToken?: string): Promise<ListResponse<AdminWorksheet>> {
    return this.requestData<ListResponse<AdminWorksheet>>(API_ENDPOINTS.adminWorksheets, {
      headers: this.adminHeaders(adminToken),
    });
  }

  createAdminWorksheet(input: AdminWorksheetInput, adminToken?: string): Promise<AdminWorksheet> {
    return this.requestData<AdminWorksheet>(API_ENDPOINTS.adminWorksheets, {
      method: "POST",
      body: input,
      headers: this.adminHeaders(adminToken),
    });
  }

  updateAdminWorksheet(id: string, input: AdminWorksheetInput, adminToken?: string): Promise<AdminWorksheet> {
    return this.requestData<AdminWorksheet>(`${API_ENDPOINTS.adminWorksheets}/${encodeURIComponent(id)}`, {
      method: "PUT",
      body: input,
      headers: this.adminHeaders(adminToken),
    });
  }

  disableAdminWorksheet(id: string, adminToken?: string): Promise<AdminWorksheet> {
    return this.requestData<AdminWorksheet>(`${API_ENDPOINTS.adminWorksheets}/${encodeURIComponent(id)}`, {
      method: "DELETE",
      headers: this.adminHeaders(adminToken),
    });
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
        headers: this.adminHeaders(params.adminToken),
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
      if (response.status === 401) {
        message = "后台令牌缺失或无效。请使用当前部署环境提供的后台令牌。";
      }
      throw new SafeHomeApiError(message, "export_error", response.status);
    }

    return response.blob();
  }

  private withDefaultUser<T extends object>(input: T): T & { user_id: string } {
    const userId = "user_id" in input ? (input as { user_id?: string }).user_id : undefined;
    return { ...input, user_id: userId ?? this.currentDefaultUserId() };
  }

  getContentGovernanceInventory(adminToken?: string): Promise<{ items: ContentGovernanceInventoryItem[]; missing_sources: string[]; import_policy: string }> {
    return this.requestData(API_ENDPOINTS.contentGovernanceInventory, { headers: this.adminHeaders(adminToken) });
  }

  registerContentGovernanceInventory(adminToken?: string): Promise<{ created: number; skipped: number; auto_approved: false }> {
    return this.requestData(`${API_ENDPOINTS.contentGovernanceInventory}/register`, { method: "POST", headers: this.adminHeaders(adminToken) });
  }

  listContentGovernanceVersions(params: { content_type?: string; item_id?: string } = {}, adminToken?: string): Promise<{ items: ContentGovernanceVersion[] }> {
    return this.requestData(this.withQuery(API_ENDPOINTS.contentGovernanceVersions, params), { headers: this.adminHeaders(adminToken) });
  }

  createContentGovernanceDraft(input: ContentGovernanceDraftInput, adminToken?: string): Promise<ContentGovernanceVersion> {
    return this.requestData(API_ENDPOINTS.contentGovernanceVersions, { method: "POST", body: input, headers: this.adminHeaders(adminToken) });
  }

  getContentGovernanceVersion(id: string, adminToken?: string): Promise<ContentGovernanceVersion> {
    return this.requestData(`${API_ENDPOINTS.contentGovernanceVersions}/${encodeURIComponent(id)}`, { headers: this.adminHeaders(adminToken) });
  }

  getContentGovernanceDiff(id: string, adminToken?: string): Promise<ContentGovernanceDiff> {
    return this.requestData(`${API_ENDPOINTS.contentGovernanceVersions}/${encodeURIComponent(id)}/diff`, { headers: this.adminHeaders(adminToken) });
  }

  submitContentGovernanceVersion(id: string, adminToken?: string): Promise<ContentGovernanceVersion> {
    return this.requestData(`${API_ENDPOINTS.contentGovernanceVersions}/${encodeURIComponent(id)}/submit`, { method: "POST", headers: this.adminHeaders(adminToken) });
  }

  reviewContentGovernanceVersion(id: string, input: { discipline: ContentReviewDiscipline; decision: "approved" | "rejected"; evidence_path: string; note?: string }, adminToken?: string): Promise<ContentGovernanceVersion> {
    return this.requestData(`${API_ENDPOINTS.contentGovernanceVersions}/${encodeURIComponent(id)}/reviews`, { method: "POST", body: input, headers: this.adminHeaders(adminToken) });
  }

  publishContentGovernanceVersion(id: string, input: { confirm_publish: true; expected_hash: string; dependency_impact_confirmed?: boolean; release_reason: string }, adminToken?: string): Promise<Record<string, unknown>> {
    return this.requestData(`${API_ENDPOINTS.contentGovernanceVersions}/${encodeURIComponent(id)}/publish`, { method: "POST", body: input, headers: this.adminHeaders(adminToken) });
  }

  changeContentGovernanceRelease(releaseId: string, action: "pause" | "retire" | "restore", input: { confirm_action: true; dependency_impact_confirmed?: boolean; reason?: string }, adminToken?: string): Promise<Record<string, unknown>> {
    return this.requestData(`/api/content-review/releases/${encodeURIComponent(releaseId)}/${action}`, { method: "POST", body: input, headers: this.adminHeaders(adminToken) });
  }

  replayContentGovernance(cases: ContentReplayCase[], adminToken?: string): Promise<ContentReplayResult> {
    return this.requestData(API_ENDPOINTS.contentGovernanceReplay, { method: "POST", body: { cases }, headers: this.adminHeaders(adminToken) });
  }

  private withDefaultUserParam<T extends object>(params: T): T & { user_id: string } {
    const userId = "user_id" in params ? (params as { user_id?: string }).user_id : undefined;
    return { ...params, user_id: userId ?? this.currentDefaultUserId() };
  }

  private currentDefaultUserId(): string {
    return getStoredAuthUser()?.id || this.defaultUserId;
  }

  private adminHeaders(adminToken?: string): Record<string, string> {
    const token = (adminToken || getStoredAdminToken()).trim();
    return token ? { "X-Admin-Token": token } : {};
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
    options: { method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE"; body?: unknown; headers?: Record<string, string> } = {},
  ): Promise<T> {
    const payload = await this.requestRaw<ApiResponse<T>>(path, options);
    if (!payload.ok) {
      throw new SafeHomeApiError(payload.error.message, payload.error.code, 400);
    }
    return payload.data;
  }

  private async requestRaw<T>(
    path: string,
    options: { method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE"; body?: unknown; headers?: Record<string, string> } = {},
  ): Promise<T> {
    const token = getToken();
    const authHeader: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
    const response = await fetch(this.absoluteUrl(path), {
      method: options.method ?? "GET",
      headers: { "Content-Type": "application/json", ...authHeader, ...(options.headers || {}) },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });

    const payload = await response.json();
    if (!response.ok) {
      const isAdminRequest = path.startsWith("/api/admin") || Boolean(options.headers?.["X-Admin-Token"]);
      const message =
        response.status === 401 && isAdminRequest
          ? "后台令牌缺失或无效。请使用当前部署环境提供的后台令牌。"
          : payload?.error?.message ?? (response.status === 401 ? "需要先登录或重新登录。" : "请求失败");
      const code = response.status === 401 && isAdminRequest ? "admin_unauthorized" : payload?.error?.code ?? "http_error";
      throw new SafeHomeApiError(message, code, response.status);
    }
    if (payload && typeof payload === "object" && payload.ok === false) {
      throw new SafeHomeApiError(payload.error?.message ?? "请求失败", payload.error?.code ?? "api_error", response.status);
    }
    return payload as T;
  }
}

export const safeHomeApi = new SafeHomeApiClient();
