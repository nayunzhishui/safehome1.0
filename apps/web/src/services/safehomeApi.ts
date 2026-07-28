import { API_ENDPOINTS } from "../../../../shared/constants/api";
import type {
  ApiResponse,
  AiQaAnswer,
  AiQaConfig,
  AiQaEvaluationReview,
  AiQaEvaluationRun,
  AiQaReviewEvidence,
  AiQaSession,
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
  ComputationContractPublicStatus,
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
  IdentityMergeWorkflow,
  IdentityStatus,
  EmotionDiary,
  EmotionDiaryInput,
  FeedbackGenerateInput,
  FeedbackLedgerEntry,
  FeedbackLedgerActionInput,
  FeedbackLedgerInput,
  FeedbackLedgerSummary,
  FeedbackResult,
  Goal,
  GoalInput,
  GrowthOverview,
  ListResponse,
  ModelInfo,
  AffectModelCandidateRegistry,
  GroupNetworkAnalysisInput,
  GroupNetworkAnalysisPolicy,
  GroupNetworkAnalysisReport,
  OfflineAdjudicationQueueItem,
  OfflineAgreementSummary,
  OfflineAnnotationGovernance,
  OfflineAnnotationInput,
  OfflineBlindCase,
  OfflineBenchmarkConfig,
  OfflineBenchmarkRun,
  OfflineDatasetCard,
  OfflineModelReviewQueueItem,
  OfflineModelMonitoringStatus,
  OfflineModelMonitorRun,
  OfflineModelReleaseGateRun,
  OfflineModelReleaseGateStatus,
  OfflineModelRuntimeControl,
  OfflineModelShadowRun,
  OfflineModelVersion,
  OfflineSplitReport,
  ResearchMethodologyCheck,
  ResearchMethodologyConfig,
  ResearchMethodologyEvidence,
  ResearchMethodologyPublicStatus,
  ResearchMethodologyRegistry,
  ResearchMethodologySimulation,
  ResearchMethodologyVersion,
  ResearchAnalysisArtifact,
  ResearchAnalysisCatalog,
  ResearchAnalysisJob,
  ResearchAnalysisJobList,
  ResearchAnalysisSnapshot,
  ResearchCapabilitySummary,
  ResearchDeliveryContent,
  ResearchDeliveryType,
  ResearchDeliveryWorkflow,
  ResearchScopeAssignment,
  ResearchScopeAssignmentInput,
  SecurityPublicStatus,
  SecurityScanResult,
  SecurityWorkbench,
  ReliabilityFeatureFlag,
  ReliabilityJob,
  ReliabilityPublicStatus,
  ReliabilitySloSnapshot,
  ReliabilityWorkbench,
  UXGovernancePublicStatus,
  UXGovernanceWorkbench,
  OperationsGovernanceWorkbench,
  OperationsIncident,
  OperationsMonitoringSnapshot,
  OperationsPublicStatus,
  OperationsReleasePackage,
  ParentAssessmentInput,
  ParentAssessmentPayload,
  ParentAssessmentResult,
  PrivacyRequest,
  PublicationCandidate,
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
  ResearchParticipantDossier,
  ResearchParticipantModuleKey,
  ResearchParticipantModulePage,
  ResearchParticipantPage,
  ResearchParticipantSummary,
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
  TherapeuticAssessmentAuthorization,
  TherapeuticAssessmentAuthorizationStatus,
  TherapeuticAssessmentCase,
  TherapeuticAssessmentCompetencyLevel,
  TherapeuticAssessmentEvidenceItem,
  TherapeuticAssessmentResearcherDraft,
  TherapeuticAssessmentResearcherWorkbench,
  TherapeuticAssessmentDataItem,
  TherapeuticAssessmentParticipantDraft,
  TherapeuticAssessmentParticipantStep,
  TherapeuticAssessmentResponsibilityChain,
  TherapeuticAssessmentSafetyEvent,
  TherapeuticAssessmentSafetyStatus,
  TherapeuticAssessmentFeedbackVersion,
  TherapeuticAssessmentLifecycle,
  TherapeuticAssessmentLifecycleMetrics,
  TherapeuticAssessmentProductionGate,
  TherapeuticAssessmentQualityDimension,
  TherapeuticAssessmentQualityIncident,
  TherapeuticAssessmentQualityReview,
  TherapeuticAssessmentReleaseEvidence,
  TherapeuticAssessmentQualityRuntime,
  TherapeuticAssessmentProductionContract,
  TherapeuticAssessmentDutyShift,
  TherapeuticAssessmentQueueRuntime,
  TherapeuticAssessmentQueueType,
  TherapeuticAssessmentWorkQueueItem,
  TherapeuticAssessmentServiceLevelStatus,
  TherapeuticAssessmentTransitionInput,
  TherapeuticAssessmentTaskCode,
  SupervisionRequest,
  TrainingCard,
  TrainingPlan,
  RecommendationSnapshot,
  TodayJourney,
  UserMessage,
  WeeklyReport,
} from "../../../../shared/types/api";
import { getStoredAdminToken } from "./adminToken";
import type { AuthUser } from "./authState";
import { getStoredAuthUser, getToken } from "./authState";
import { clearAnonymousUserId, getAnonymousUserId } from "./userIdentity";

export type { ResearchParticipantDossier, ResearchParticipantModuleKey, ResearchParticipantModulePage, ResearchParticipantSummary } from "../../../../shared/types/api";

export interface SafeHomeApiClientOptions {
  baseUrl?: string;
  defaultUserId?: string;
}

export class SafeHomeApiError extends Error {
  code: string;
  status: number;
  requestId: string;
  clientVersion: string;
  serviceVersion: string;
  buildId: string;
  occurredAt: string;

  constructor(
    message: string,
    code: string,
    status: number,
    diagnostic: Partial<Pick<SafeHomeApiError, "requestId" | "clientVersion" | "serviceVersion" | "buildId" | "occurredAt">> = {},
  ) {
    super(message);
    this.name = "SafeHomeApiError";
    this.code = code;
    this.status = status;
    this.requestId = diagnostic.requestId || "";
    this.clientVersion = diagnostic.clientVersion || "web-dev";
    this.serviceVersion = diagnostic.serviceVersion || "";
    this.buildId = diagnostic.buildId || "";
    this.occurredAt = diagnostic.occurredAt || new Date().toISOString();
  }
}

export function formatSafeHomeErrorDiagnostic(error: SafeHomeApiError): string {
  return [
    `请求编号：${error.requestId || "未返回"}`,
    `客户端版本：${error.clientVersion || "未知"}`,
    `服务版本：${error.serviceVersion || "未知"}`,
    `构建编号：${error.buildId || "未知"}`,
    `发生时间：${error.occurredAt}`,
  ].join("\n");
}

