import { safeHomeApi, type SafeHomeApiClient } from "./safehomeApi";

type PublicMethodKey<T> = {
  [K in keyof T]-?: T[K] extends (...args: any[]) => any ? K : never;
}[keyof T];

function bindApiMethods<K extends PublicMethodKey<SafeHomeApiClient>>(
  ...names: readonly K[]
): Pick<SafeHomeApiClient, K> {
  const result = {} as Pick<SafeHomeApiClient, K>;
  for (const name of names) {
    const method = safeHomeApi[name];
    if (typeof method !== "function") {
      throw new Error(`SafeHome API method is unavailable: ${String(name)}`);
    }
    (result as Record<string, unknown>)[String(name)] = method.bind(safeHomeApi);
  }
  return result;
}

/**
 * New Web code should import a domain facade instead of extending or importing
 * the legacy all-in-one client directly. The legacy client remains intact as a
 * compatibility layer while pages are migrated incrementally.
 */
export const participantApi = bindApiMethods(
  "healthz",
  "login",
  "register",
  "changePassword",
  "getCurrentUser",
  "getDataClaimPreview",
  "getIdentityStatus",
  "unbindIdentity",
  "getTodayJourney",
  "getTrainingPlan",
  "getGrowthOverview",
  "createGoal",
  "listGoals",
  "createConsent",
  "listConsentRecords",
  "createDiary",
  "listDiaries",
  "generateFeedback",
  "createProfile",
  "listProfileResults",
  "getProfileResult",
  "checkRisk",
  "getStudentAssessment",
  "getProfileVisuals",
  "getParentAssessment",
  "createParentAssessment",
  "listCards",
  "recommendCards",
  "listAssessmentResults",
  "listAssessments",
  "getAssessment",
  "createAssessmentResult",
  "getAssessmentProfilePosition",
  "createCheckin",
  "listCheckins",
  "getWeeklyReport",
  "createSupervision",
);

export const researchApi = bindApiMethods(
  "getTextAnalysisSummary",
  "getRelationshipResearchDashboard",
  "getResearchCapabilities",
  "createResearchDelivery",
  "saveResearchDelivery",
  "runResearchDeliveryAction",
  "listResearchDeliveries",
  "listResearchAssignments",
  "createResearchAssignment",
  "claimResearchEnrollment",
  "listResearchParticipants",
  "getResearchParticipant",
  "getResearchParticipantModule",
  "getResearchOperations",
  "getResearchQueue",
  "getResearchWorkItem",
  "actOnResearchWorkItem",
  "getResearchWorkItemMetrics",
  "getRelationshipEnrollment",
  "getRelationshipReport",
  "confirmRelationshipReport",
  "updateRelationshipReport",
  "sendRelationshipReport",
  "createRelationshipResearchNote",
);

export const governanceApi = bindApiMethods(
  "listRiskReviews",
  "updateRiskReview",
  "listPrivacyRequests",
  "cancelPrivacyRequest",
  "appealPrivacyRequest",
  "listPrivacyRequestsForReview",
  "getPrivacyRequestForReview",
  "transitionPrivacyRequest",
  "previewPrivacyRequest",
  "approvePrivacyExecution",
  "executePrivacyRequest",
  "updateContentReview",
  "listAdminWorksheets",
  "createAdminWorksheet",
  "updateAdminWorksheet",
  "disableAdminWorksheet",
);

/**
 * Internal R&D remains deliberately explicit and small. Add methods here only
 * when they are already present in the legacy client and are not participant
 * capabilities.
 */
export const internalRdApi = bindApiMethods(
  "getShowcaseAccess",
);

export type SafeHomeDomainApi = {
  participant: typeof participantApi;
  research: typeof researchApi;
  governance: typeof governanceApi;
  internalRd: typeof internalRdApi;
};

export const domainApi: SafeHomeDomainApi = {
  participant: participantApi,
  research: researchApi,
  governance: governanceApi,
  internalRd: internalRdApi,
};