export async function copySafeHomeErrorDiagnostic(error: SafeHomeApiError): Promise<void> {
  const text = formatSafeHomeErrorDiagnostic(error);
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  const copied = document.execCommand("copy");
  textarea.remove();
  if (!copied) throw new Error("复制诊断信息失败");
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
  private readonly clientVersion: string;

  constructor(options: SafeHomeApiClientOptions = {}) {
    this.baseUrl = options.baseUrl ?? import.meta.env.VITE_SAFEHOME_API_BASE_URL ?? "http://127.0.0.1:5050";
    this.defaultUserId = options.defaultUserId ?? getAnonymousUserId();
    this.clientVersion = import.meta.env.VITE_SAFEHOME_CLIENT_VERSION ?? "web-dev";
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

  async changePassword(input: {
    current_password: string;
    new_password: string;
  }): Promise<{ token: string; user: AuthUser; sessions_revoked: boolean }> {
    return this.requestData(API_ENDPOINTS.authChangePassword, {
      method: "POST",
      body: input,
    });
  }

  async getCurrentUser(): Promise<AuthUser> {
    const data = await this.requestData<{ user: AuthUser }>(API_ENDPOINTS.authMe);
    return data.user;
  }

  getDataClaimPreview(): Promise<DataClaimPreview> {
    return this.requestData<DataClaimPreview>(API_ENDPOINTS.authDataClaimPreview);
  }

  getIdentityStatus(): Promise<IdentityStatus> {
    return this.requestData<IdentityStatus>(API_ENDPOINTS.authIdentityStatus);
  }

  unbindIdentity(identityType: "wechat" | "phone", expectedAuthEpoch: number): Promise<IdentityStatus> {
    return this.requestData<IdentityStatus>(API_ENDPOINTS.authIdentityUnbind, {
      method: "POST",
      body: {
        identity_type: identityType,
        expected_auth_epoch: expectedAuthEpoch,
        confirm: true,
      },
    });
  }

  getTodayJourney(params: { user_id?: string } = {}): Promise<TodayJourney> {
    return this.requestData<TodayJourney>(this.withQuery(API_ENDPOINTS.journeyToday, this.withDefaultUserParam(params)));
  }

  getTrainingPlan(params: { user_id?: string } = {}): Promise<TrainingPlan> {
    return this.requestData<TrainingPlan>(this.withQuery(API_ENDPOINTS.trainingPlan, this.withDefaultUserParam(params)));
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

  applyFeedbackLedgerAction(entryId: string, input: FeedbackLedgerActionInput): Promise<FeedbackLedgerEntry> {
    return this.requestData<FeedbackLedgerEntry>(`${API_ENDPOINTS.feedbackLedger}/${encodeURIComponent(entryId)}/actions`, {
      method: "POST",
      body: input,
      headers: input.idempotency_key ? { "Idempotency-Key": input.idempotency_key } : undefined,
    });
  }

  replayTrainingRecommendation(input: { source_result_id: string; strategy_version: string; idempotency_key: string }): Promise<RecommendationSnapshot> {
    return this.requestData<RecommendationSnapshot>(API_ENDPOINTS.trainingRecommendationReplay, {
      method: "POST",
      body: input,
      headers: { "Idempotency-Key": input.idempotency_key },
    });
  }

  getTrainingRecommendationSnapshot(snapshotId: string): Promise<RecommendationSnapshot> {
    return this.requestData<RecommendationSnapshot>(`${API_ENDPOINTS.trainingRecommendationSnapshots}/${encodeURIComponent(snapshotId)}`);
  }

  listFeedbackLedgerEntries(params: { source_type?: string; source_id?: string } = {}): Promise<ListResponse<FeedbackLedgerEntry>> {
    return this.requestData<ListResponse<FeedbackLedgerEntry>>(this.withQuery(API_ENDPOINTS.feedbackLedger, params));
  }

  getFeedbackLedgerSummary(userId: string): Promise<FeedbackLedgerSummary> {
    return this.requestData<FeedbackLedgerSummary>(this.withQuery(API_ENDPOINTS.feedbackLedgerSummary, { user_id: userId }));
  }

  claimAnonymousData(claimId: string, expectedVersion = 0): Promise<DataClaimResult> {
    return this.requestData<DataClaimResult>(API_ENDPOINTS.authDataClaim, {
      method: "POST",
      headers: { "Idempotency-Key": `data-claim-${claimId}` },
      body: { claim_id: claimId, confirm: true, expected_version: expectedVersion },
    });
  }

  createIdentityMergeCandidate(input: {
    source_user_id: string;
    target_user_id: string;
    reason_code: string;
    idempotency_key: string;
  }): Promise<IdentityMergeWorkflow> {
    return this.requestData<IdentityMergeWorkflow>(API_ENDPOINTS.authAccountMerges, {
      method: "POST",
      headers: { "Idempotency-Key": input.idempotency_key },
      body: {
        source_user_id: input.source_user_id,
        target_user_id: input.target_user_id,
        reason_code: input.reason_code,
      },
    });
  }

  getIdentityMergeWorkflow(id: string): Promise<IdentityMergeWorkflow> {
    return this.requestData<IdentityMergeWorkflow>(`${API_ENDPOINTS.authAccountMerges}/${encodeURIComponent(id)}`);
  }

  actOnIdentityMerge(
    id: string,
    action: "confirm" | "execute" | "verify" | "rollback",
    expectedVersion: number,
    idempotencyKey: string,
  ): Promise<IdentityMergeWorkflow> {
    return this.requestData<IdentityMergeWorkflow>(
      `${API_ENDPOINTS.authAccountMerges}/${encodeURIComponent(id)}/${action}`,
      {
        method: "POST",
        headers: { "Idempotency-Key": idempotencyKey },
        body: {
          expected_version: expectedVersion,
          confirm: action === "confirm" || action === "rollback",
        },
      },
    );
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
      headers: input.client_submission_id ? { "Idempotency-Key": input.client_submission_id } : undefined,
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
      headers: input.client_submission_id ? { "Idempotency-Key": input.client_submission_id } : undefined,
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
    return this.requestData(API_ENDPOINTS.assessmentResults, {
      method: "POST",
      body: input,
      headers: input.client_submission_id ? { "Idempotency-Key": input.client_submission_id } : undefined,
    });
  }

  getRelationshipResearchDashboard(adminToken?: string): Promise<ListResponse<RelationshipPilotEnrollment> & { boundary_notice?: string }> {
    return this.requestData(`${API_ENDPOINTS.relationshipPilot}/researcher/dashboard`, {
      headers: this.adminHeaders(adminToken),
    });
  }

  getResearchCapabilities(): Promise<ResearchCapabilitySummary> {
    return this.requestData(`${API_ENDPOINTS.researchAccess}/capabilities`);
  }

  createResearchDelivery(
    input: { enrollment_id: string; delivery_type: ResearchDeliveryType; title: string; content: ResearchDeliveryContent },
    idempotencyKey: string,
  ): Promise<ResearchDeliveryWorkflow> {
    return this.requestData(API_ENDPOINTS.researchDeliveries, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: input,
    });
  }

  saveResearchDelivery(
    id: string,
    input: { expected_version: number; title: string; content: ResearchDeliveryContent },
    idempotencyKey: string,
  ): Promise<ResearchDeliveryWorkflow> {
    return this.requestData(`${API_ENDPOINTS.researchDeliveries}/${encodeURIComponent(id)}`, {
      method: "PATCH",
      headers: { "Idempotency-Key": idempotencyKey },
      body: input,
    });
  }

  runResearchDeliveryAction(
    id: string,
    action: "preview" | "confirm" | "send" | "withdraw",
    expectedVersion: number,
    idempotencyKey: string,
    extra: Record<string, unknown> = {},
  ): Promise<ResearchDeliveryWorkflow> {
    return this.requestData(`${API_ENDPOINTS.researchDeliveries}/${encodeURIComponent(id)}/${action}`, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: { expected_version: expectedVersion, ...extra },
    });
  }

  listResearchDeliveries(enrollmentId: string): Promise<ListResponse<ResearchDeliveryWorkflow>> {
    return this.requestData(this.withQuery(API_ENDPOINTS.researchDeliveries, { enrollment_id: enrollmentId }));
  }

  listResearchAssignments(enrollmentId = ""): Promise<ListResponse<ResearchScopeAssignment>> {
    return this.requestData(
      this.withQuery(`${API_ENDPOINTS.researchAccess}/assignments`, { enrollment_id: enrollmentId || undefined }),
    );
  }

  createResearchAssignment(input: ResearchScopeAssignmentInput): Promise<ResearchScopeAssignment> {
    return this.requestData(`${API_ENDPOINTS.researchAccess}/assignments`, {
      method: "POST",
      headers: { "Idempotency-Key": input.idempotency_key },
      body: input,
    });
  }

  claimResearchEnrollment(enrollmentId: string, idempotencyKey: string): Promise<ResearchScopeAssignment> {
    return this.requestData(
      `${API_ENDPOINTS.researchAccess}/enrollments/${encodeURIComponent(enrollmentId)}/claim`,
      { method: "POST", headers: { "Idempotency-Key": idempotencyKey } },
    );
  }

  listResearchParticipants(
    params: { q?: string; limit?: number; page?: number; page_size?: number } = {},
    adminToken?: string,
  ): Promise<ResearchParticipantPage> {
    return this.requestData(this.withQuery(API_ENDPOINTS.researchParticipants, params), {
      headers: this.adminHeaders(adminToken),
    });
  }

  getResearchParticipant(userId: string, adminToken?: string): Promise<ResearchParticipantDossier> {
    return this.requestData(`${API_ENDPOINTS.researchParticipants}/${encodeURIComponent(userId)}`, {
      headers: this.adminHeaders(adminToken),
    });
  }

  getResearchParticipantModule(
    userId: string,
    moduleKey: ResearchParticipantModuleKey,
    params: { page?: number; page_size?: number; date_from?: string; date_to?: string; type?: string; status?: string; batch?: string } = {},
    adminToken?: string,
  ): Promise<ResearchParticipantModulePage> {
    return this.requestData(
      this.withQuery(`${API_ENDPOINTS.researchParticipants}/${encodeURIComponent(userId)}/modules/${encodeURIComponent(moduleKey)}`, params),
      { headers: this.adminHeaders(adminToken) },
    );
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

  getAiQaConfig(): Promise<AiQaConfig> {
    return this.requestData(API_ENDPOINTS.aiQaConfig);
  }

  listAiQaSessions(): Promise<ListResponse<AiQaSession>> {
    return this.requestData(API_ENDPOINTS.aiQaSessions);
  }

  createAiQaSession(): Promise<AiQaSession> {
    return this.requestData(API_ENDPOINTS.aiQaSessions, { method: "POST", body: { synthetic_data: true, research_use_allowed: false } });
  }

  getAiQaSession(id: string): Promise<AiQaSession> {
    return this.requestData(`${API_ENDPOINTS.aiQaSessions}/${encodeURIComponent(id)}`);
  }

  deleteAiQaSession(id: string): Promise<{ id: string; status: "deleted"; idempotent: boolean }> {
    return this.requestData(`${API_ENDPOINTS.aiQaSessions}/${encodeURIComponent(id)}`, { method: "DELETE" });
  }

  sendAiQaMessage(sessionId: string, text: string, fakeMode = "normal"): Promise<AiQaAnswer> {
    return this.requestData(`${API_ENDPOINTS.aiQaSessions}/${encodeURIComponent(sessionId)}/messages`, { method: "POST", body: { text, synthetic_data: true, fake_mode: fakeMode } });
  }

  saveAiQaFeedback(messageId: string, evaluation: "helpful" | "neutral" | "does_not_match" | "uncomfortable", note?: string): Promise<Record<string, unknown>> {
    return this.requestData(`/api/ai-qa/messages/${encodeURIComponent(messageId)}/feedback`, { method: "POST", body: { evaluation, note, research_use_allowed: false } });
  }

  runAiQaEvaluation(): Promise<AiQaEvaluationRun> {
    return this.requestData(`${API_ENDPOINTS.aiQaEvaluation}/run`, { method: "POST" });
  }

  getAiQaReviewEvidence(): Promise<AiQaReviewEvidence> {
    return this.requestData(API_ENDPOINTS.aiQaReviewEvidence);
  }

  reviewAiQaEvaluation(runId: string, input: { decision: AiQaEvaluationReview["decision"]; evidence_path: string; note?: string }): Promise<AiQaEvaluationReview> {
    return this.requestData(`${API_ENDPOINTS.aiQaEvaluation}/${encodeURIComponent(runId)}/reviews`, { method: "POST", body: input });
  }

  activateAiQaKillSwitch(reason: string): Promise<Record<string, unknown>> {
    return this.requestData(API_ENDPOINTS.aiQaKillSwitch, { method: "POST", body: { killed: true, reason } });
  }

  getOfflineBenchmarkConfig(): Promise<OfflineBenchmarkConfig> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/config`);
  }

  getOfflineModelCandidates(): Promise<AffectModelCandidateRegistry> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/model-candidates`);
  }

  getGroupNetworkAnalysisPolicy(): Promise<GroupNetworkAnalysisPolicy> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/network-policy`);
  }

  analyzeGroupNetwork(input: GroupNetworkAnalysisInput): Promise<GroupNetworkAnalysisReport> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/network/analyze`, {
      method: "POST",
      body: input,
    });
  }

  syncOfflineDatasetCards(): Promise<{ registry_version: string; card_count: number; external_downloaded: false }> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/dataset-cards/sync`, { method: "POST" });
  }

  listOfflineDatasetCards(): Promise<ListResponse<OfflineDatasetCard>> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/dataset-cards`);
  }

  listOfflineBenchmarkRuns(): Promise<ListResponse<OfflineBenchmarkRun>> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/runs`);
  }

  runOfflineBenchmark(type: "affect" | "network"): Promise<OfflineBenchmarkRun> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/runs/${type}`, { method: "POST" });
  }

  registerOfflineModelVersion(codeCommit: string): Promise<OfflineModelVersion> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/model-versions`, {
      method: "POST",
      body: { code_commit: codeCommit },
    });
  }

  listOfflineModelVersions(): Promise<ListResponse<OfflineModelVersion> & { boundary_notice: string }> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/model-versions`);
  }

  runOfflineModelShadow(modelVersionId: string): Promise<OfflineModelShadowRun> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/shadow-runs`, {
      method: "POST",
      body: { model_version_id: modelVersionId },
    });
  }

  replayOfflineModelShadow(runId: string, modelVersionId: string): Promise<OfflineModelShadowRun> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/shadow-runs/${encodeURIComponent(runId)}/replay`, {
      method: "POST",
      body: { model_version_id: modelVersionId },
    });
  }

  listOfflineModelShadowRuns(): Promise<ListResponse<OfflineModelShadowRun>> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/shadow-runs`);
  }

  listOfflineModelReviewQueue(): Promise<ListResponse<OfflineModelReviewQueueItem> & { raw_text_included: false; participant_identifiers_included: false }> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/shadow-review-queue`);
  }

  getOfflineModelMonitoring(): Promise<OfflineModelMonitoringStatus> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/monitoring`);
  }

  runOfflineModelMonitorDrill(scenario: string, modelVersionId?: string): Promise<OfflineModelMonitorRun & { runtime_control: OfflineModelRuntimeControl; boundary_notice: string }> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/monitoring/drills`, {
      method: "POST",
      body: { scenario, model_version_id: modelVersionId },
    });
  }

  applyOfflineModelRuntimeAction(action: "model_rollback" | "threshold_rollback" | "readonly_degrade" | "full_disable", input: { reason: string; model_version_id?: string; threshold_hash?: string }): Promise<OfflineModelRuntimeControl> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/runtime-actions/${action}`, {
      method: "POST",
      body: input,
    });
  }

  getOfflineModelReleaseGate(): Promise<OfflineModelReleaseGateStatus> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/release-gate`);
  }

  buildOfflineModelReleaseGate(): Promise<OfflineModelReleaseGateRun & {
    boundary_notice: string;
    temporary_showcase_privilege_counts_as_approval: false;
    simulated_agent_counts_as_human_signoff: false;
  }> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/release-gate/packages`, {
      method: "POST",
    });
  }

  getOfflineAgreement(): Promise<OfflineAgreementSummary> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/agreement`);
  }

  listOfflineBlindCases(offset = 0, limit = 12): Promise<{ items: OfflineBlindCase[]; offset: number; limit: number; total: 240; blind: true; generator_labels_included: false }> {
    return this.requestData(this.withQuery(`${API_ENDPOINTS.offlineBenchmarks}/cases`, { offset, limit }));
  }

  getOfflineAnnotationGovernance(): Promise<OfflineAnnotationGovernance> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/annotation-governance`);
  }

  saveOfflineAnnotation(caseId: string, input: OfflineAnnotationInput): Promise<Record<string, unknown>> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/cases/${encodeURIComponent(caseId)}/annotations`, { method: "POST", body: input });
  }

  listOfflineAdjudicationQueue(): Promise<{ items: OfflineAdjudicationQueueItem[]; total: number; blind_identity: true }> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/adjudication-queue`);
  }

  adjudicateOfflineCase(caseId: string, input: OfflineAnnotationInput & { rationale: string; manual_clause: string }): Promise<Record<string, unknown>> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/cases/${encodeURIComponent(caseId)}/adjudications`, { method: "POST", body: input });
  }

  getOfflineSplitReport(): Promise<OfflineSplitReport> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/split-report`);
  }

  reviewOfflineBenchmark(runId: string, input: { decision: "engineering_reviewed" | "changes_required" | "stop"; evidence_path: string; notes?: string }): Promise<Record<string, unknown>> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/runs/${encodeURIComponent(runId)}/reviews`, { method: "POST", body: input });
  }

  disableOfflineBenchmarks(reason: string): Promise<Record<string, unknown>> {
    return this.requestData(`${API_ENDPOINTS.offlineBenchmarks}/disable`, { method: "POST", body: { reason } });
  }

  getResearchMethodologyPublicStatus(): Promise<ResearchMethodologyPublicStatus> {
    return this.requestData(`${API_ENDPOINTS.researchMethodology}/public-status`);
  }

  getComputationContractPublicStatus(): Promise<ComputationContractPublicStatus> {
    return this.requestData(`${API_ENDPOINTS.computationContract}/public-status`);
  }

  getResearchMethodologyConfig(): Promise<ResearchMethodologyConfig> {
    return this.requestData(`${API_ENDPOINTS.researchMethodology}/config`);
  }

  getResearchMethodologyRegistry(): Promise<ResearchMethodologyRegistry> {
    return this.requestData(`${API_ENDPOINTS.researchMethodology}/registry`);
  }

  listResearchMethodologyVersions(): Promise<ListResponse<ResearchMethodologyVersion>> {
    return this.requestData(`${API_ENDPOINTS.researchMethodology}/versions`);
  }

  syncResearchMethodologyRegistry(): Promise<ResearchMethodologyVersion> {
    return this.requestData(`${API_ENDPOINTS.researchMethodology}/versions/sync`, { method: "POST" });
  }

  runResearchMethodologyChecks(versionId?: string): Promise<ResearchMethodologyCheck> {
    return this.requestData(`${API_ENDPOINTS.researchMethodology}/checks/run`, { method: "POST", body: { version_id: versionId } });
  }

  runResearchMethodologySimulation(versionId?: string): Promise<ResearchMethodologySimulation> {
    return this.requestData(`${API_ENDPOINTS.researchMethodology}/simulations/run`, { method: "POST", body: { version_id: versionId } });
  }

  getResearchMethodologyEvidence(): Promise<ResearchMethodologyEvidence> {
    return this.requestData(`${API_ENDPOINTS.researchMethodology}/evidence`);
  }

  createResearchMethodologyEvidencePackage(versionId?: string): Promise<Record<string, unknown>> {
    return this.requestData(`${API_ENDPOINTS.researchMethodology}/evidence-packages`, { method: "POST", body: { version_id: versionId } });
  }

  disableResearchMethodology(reason: string): Promise<Record<string, unknown>> {
    return this.requestData(`${API_ENDPOINTS.researchMethodology}/disable`, { method: "POST", body: { reason } });
  }

  listResearchAnalysisJobs(status = ""): Promise<ResearchAnalysisJobList> {
    return this.requestData(this.withQuery(`${API_ENDPOINTS.researchAnalysis}/jobs`, { status }));
  }

  getResearchAnalysisJob(jobId: string): Promise<ResearchAnalysisJob> {
    return this.requestData(`${API_ENDPOINTS.researchAnalysis}/jobs/${encodeURIComponent(jobId)}`);
  }

  createResearchAnalysisSnapshot(input: {
    participant_user_id: string;
    enrollment_id: string;
    purpose_code: string;
    expires_in_days: number;
    source_refs: Array<{ source_type: string; source_id: string; source_version?: string; source_hash: string }>;
  }): Promise<ResearchAnalysisSnapshot> {
    return this.requestData(`${API_ENDPOINTS.researchAnalysis}/snapshots`, { method: "POST", body: input });
  }

  createResearchAnalysisJob(input: {
    snapshot_id: string;
    analysis_type: string;
    analysis_version: string;
    resource_hash: string;
    parameters: Record<string, unknown>;
    idempotency_key: string;
  }): Promise<ResearchAnalysisJob> {
    return this.requestData(`${API_ENDPOINTS.researchAnalysis}/jobs`, {
      method: "POST",
      headers: { "Idempotency-Key": input.idempotency_key },
      body: {
        snapshot_id: input.snapshot_id,
        analysis_type: input.analysis_type,
        analysis_version: input.analysis_version,
        resource_hash: input.resource_hash,
        parameters: input.parameters,
      },
    });
  }

  getResearchAnalysisCatalog(): Promise<ResearchAnalysisCatalog> {
    return this.requestData(`${API_ENDPOINTS.researchAnalysis}/catalog`);
  }

  getResearchAnalysisArtifact(artifactId: string): Promise<ResearchAnalysisArtifact> {
    return this.requestData(`${API_ENDPOINTS.researchAnalysis}/artifacts/${encodeURIComponent(artifactId)}`);
  }

  getSecurityPublicStatus(): Promise<SecurityPublicStatus> {
    return this.requestData(`${API_ENDPOINTS.securityControls}/public-status`);
  }

  getSecurityWorkbench(): Promise<SecurityWorkbench> {
    return this.requestData(`${API_ENDPOINTS.securityControls}/workbench`);
  }

  runSecurityScan(): Promise<SecurityScanResult> {
    return this.requestData(`${API_ENDPOINTS.securityControls}/scans`, { method: "POST" });
  }

  updateAccountStatus(userId: string, input: { status: "active" | "disabled"; reason_code: string; expected_auth_epoch?: number }): Promise<Record<string, unknown>> {
    return this.requestData(`${API_ENDPOINTS.securityControls}/accounts/${encodeURIComponent(userId)}/status`, { method: "PATCH", body: input });
  }

  resolveSecurityEvent(eventId: string): Promise<Record<string, unknown>> {
    return this.requestData(`${API_ENDPOINTS.securityControls}/events/${encodeURIComponent(eventId)}/resolve`, { method: "POST" });
  }

  getReliabilityPublicStatus(): Promise<ReliabilityPublicStatus> {
    return this.requestData(`${API_ENDPOINTS.reliability}/public-status`);
  }

  getReliabilityWorkbench(): Promise<ReliabilityWorkbench> {
    return this.requestData(`${API_ENDPOINTS.reliability}/workbench`);
  }

  createReliabilitySloSnapshot(windowMinutes = 60): Promise<ReliabilitySloSnapshot> {
    return this.requestData(`${API_ENDPOINTS.reliability}/slo-snapshots`, { method: "POST", body: { environment: "local_synthetic", window_minutes: windowMinutes } });
  }

  listReliabilityJobs(): Promise<ListResponse<ReliabilityJob>> {
    return this.requestData(`${API_ENDPOINTS.reliability}/jobs`);
  }

  recoverReliabilityJob(jobId: string): Promise<ReliabilityJob> {
    return this.requestData(`${API_ENDPOINTS.reliability}/jobs/${encodeURIComponent(jobId)}/recover`, { method: "POST", body: { reason_code: "manual_dependency_recovered" } });
  }

  updateReliabilityFlag(flagName: string, input: { enabled: boolean; role_scope: string[]; rollout_percent: number; reason_code: string }): Promise<ReliabilityFeatureFlag> {
    return this.requestData(`${API_ENDPOINTS.reliability}/feature-flags/${encodeURIComponent(flagName)}`, { method: "PATCH", body: input });
  }

  runReliabilityDrill(scenario: string): Promise<Record<string, unknown>> {
    return this.requestData(`${API_ENDPOINTS.reliability}/drills`, { method: "POST", body: { scenario } });
  }

  createReliabilityEvidencePackage(): Promise<Record<string, unknown>> {
    return this.requestData(`${API_ENDPOINTS.reliability}/evidence-packages`, { method: "POST" });
  }

  getUXGovernancePublicStatus(): Promise<UXGovernancePublicStatus> {
    return this.requestData(`${API_ENDPOINTS.uxGovernance}/public-status`);
  }

  getUXGovernanceWorkbench(): Promise<UXGovernanceWorkbench> {
    return this.requestData(`${API_ENDPOINTS.uxGovernance}/workbench`);
  }

  createUXEvidencePackage(): Promise<Record<string, unknown>> {
    return this.requestData(`${API_ENDPOINTS.uxGovernance}/evidence-packages`, { method: "POST" });
  }

  getOperationsGovernancePublicStatus(): Promise<OperationsPublicStatus> {
    return this.requestData(`${API_ENDPOINTS.operationsGovernance}/public-status`);
  }

  getOperationsGovernanceWorkbench(): Promise<OperationsGovernanceWorkbench> {
    return this.requestData(`${API_ENDPOINTS.operationsGovernance}/workbench`);
  }

  createOperationsPackage(input: { package_version: string; risk_level: "low" | "medium" | "high"; target_environment: "local_synthetic" | "production_candidate"; previous_package_id?: string }): Promise<OperationsReleasePackage> {
    return this.requestData(`${API_ENDPOINTS.operationsGovernance}/packages`, { method: "POST", body: input });
  }

  runOperationsReplay(packageId: string): Promise<Record<string, unknown>> {
    return this.requestData(`${API_ENDPOINTS.operationsGovernance}/packages/${encodeURIComponent(packageId)}/replay`, { method: "POST" });
  }

  submitOperationsPackage(packageId: string): Promise<OperationsReleasePackage> {
    return this.requestData(`${API_ENDPOINTS.operationsGovernance}/packages/${encodeURIComponent(packageId)}/submit`, { method: "POST" });
  }

  reviewOperationsPackage(packageId: string, input: { decision: "recommended" | "changes_requested"; evidence_ref: string; note?: string }): Promise<OperationsReleasePackage> {
    return this.requestData(`${API_ENDPOINTS.operationsGovernance}/packages/${encodeURIComponent(packageId)}/reviews`, { method: "POST", body: input });
  }

  approveOperationsPackage(packageId: string, input: { domain: "research" | "psychology" | "security"; decision: "approved" | "rejected"; evidence_ref: string; note?: string }): Promise<OperationsReleasePackage> {
    return this.requestData(`${API_ENDPOINTS.operationsGovernance}/packages/${encodeURIComponent(packageId)}/approvals`, { method: "POST", body: input });
  }

  releaseOperationsPackage(packageId: string): Promise<OperationsReleasePackage> {
    return this.requestData(`${API_ENDPOINTS.operationsGovernance}/packages/${encodeURIComponent(packageId)}/release`, { method: "POST", body: { confirmation: "LOCAL_SYNTHETIC_RELEASE_ONLY" } });
  }

  changeOperationsPackageState(packageId: string, action: "pause" | "resume" | "retire", reasonCode: string): Promise<OperationsReleasePackage> {
    return this.requestData(`${API_ENDPOINTS.operationsGovernance}/packages/${encodeURIComponent(packageId)}/${action}`, { method: "POST", body: { reason_code: reasonCode } });
  }

  rollbackOperationsRuntime(targetPackageId: string): Promise<Record<string, unknown>> {
    return this.requestData(`${API_ENDPOINTS.operationsGovernance}/runtime/rollback`, { method: "POST", body: { target_package_id: targetPackageId, reason_code: "human_selected_verified_rollback" } });
  }

  createOperationsMonitorSnapshot(): Promise<OperationsMonitoringSnapshot> {
    return this.requestData(`${API_ENDPOINTS.operationsGovernance}/monitoring/snapshots`, { method: "POST", body: { environment: "local_synthetic", window_days: 30 } });
  }

  reportOperationsIncident(input: { capability_id: string; incident_type: OperationsIncident["incident_type"]; severity: "high" | "critical"; summary_code: string; evidence_refs: string[]; package_id?: string }): Promise<OperationsIncident> {
    return this.requestData(`${API_ENDPOINTS.operationsGovernance}/incidents`, { method: "POST", body: input });
  }

  recordOperationsPostmortem(incidentId: string, input: { root_cause_code: string; corrective_actions: string[]; evidence_refs?: string[] }): Promise<OperationsIncident> {
    return this.requestData(`${API_ENDPOINTS.operationsGovernance}/incidents/${encodeURIComponent(incidentId)}/postmortem`, { method: "POST", body: input });
  }

  createOperationsEvidencePackage(): Promise<Record<string, unknown>> {
    return this.requestData(`${API_ENDPOINTS.operationsGovernance}/evidence-packages`, { method: "POST" });
  }

  listTherapeuticAssessmentCases(): Promise<{ items: TherapeuticAssessmentCase[]; count: number; boundary_notice: string }> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/cases`);
  }

  listTherapeuticAssessmentAuthorizations(userId?: string): Promise<{
    items: TherapeuticAssessmentAuthorization[];
    count: number;
    default_decision: "deny";
    temporary_showcase_bypass_counts: false;
  }> {
    const query = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/competency/authorizations${query}`);
  }

  getTherapeuticAssessmentAuthorizationStatus(
    caseId: string,
    taskCode: TherapeuticAssessmentTaskCode,
  ): Promise<TherapeuticAssessmentAuthorizationStatus> {
    const params = new URLSearchParams({ case_id: caseId, task_code: taskCode });
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/competency/effective?${params.toString()}`);
  }

  createTherapeuticAssessmentAuthorization(
    input: {
      user_id: string;
      competency_level: TherapeuticAssessmentCompetencyLevel;
      task_code: TherapeuticAssessmentTaskCode;
      scope: TherapeuticAssessmentAuthorization["scope"];
      supervisor_user_id: string;
      evidence_ref: string;
      starts_at?: string;
      expires_at: string;
    },
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentAuthorization> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/competency/authorizations`, {
      method: "POST",
      body: input,
      headers: { "Idempotency-Key": idempotencyKey },
    });
  }

  revokeTherapeuticAssessmentAuthorization(
    authorizationId: string,
    input: { reason: string; expected_version: number },
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentAuthorization> {
    return this.requestData(
      `${API_ENDPOINTS.therapeuticAssessment}/competency/authorizations/${encodeURIComponent(authorizationId)}/revoke`,
      { method: "PATCH", body: input, headers: { "Idempotency-Key": idempotencyKey } },
    );
  }

  getTherapeuticAssessmentQualityRuntime(): Promise<TherapeuticAssessmentQualityRuntime> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/quality/runtime`);
  }

  listTherapeuticAssessmentQualityReviews(
    query: { status?: string; page?: number; page_size?: number } = {},
  ): Promise<{
    items: TherapeuticAssessmentQualityReview[];
    total: number;
    page: number;
    page_size: number;
    runtime: TherapeuticAssessmentQualityRuntime;
    policy: { version: string; review_dimensions: TherapeuticAssessmentQualityDimension[] };
  }> {
    return this.requestData(
      this.withQuery(`${API_ENDPOINTS.therapeuticAssessment}/quality/reviews`, query),
    );
  }

  claimTherapeuticAssessmentQualityReview(
    reviewId: string,
    expectedVersion: number,
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentQualityReview> {
    return this.requestData(
      `${API_ENDPOINTS.therapeuticAssessment}/quality/reviews/${encodeURIComponent(reviewId)}/claim`,
      {
        method: "POST",
        body: { expected_version: expectedVersion },
        headers: { "Idempotency-Key": idempotencyKey },
      },
    );
  }

  completeTherapeuticAssessmentQualityReview(
    reviewId: string,
    input: {
      expected_version: number;
      dimensions: Record<
        TherapeuticAssessmentQualityDimension,
        { status: "pass" | "concern" | "not_applicable"; note: string; evidence_ref: string }
      >;
      decision: "pass" | "remediation_required";
      remediation_summary?: string;
    },
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentQualityReview> {
    return this.requestData(
      `${API_ENDPOINTS.therapeuticAssessment}/quality/reviews/${encodeURIComponent(reviewId)}/complete`,
      { method: "POST", body: input, headers: { "Idempotency-Key": idempotencyKey } },
    );
  }

  createTherapeuticAssessmentQualityIncident(
    caseId: string,
    input: {
      feedback_id?: string;
      category: TherapeuticAssessmentQualityIncident["category"];
      description: string;
      requested_resolution: string;
    },
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentQualityIncident> {
    return this.requestData(
      `${API_ENDPOINTS.therapeuticAssessment}/cases/${encodeURIComponent(caseId)}/quality-incidents`,
      { method: "POST", body: input, headers: { "Idempotency-Key": idempotencyKey } },
    );
  }

  listTherapeuticAssessmentQualityIncidents(
    query: { case_id?: string; status?: string } = {},
  ): Promise<{ items: TherapeuticAssessmentQualityIncident[]; count: number }> {
    return this.requestData(
      this.withQuery(`${API_ENDPOINTS.therapeuticAssessment}/quality/incidents`, query),
    );
  }

  analyzeTherapeuticAssessmentQualityIncident(
    incidentId: string,
    input: { expected_version: number; impact_analysis: Record<string, unknown> },
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentQualityIncident> {
    return this.requestData(
      `${API_ENDPOINTS.therapeuticAssessment}/quality/incidents/${encodeURIComponent(incidentId)}/impact-analysis`,
      { method: "POST", body: input, headers: { "Idempotency-Key": idempotencyKey } },
    );
  }

  resolveTherapeuticAssessmentQualityIncident(
    incidentId: string,
    input: {
      expected_version: number;
      resolution_action: "no_change" | "withdraw" | "correct";
      resolution_summary: string;
      replacement_feedback_id?: string;
    },
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentQualityIncident> {
    return this.requestData(
      `${API_ENDPOINTS.therapeuticAssessment}/quality/incidents/${encodeURIComponent(incidentId)}/resolve`,
      { method: "POST", body: input, headers: { "Idempotency-Key": idempotencyKey } },
    );
  }

  getTherapeuticAssessmentServiceLevels(): Promise<TherapeuticAssessmentServiceLevelStatus> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/service-levels`);
  }

  getTherapeuticAssessmentProductionContract(): Promise<TherapeuticAssessmentProductionContract> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/production-contract`);
  }

  listTherapeuticAssessmentWorkQueue(status = ""): Promise<{
    items: TherapeuticAssessmentWorkQueueItem[];
    count: number;
  }> {
    const suffix = status ? `?status=${encodeURIComponent(status)}` : "";
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/work-queue${suffix}`);
  }

  getTherapeuticAssessmentQueueRuntime(): Promise<TherapeuticAssessmentQueueRuntime> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/work-queue/runtime`);
  }

  runTherapeuticAssessmentQueueMonitor(): Promise<TherapeuticAssessmentQueueRuntime> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/work-queue/monitor`, {
      method: "POST",
    });
  }

  createTherapeuticAssessmentWorkItem(
    caseId: string,
    input: { queue_type: TherapeuticAssessmentQueueType; drafted_by?: string },
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentWorkQueueItem> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/cases/${encodeURIComponent(caseId)}/work-queue`, {
      method: "POST",
      body: input,
      headers: { "Idempotency-Key": idempotencyKey },
    });
  }

  claimTherapeuticAssessmentWorkItem(
    itemId: string,
    expectedVersion: number,
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentWorkQueueItem> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/work-queue/${encodeURIComponent(itemId)}/claim`, {
      method: "POST",
      body: { expected_version: expectedVersion },
      headers: { "Idempotency-Key": idempotencyKey },
    });
  }

  listTherapeuticAssessmentDutyShifts(userId = ""): Promise<{
    items: TherapeuticAssessmentDutyShift[];
    count: number;
  }> {
    const suffix = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/duty-shifts${suffix}`);
  }

  listPublicationCandidates(status = "", channel = ""): Promise<{
    items: PublicationCandidate[];
    count: number;
    production_release_approved: false;
  }> {
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (channel) params.set("channel", channel);
    const suffix = params.size ? `?${params.toString()}` : "";
    return this.requestData(
      `${API_ENDPOINTS.therapeuticAssessment}/publication-candidates${suffix}`,
    );
  }

  recoverPublicationCandidate(
    candidateId: string,
    input: {
      expected_version: number;
      content?: unknown;
      source_refs?: string[];
      context: Record<string, unknown>;
    },
    idempotencyKey: string,
  ): Promise<PublicationCandidate> {
    return this.requestData(
      `${API_ENDPOINTS.therapeuticAssessment}/publication-candidates/${encodeURIComponent(candidateId)}/recover`,
      {
        method: "POST",
        body: input,
        headers: { "Idempotency-Key": idempotencyKey },
      },
    );
  }

  withdrawPublicationCandidate(
    candidateId: string,
    expectedVersion: number,
    reason: string,
    idempotencyKey: string,
  ): Promise<PublicationCandidate> {
    return this.requestData(
      `${API_ENDPOINTS.therapeuticAssessment}/publication-candidates/${encodeURIComponent(candidateId)}/withdraw`,
      {
        method: "POST",
        body: { expected_version: expectedVersion, reason },
        headers: { "Idempotency-Key": idempotencyKey },
      },
    );
  }

  getTherapeuticAssessmentCase(caseId: string): Promise<TherapeuticAssessmentCase> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/cases/${encodeURIComponent(caseId)}`);
  }

  getTherapeuticAssessmentLifecycle(caseId: string): Promise<TherapeuticAssessmentLifecycle> {
    return this.requestData(
      `${API_ENDPOINTS.therapeuticAssessment}/cases/${encodeURIComponent(caseId)}/lifecycle`,
    );
  }

  getTherapeuticAssessmentLifecycleMetrics(): Promise<TherapeuticAssessmentLifecycleMetrics> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/lifecycle/metrics`);
  }

  getTherapeuticAssessmentProductionGate(): Promise<TherapeuticAssessmentProductionGate> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/production-gate`);
  }

  evaluateTherapeuticAssessmentProductionGate(
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentProductionGate> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/production-gate/evaluate`, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
    });
  }

  listTherapeuticAssessmentReleaseEvidence(): Promise<{
    items: TherapeuticAssessmentReleaseEvidence[];
    count: number;
    boundary_notice: string;
  }> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/production-gate/evidence`);
  }

  transitionTherapeuticAssessmentState(
    caseId: string,
    input: TherapeuticAssessmentTransitionInput,
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentCase> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/cases/${encodeURIComponent(caseId)}/transitions`, {
      method: "POST",
      body: input,
      headers: { "Idempotency-Key": idempotencyKey },
    });
  }

  listTherapeuticAssessmentEvidence(caseId: string): Promise<{ items: TherapeuticAssessmentEvidenceItem[]; count: number }> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/cases/${encodeURIComponent(caseId)}/evidence`);
  }

  getTherapeuticAssessmentResearcherWorkbench(
    caseId: string,
    query: {
      kind?: string;
      review_status?: string;
      visibility?: string;
      page?: number;
      page_size?: number;
    } = {},
  ): Promise<TherapeuticAssessmentResearcherWorkbench> {
    return this.requestData(
      this.withQuery(
        `${API_ENDPOINTS.therapeuticAssessment}/cases/${encodeURIComponent(caseId)}/researcher-workbench`,
        query,
      ),
    );
  }

  saveTherapeuticAssessmentResearcherDraft(
    caseId: string,
    input: {
      internal_notes: string;
      participant_visible_draft: string;
      filters: TherapeuticAssessmentResearcherDraft["filters"];
      selected_evidence_id?: string | null;
      expected_version: number;
    },
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentResearcherDraft> {
    return this.requestData(
      `${API_ENDPOINTS.therapeuticAssessment}/cases/${encodeURIComponent(caseId)}/researcher-workbench/draft`,
      { method: "PUT", body: input, headers: { "Idempotency-Key": idempotencyKey } },
    );
  }

  updateTherapeuticAssessmentQuestion(
    caseId: string,
    input: Record<string, unknown>,
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentCase> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/cases/${encodeURIComponent(caseId)}/question`, {
      method: "PATCH",
      body: input,
      headers: { "Idempotency-Key": idempotencyKey },
    });
  }

  createTherapeuticAssessmentEvidence(
    caseId: string,
    input: Record<string, unknown>,
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentEvidenceItem> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/cases/${encodeURIComponent(caseId)}/evidence`, {
      method: "POST",
      body: input,
      headers: { "Idempotency-Key": idempotencyKey },
    });
  }

  createTherapeuticAssessmentDataItem(
    caseId: string,
    input: Record<string, unknown>,
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentDataItem> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/cases/${encodeURIComponent(caseId)}/data-items`, {
      method: "POST",
      body: input,
      headers: { "Idempotency-Key": idempotencyKey },
    });
  }

  updateTherapeuticAssessmentDataConsent(
    itemId: string,
    input: Record<string, unknown>,
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentDataItem> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/data-items/${encodeURIComponent(itemId)}/consent`, {
      method: "PATCH",
      body: input,
      headers: { "Idempotency-Key": idempotencyKey },
    });
  }

  getTherapeuticAssessmentParticipantDraft(
    caseId: string,
    stepId: TherapeuticAssessmentParticipantStep,
  ): Promise<TherapeuticAssessmentParticipantDraft> {
    return this.requestData(
      `${API_ENDPOINTS.therapeuticAssessment}/cases/${encodeURIComponent(caseId)}/participant-drafts/${encodeURIComponent(stepId)}`,
    );
  }

  saveTherapeuticAssessmentParticipantDraft(
    caseId: string,
    stepId: TherapeuticAssessmentParticipantStep,
    input: {
      payload: Record<string, unknown>;
      expected_version: number;
      status?: "active" | "completed" | "discarded";
      client_updated_at?: string;
    },
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentParticipantDraft> {
    return this.requestData(
      `${API_ENDPOINTS.therapeuticAssessment}/cases/${encodeURIComponent(caseId)}/participant-drafts/${encodeURIComponent(stepId)}`,
      { method: "PUT", body: input, headers: { "Idempotency-Key": idempotencyKey } },
    );
  }

  getTherapeuticAssessmentSafetyStatus(): Promise<TherapeuticAssessmentSafetyStatus> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/safety/status`);
  }

  configureTherapeuticAssessmentResponsibilityChain(
    caseId: string,
    input: Record<string, unknown>,
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentResponsibilityChain> {
    return this.requestData(
      `${API_ENDPOINTS.therapeuticAssessment}/cases/${encodeURIComponent(caseId)}/responsibility-chain`,
      { method: "PUT", body: input, headers: { "Idempotency-Key": idempotencyKey } },
    );
  }

  createTherapeuticAssessmentSafetySignal(
    caseId: string,
    input: Record<string, unknown>,
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentSafetyEvent> {
    return this.requestData(
      `${API_ENDPOINTS.therapeuticAssessment}/cases/${encodeURIComponent(caseId)}/safety-signals`,
      { method: "POST", body: input, headers: { "Idempotency-Key": idempotencyKey } },
    );
  }

  resolveTherapeuticAssessmentSafetyEvent(
    eventId: string,
    input: { resolution_evidence_ref: string },
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentSafetyEvent> {
    return this.requestData(
      `${API_ENDPOINTS.therapeuticAssessment}/safety-events/${encodeURIComponent(eventId)}/resolve`,
      { method: "POST", body: input, headers: { "Idempotency-Key": idempotencyKey } },
    );
  }

  restoreTherapeuticAssessmentRuntime(
    input: { restoration_evidence_ref: string },
  ): Promise<TherapeuticAssessmentSafetyStatus> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/safety/runtime/restore`, {
      method: "POST",
      body: input,
    });
  }

  createTherapeuticAssessmentFeedback(
    caseId: string,
    input: {
      source: "human" | "ai_draft";
      feedback_layer?: "layer_1" | "layer_2";
      recipient_user_id?: string;
      letter_title?: string;
      observations: string[];
      evidence: string[];
      alternatives: string[];
      uncertainty: string;
      next_step: string;
      human_discussion: string[];
      participant_content: string;
    },
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentFeedbackVersion> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/cases/${encodeURIComponent(caseId)}/feedback-versions`, {
      method: "POST",
      body: input,
      headers: { "Idempotency-Key": idempotencyKey },
    });
  }

  reviewTherapeuticAssessmentFeedback(feedbackId: string, decision: "approved" | "changes_requested", idempotencyKey: string): Promise<TherapeuticAssessmentFeedbackVersion> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/feedback-versions/${encodeURIComponent(feedbackId)}/review`, {
      method: "POST",
      body: { decision },
      headers: { "Idempotency-Key": idempotencyKey },
    });
  }

  sendTherapeuticAssessmentFeedback(feedbackId: string, idempotencyKey: string): Promise<TherapeuticAssessmentFeedbackVersion> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/feedback-versions/${encodeURIComponent(feedbackId)}/send`, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
    });
  }

  respondToTherapeuticAssessmentFeedback(
    feedbackId: string,
    input: { recognition: "like" | "partly_like" | "not_like" | "need_time"; disagreement_note?: string },
    idempotencyKey: string,
  ) {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/feedback-versions/${encodeURIComponent(feedbackId)}/responses`, {
      method: "POST",
      body: input,
      headers: { "Idempotency-Key": idempotencyKey },
    });
  }

  reviseTherapeuticAssessmentFeedback(
    feedbackId: string,
    input: {
      expected_lifecycle_version: number;
      revision_reason: string;
      feedback_layer?: "layer_1" | "layer_2";
      letter_title?: string;
      participant_content?: string;
    },
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentFeedbackVersion> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/feedback-versions/${encodeURIComponent(feedbackId)}/revise`, {
      method: "POST",
      body: input,
      headers: { "Idempotency-Key": idempotencyKey },
    });
  }

  withdrawTherapeuticAssessmentFeedback(
    feedbackId: string,
    input: { expected_lifecycle_version: number; reason: string },
    idempotencyKey: string,
  ): Promise<TherapeuticAssessmentFeedbackVersion> {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/feedback-versions/${encodeURIComponent(feedbackId)}/withdraw`, {
      method: "POST",
      body: input,
      headers: { "Idempotency-Key": idempotencyKey },
    });
  }

  resendTherapeuticAssessmentFeedback(feedbackId: string, idempotencyKey: string) {
    return this.requestData(`${API_ENDPOINTS.therapeuticAssessment}/feedback-versions/${encodeURIComponent(feedbackId)}/resend`, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
    });
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
    let response: Response;
    try {
      response = await fetch(this.absoluteUrl(path), {
        method: options.method ?? "GET",
        headers: { "Content-Type": "application/json", ...authHeader, ...(options.headers || {}) },
        body: options.body === undefined ? undefined : JSON.stringify(options.body),
      });
    } catch (error) {
      throw new SafeHomeApiError("现在没能连接服务，请检查网络后再试。", "network_error", 0, {
        clientVersion: this.clientVersion,
        occurredAt: new Date().toISOString(),
      });
    }

    const responseText = await response.text();
    let payload: any;
    try {
      payload = responseText ? JSON.parse(responseText) : {};
    } catch (error) {
      throw new SafeHomeApiError("服务返回了无法识别的内容，请稍后再试。", "invalid_response", response.status, {
        requestId: response.headers.get("X-Request-ID") || "",
        clientVersion: this.clientVersion,
        serviceVersion: response.headers.get("X-SafeHome-Service-Version") || "",
        buildId: response.headers.get("X-SafeHome-Build-ID") || "",
        occurredAt: new Date().toISOString(),
      });
    }
    const diagnostic = {
      requestId: String(payload?.request_id || response.headers.get("X-Request-ID") || ""),
      clientVersion: this.clientVersion,
      serviceVersion: response.headers.get("X-SafeHome-Service-Version") || "",
      buildId: response.headers.get("X-SafeHome-Build-ID") || "",
      occurredAt: new Date().toISOString(),
    };
    if (!response.ok) {
      const isAdminRequest = path.startsWith("/api/admin") || Boolean(options.headers?.["X-Admin-Token"]);
      const message =
        response.status === 401 && isAdminRequest
          ? "后台令牌缺失或无效。请使用当前部署环境提供的后台令牌。"
          : payload?.error?.message ?? (response.status === 401 ? "需要先登录或重新登录。" : "请求失败");
      const code = response.status === 401 && isAdminRequest ? "admin_unauthorized" : payload?.error?.code ?? "http_error";
      throw new SafeHomeApiError(message, code, response.status, diagnostic);
    }
    if (payload && typeof payload === "object" && payload.ok === false) {
      throw new SafeHomeApiError(payload.error?.message ?? "请求失败", payload.error?.code ?? "api_error", response.status, diagnostic);
    }
    return payload as T;
  }
}

export const safeHomeApi = new SafeHomeApiClient();
