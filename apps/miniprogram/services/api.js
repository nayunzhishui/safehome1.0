const { getAnonymousUserId } = require("./userIdentity");
const { DEFAULT_CLOUD_CONFIG, getCloudConfig } = require("./cloudConfig");

const DEFAULT_CONTAINER_SERVICE = DEFAULT_CLOUD_CONFIG.containerService;
const DEFAULT_CLOUD_ENV_ID = DEFAULT_CLOUD_CONFIG.cloudEnvId;
const DEFAULT_HTTP_BASE_URL = DEFAULT_CLOUD_CONFIG.httpBaseUrl;

const ERROR_MESSAGES_BY_STATUS = {
  400: "提交内容还不完整，请检查后再试一次。",
  401: "登录状态已过期，请重新登录后再继续。",
  403: "当前账号没有权限执行这个操作。",
  404: "没有找到对应内容，可能已经更新或不可访问。",
  409: "当前内容已被更新，请刷新后再试一次。",
  422: "提交内容还不完整，请检查后再试一次。",
  429: "操作有点频繁，请稍后再试。",
  500: "服务暂时没有响应，请稍后再试。",
  502: "服务暂时没有响应，请稍后再试。",
  503: "服务暂时没有响应，请稍后再试。",
  504: "服务暂时没有响应，请稍后再试。",
};

const ERROR_MESSAGES_BY_CODE = {
  validation_error: "提交内容还不完整，请检查后再试一次。",
  auth_required: "登录状态已过期，请重新登录后再继续。",
  unauthorized: "登录状态已过期，请重新登录后再继续。",
  forbidden: "当前账号没有权限执行这个操作。",
  not_found: "没有找到对应内容，可能已经更新或不可访问。",
  network_error: "现在没能连上，请检查网络后再试一次。",
  local_http_error: "本地后端连接失败，请确认 Flask 已启动后再试一次。",
  wechat_login_config_missing: "微信登录暂不可用，请尝试手机号快捷登录或账号密码登录。",
  wechat_login_failed: "微信登录凭证已失效，请重新尝试。",
  wechat_phone_config_missing: "手机号快捷登录尚未开通，请使用微信一键登录或账号密码登录。",
  wechat_phone_config_invalid: "手机号快捷登录暂不可用，请使用其他登录方式。",
  wechat_phone_exchange_failed: "手机号授权已失效，请重新授权后再试。",
  wechat_phone_invalid: "微信没有返回有效手机号，请重新授权。",
  wechat_service_unavailable: "微信服务暂时没有响应，请稍后重试。",
  phone_account_conflict: "该手机号已关联其他账号，请使用原账号登录。",
};

const API_ENDPOINTS = {
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
  trainingRecommendationReplay: "/api/training-plan/recommendations/replay",
  trainingRecommendationSnapshots: "/api/training-plan/recommendation-snapshots",
  trainingPlanAssignment: "/api/training-plan/assignment",
  notificationConfig: "/api/notifications/config",
  notificationConsent: "/api/notifications/consent",
  courses: "/api/courses",
  courseDetailBase: "/api/courses/:id",
  courseProgressBase: "/api/courses/:id/progress",
  programs: "/api/programs",
  programDetailBase: "/api/programs/:id",
  programEntriesBase: "/api/programs/:id/entries",
  assessments: "/api/assessments",
  assessmentResults: "/api/assessment-results",
  assessmentProfilePositionBase: "/api/assessment-results/:id/profile-position",
  consent: "/api/consent",
  profile: "/api/profile",
  profileStats: "/api/profile/stats",
  progressSummary: "/api/progress-summary",
  profileTrend: "/api/profile-trend",
  trainingEffectiveness: "/api/training-effectiveness",
  textAnalysisSummary: "/api/text-analysis/summary",
  showcaseAccess: "/api/showcase-access",
  profileResults: "/api/profile-results",
  messages: "/api/messages",
  riskCheck: "/api/risk/check",
  riskReview: "/api/risk-review",
  modelInfo: "/api/model/info",
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
  parentAssessments: "/api/parent-assessments",
  checkins: "/api/checkins",
  weeklyReport: "/api/weekly-report",
  growthOverview: "/api/growth/overview",
  supervision: "/api/supervision",
  adminExport: "/api/admin/export",
  relationshipPilot: "/api/relationship-pilot",
  productEvents: "/api/product-events",
  privacyRequests: "/api/privacy/requests",
  privacyDeleteMyData: "/api/privacy/delete-my-data",
  researchQueues: "/api/research/queues",
  researchWorkItems: "/api/research/work-items",
  researchWorkItemMetrics: "/api/research/work-items/metrics",
  contentGovernanceActive: "/api/content-review/active",
  aiQaConfig: "/api/ai-qa/config",
  offlineBenchmarks: "/api/research/benchmarks",
  researchMethodology: "/api/research/methodology",
  securityControls: "/api/security",
  reliability: "/api/reliability",
  uxGovernance: "/api/ux-governance",
  operationsGovernance: "/api/operations-governance",
};

function createSafeHomeApi(options = {}) {
  const cloudConfig = getCloudConfig(options);
  const containerService = cloudConfig.containerService;
  const cloudEnvId = cloudConfig.cloudEnvId;
  const httpBaseUrl = cloudConfig.httpBaseUrl;
  const localHttpBaseUrl = cloudConfig.localHttpBaseUrl;
  const useLocalHttp = cloudConfig.useLocalHttp;
  const defaultUserId = options.defaultUserId || getAnonymousUserId();

  function getCurrentDefaultUserId() {
    try {
      const storedUser = wx.getStorageSync("auth_user");
      if (storedUser && storedUser.id) {
        return storedUser.id;
      }
      if (typeof storedUser === "string" && storedUser) {
        const parsed = JSON.parse(storedUser);
        if (parsed && parsed.id) {
          return parsed.id;
        }
      }
    } catch (error) {
      // Ignore malformed local auth state and keep anonymous trial mode working.
    }
    return defaultUserId;
  }

  function withDefaultUser(data = {}) {
    return {
      ...data,
      user_id: data.user_id || getCurrentDefaultUserId(),
    };
  }

  function clearAuthSession() {
    wx.removeStorageSync("auth_token");
    wx.removeStorageSync("auth_user");
    try {
      const app = typeof getApp === "function" ? getApp() : null;
      if (app && app.globalData) {
        app.globalData.token = "";
        app.globalData.user = null;
      }
    } catch (error) {
      // getApp can be unavailable in isolated service-layer tests.
    }
  }

  function request(path, options = {}) {
    const method = options.method || "GET";
    const debug = {
      env: cloudEnvId,
      service: containerService,
      transport: useLocalHttp ? "local-http" : "cloud-container",
      path,
      method,
    };
    const authToken = wx.getStorageSync("auth_token") || "";
    const authHeader = authToken ? { Authorization: `Bearer ${authToken}` } : {};

    return new Promise((resolve, reject) => {
      if (options.requiresAuth && !authToken) {
        reject({
          code: "auth_required",
          message: ERROR_MESSAGES_BY_CODE.auth_required,
          retryable: false,
          path,
          method,
          status: 401,
          statusCode: 401,
          debug,
          debugMessage: "本接口需要先登录，小程序端未找到 auth_token。",
        });
        return;
      }

      if (useLocalHttp) {
        wx.request({
          url: `${localHttpBaseUrl}${path}`,
          method,
          data: options.data || {},
          header: {
            "content-type": "application/json",
            ...authHeader,
            ...(options.header || {}),
          },
          success(res) {
            handleResponse(res, resolve, reject, path, method, debug);
          },
          fail(err) {
            reject({
              code: err.errCode || "local_http_error",
              message: ERROR_MESSAGES_BY_CODE.local_http_error,
              retryable: true,
              debugMessage: `本地 HTTP 调试请求失败：${localHttpBaseUrl}${path}`,
              path,
              method,
              status: 0,
              detail: err,
              debug,
            });
          },
        });
        return;
      }

      if (!wx.cloud || !wx.cloud.callContainer) {
        const debugMessage = `云托管调用不可用，请确认微信开发者工具已启用云开发环境。当前 env=${cloudEnvId}，service=${containerService}，path=${path}。`;
        console.warn("[safehome api]", debugMessage);
        reject({
          code: "cloud_container_unavailable",
          message: "网络好像没连上，请检查网络后再试一次。",
          retryable: true,
          debugMessage,
          debug,
        });
        return;
      }

      wx.cloud.callContainer({
        config: {
          env: cloudEnvId,
        },
        path,
        method,
        data: options.data || {},
        header: {
          "content-type": "application/json",
          ...authHeader,
          ...(options.header || {}),
          "X-WX-SERVICE": containerService,
        },
        success(res) {
          handleResponse(res, resolve, reject, path, method, debug);
        },
        fail(err) {
          const debugMessage = `云托管调用失败，请检查云环境 ID、云托管服务名和服务状态。当前 env=${cloudEnvId}，service=${containerService}，path=${path}。`;
          console.warn("[safehome api]", debugMessage, err);
          reject({
            code: err.errCode || "network_error",
            message: "现在没能连上，请检查网络后再试一次。",
            retryable: true,
            debugMessage,
            path,
            method,
            status: 0,
            detail: err,
            debug,
          });
        },
      });
    });
  }

  function handleResponse(res, resolve, reject, path, method, debug) {
    const statusCode = res.statusCode || 0;
    const payload = res.data;

    if (statusCode < 200 || statusCode >= 300) {
      if (statusCode === 401) {
        clearAuthSession();
      }
      reject(normalizeApiError({
        path,
        method,
        statusCode,
        payload,
        debug,
      }));
      return;
    }

    if (payload && payload.ok === false) {
      reject(normalizeApiError({
        path,
        method,
        statusCode,
        payload,
        debug,
      }));
      return;
    }

    resolve(payload && payload.data !== undefined ? payload.data : payload);
  }

  function normalizeApiError({ path, method, statusCode, payload, debug }) {
    const backendError = payload && payload.error ? payload.error : {};
    const rawCode = backendError.code || payload && payload.code || "api_error";
    const code = String(rawCode || "api_error");
    const rawMessage = backendError.message || payload && payload.message || "";
    const retryable = statusCode === 0 || statusCode === 429 || statusCode >= 500;
    const message = getSafeUserMessage(code, statusCode);

    return {
      code,
      message,
      retryable,
      path,
      method,
      status: statusCode,
      statusCode,
      payload,
      debug,
      debugMessage: rawMessage ? `后端返回：${rawMessage}` : "",
    };
  }

  function getSafeUserMessage(code, statusCode) {
    if (ERROR_MESSAGES_BY_CODE[code]) {
      return ERROR_MESSAGES_BY_CODE[code];
    }
    if (ERROR_MESSAGES_BY_STATUS[statusCode]) {
      return ERROR_MESSAGES_BY_STATUS[statusCode];
    }
    if (statusCode >= 500) {
      return ERROR_MESSAGES_BY_STATUS[500];
    }
    return "请求暂时没有完成，请稍后再试。";
  }

  function queryString(params = {}) {
    const query = Object.keys(params)
      .filter((key) => params[key] !== undefined && params[key] !== "")
      .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
      .join("&");
    return query ? `?${query}` : "";
  }

  function endpointWithId(template, id) {
    return template.replace(":id", encodeURIComponent(id));
  }

  return {
    getDebugConfig() {
      return {
        cloudEnvId,
        containerService,
        httpBaseUrl,
        localHttpBaseUrl,
        useLocalHttp,
        transport: useLocalHttp ? "local-http" : "cloud-container",
        defaultUserId,
      };
    },

    healthz() {
      return request(API_ENDPOINTS.healthz);
    },

    readyz() {
      return request(API_ENDPOINTS.readyz);
    },

    getShowcaseAccess() {
      return request(API_ENDPOINTS.showcaseAccess);
    },

    login(data) {
      return request(API_ENDPOINTS.authLogin, {
        method: "POST",
        data: {
          ...data,
          anonymous_id: defaultUserId,
        },
      }).then((result) => {
        if (result && result.token) {
          wx.setStorageSync("auth_token", result.token);
          wx.setStorageSync("auth_user", result.user || null);
          wx.removeStorageSync("safehome_anonymous_user_id");
        }
        return result;
      });
    },

    getAuthCapabilities() {
      return request(API_ENDPOINTS.authCapabilities);
    },

    getDataClaimPreview() {
      return request(API_ENDPOINTS.authDataClaimPreview, { requiresAuth: true });
    },

    claimAnonymousData(claimId) {
      return request(API_ENDPOINTS.authDataClaim, {
        method: "POST",
        data: { claim_id: claimId, confirm: true },
        requiresAuth: true,
      });
    },

    wechatLogin(data) {
      return request(API_ENDPOINTS.authWechatLogin, {
        method: "POST",
        data: {
          ...data,
          anonymous_id: defaultUserId,
        },
      }).then((result) => {
        if (result && result.token) {
          wx.setStorageSync("auth_token", result.token);
          wx.setStorageSync("auth_user", result.user || null);
          wx.removeStorageSync("safehome_anonymous_user_id");
        }
        return result;
      });
    },

    phoneLogin(data) {
      return request(API_ENDPOINTS.authPhoneLogin, {
        method: "POST",
        data: {
          ...data,
          anonymous_id: defaultUserId,
        },
      }).then((result) => {
        if (result && result.token) {
          wx.setStorageSync("auth_token", result.token);
          wx.setStorageSync("auth_user", result.user || null);
          wx.removeStorageSync("safehome_anonymous_user_id");
        }
        return result;
      });
    },

    bindWechatPhone(data) {
      return request(API_ENDPOINTS.authBindPhone, {
        method: "POST",
        data,
        requiresAuth: true,
      });
    },

    register(data) {
      return request(API_ENDPOINTS.authRegister, {
        method: "POST",
        data: {
          ...data,
          anonymous_id: defaultUserId,
        },
      }).then((result) => {
        if (result && result.token) {
          wx.setStorageSync("auth_token", result.token);
          wx.setStorageSync("auth_user", result.user || null);
          wx.removeStorageSync("safehome_anonymous_user_id");
        }
        return result;
      });
    },

    logout() {
      wx.removeStorageSync("auth_token");
      wx.removeStorageSync("auth_user");
      return request(API_ENDPOINTS.authLogout, { method: "POST" }).catch(() => ({}));
    },

    createGoal(data) {
      const idempotencyKey = data.client_submission_id || "";
      return request(API_ENDPOINTS.goals, {
        method: "POST",
        data: withDefaultUser(data),
        header: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
        requiresAuth: true,
      });
    },

    listGoals(params = {}) {
      return request(`${API_ENDPOINTS.goals}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    createConsent(data) {
      return request(API_ENDPOINTS.consent, {
        method: "POST",
        data: withDefaultUser(data),
        requiresAuth: true,
      });
    },

    listConsentRecords(params = {}) {
      return request(`${API_ENDPOINTS.consent}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    createDiary(data) {
      const idempotencyKey = data.client_submission_id || "";
      return request(API_ENDPOINTS.diaries, {
        method: "POST",
        data: withDefaultUser(data),
        header: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
        requiresAuth: true,
      });
    },

    listDiaries(params = {}) {
      return request(`${API_ENDPOINTS.diaries}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    createEmotionThermometer(data) {
      return request(API_ENDPOINTS.emotionThermometer, {
        method: "POST",
        data: withDefaultUser(data),
        requiresAuth: true,
      });
    },

    getEmotionThermometerDay(params = {}) {
      return request(`${API_ENDPOINTS.emotionThermometerDay}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    generateFeedback(data) {
      return request(API_ENDPOINTS.feedbackGenerate, {
        method: "POST",
        data: withDefaultUser(data),
        requiresAuth: true,
      });
    },

    createProfile(data) {
      const idempotencyKey = data.client_submission_id || "";
      return request(API_ENDPOINTS.profile, {
        method: "POST",
        data: withDefaultUser(data),
        header: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
        requiresAuth: true,
      });
    },

    getProfileResult(id, params = {}) {
      return request(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    getProfileVisuals(id, params = {}) {
      return request(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/visuals${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    getProfileStats(params = {}) {
      return request(`${API_ENDPOINTS.profileStats}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    getProgressSummary(params = {}) {
      return request(`${API_ENDPOINTS.progressSummary}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    getProfileTrend(params = {}) {
      return request(`${API_ENDPOINTS.profileTrend}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    getTrainingEffectiveness(params = {}) {
      return request(`${API_ENDPOINTS.trainingEffectiveness}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    listMessages(params = {}) {
      return request(`${API_ENDPOINTS.messages}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    getMessage(id, params = {}) {
      return request(`${API_ENDPOINTS.messages}/${encodeURIComponent(id)}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    markMessageRead(id, data = {}) {
      return request(`${API_ENDPOINTS.messages}/${encodeURIComponent(id)}/read`, {
        method: "POST",
        data: withDefaultUser(data),
        requiresAuth: true,
      });
    },

    markAllMessagesRead(data = {}) {
      return request(`${API_ENDPOINTS.messages}/read-all`, {
        method: "POST",
        data: withDefaultUser(data),
        requiresAuth: true,
      });
    },

    sendResearcherMessage(data) {
      const payload = { ...data };
      const idempotencyKey = payload.idempotency_key || "";
      delete payload.idempotency_key;
      return request(API_ENDPOINTS.messages, {
        method: "POST",
        data: payload,
        header: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
        requiresAuth: true,
      });
    },

    listProfileFollowups(id, params = {}) {
      return request(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/followups${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    createProfileFollowup(id, data) {
      return request(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/followups`, {
        method: "POST",
        data: withDefaultUser(data),
        requiresAuth: true,
      });
    },

    listProfileSandplay(id, params = {}) {
      return request(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/sandplay${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    createProfileSandplay(id, data) {
      return request(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/sandplay`, {
        method: "POST",
        data: withDefaultUser(data),
        requiresAuth: true,
      });
    },

    checkRisk(data) {
      return request(API_ENDPOINTS.riskCheck, {
        method: "POST",
        data,
      });
    },

    listRiskReviews(params = {}) {
      return request(`${API_ENDPOINTS.riskReview}${queryString(params)}`);
    },

    updateRiskReview(id, data) {
      return request(`${API_ENDPOINTS.riskReview}/${encodeURIComponent(id)}/review`, {
        method: "POST",
        data,
      });
    },

    getModelInfo() {
      return request(API_ENDPOINTS.modelInfo);
    },

    listCards() {
      return request(API_ENDPOINTS.cards);
    },

    recommendCards(params = {}) {
      return request(
        `${API_ENDPOINTS.cardsRecommend}${queryString({
          ...params,
          tags: Array.isArray(params.tags) ? params.tags.join(",") : params.tags,
        })}`,
      );
    },

    getTrainingPlan(params = {}) {
      return request(`${API_ENDPOINTS.trainingPlan}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    getTodayJourney(params = {}) {
      return request(`${API_ENDPOINTS.journeyToday}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    createFeedbackLedgerEntry(data) {
      const payload = { ...data };
      const idempotencyKey = payload.idempotency_key || "";
      return request(API_ENDPOINTS.feedbackLedger, {
        method: "POST",
        data: payload,
        header: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
        requiresAuth: true,
      });
    },

    listFeedbackLedgerEntries(params = {}) {
      return request(`${API_ENDPOINTS.feedbackLedger}${queryString(params)}`, { requiresAuth: true });
    },

    applyFeedbackLedgerAction(entryId, data = {}) {
      const payload = { ...data };
      const idempotencyKey = payload.idempotency_key || "";
      return request(`${API_ENDPOINTS.feedbackLedger}/${encodeURIComponent(entryId)}/actions`, {
        method: "POST",
        data: payload,
        header: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
        requiresAuth: true,
      });
    },

    replayTrainingRecommendation(data = {}) {
      const payload = { ...data };
      const idempotencyKey = payload.idempotency_key || "";
      return request(API_ENDPOINTS.trainingRecommendationReplay, {
        method: "POST",
        data: payload,
        header: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
        requiresAuth: true,
      });
    },

    getTrainingRecommendationSnapshot(snapshotId) {
      return request(`${API_ENDPOINTS.trainingRecommendationSnapshots}/${encodeURIComponent(snapshotId)}`, { requiresAuth: true });
    },

    getFeedbackLedgerSummary(params = {}) {
      return request(`${API_ENDPOINTS.feedbackLedgerSummary}${queryString(params)}`, { requiresAuth: true });
    },

    listPrivacyRequests(params = {}) {
      return request(`${API_ENDPOINTS.privacyRequests}${queryString(params)}`, { requiresAuth: true });
    },

    createPrivacyDeleteRequest(data = {}) {
      return request(API_ENDPOINTS.privacyDeleteMyData, {
        method: "POST",
        data,
        requiresAuth: true,
      });
    },

    cancelPrivacyRequest(requestId, data = {}, idempotencyKey = "") {
      return request(`${API_ENDPOINTS.privacyRequests}/${encodeURIComponent(requestId)}/cancel`, {
        method: "POST",
        data,
        header: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
        requiresAuth: true,
      });
    },

    appealPrivacyRequest(requestId, data = {}, idempotencyKey = "") {
      return request(`${API_ENDPOINTS.privacyRequests}/${encodeURIComponent(requestId)}/appeal`, {
        method: "POST",
        data,
        header: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
        requiresAuth: true,
      });
    },

    getResearchQueue(params = {}) {
      return request(`${API_ENDPOINTS.researchQueues}${queryString(params)}`, { requiresAuth: true });
    },

    saveTrainingPlanAssignment(data) {
      return request(API_ENDPOINTS.trainingPlanAssignment, {
        method: "POST",
        data: withDefaultUser(data),
        requiresAuth: true,
      });
    },

    getNotificationConfig(params = {}) {
      return request(`${API_ENDPOINTS.notificationConfig}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    saveNotificationConsent(data) {
      return request(API_ENDPOINTS.notificationConsent, {
        method: "POST",
        data: withDefaultUser(data),
        requiresAuth: true,
      });
    },

    listCourses() {
      return request(API_ENDPOINTS.courses);
    },

    getCourse(id) {
      return request(endpointWithId(API_ENDPOINTS.courseDetailBase, id));
    },

    getCourseProgress(id) {
      return request(endpointWithId(API_ENDPOINTS.courseProgressBase, id), { requiresAuth: true });
    },

    saveCourseProgress(id, data) {
      return request(endpointWithId(API_ENDPOINTS.courseProgressBase, id), {
        method: "POST",
        data: withDefaultUser(data),
        requiresAuth: true,
      });
    },

    listPrograms(params = {}) {
      return request(`${API_ENDPOINTS.programs}${queryString(params)}`, { requiresAuth: Boolean(params.include_drafts) });
    },

    getProgram(id, params = {}) {
      return request(`${endpointWithId(API_ENDPOINTS.programDetailBase, id)}${queryString(params)}`, { requiresAuth: Boolean(params.include_drafts) });
    },

    listProgramEntries(programId, params = {}) {
      return request(`${endpointWithId(API_ENDPOINTS.programEntriesBase, programId)}${queryString(withDefaultUser(params))}`, {
        requiresAuth: true,
      });
    },

    createProgramEntry(programId, data) {
      return request(endpointWithId(API_ENDPOINTS.programEntriesBase, programId), {
        method: "POST",
        data: withDefaultUser(data),
        requiresAuth: true,
      });
    },

    listAssessments(params = {}) {
      return request(`${API_ENDPOINTS.assessments}${queryString(params)}`);
    },

    getAssessment(id) {
      return request(`${API_ENDPOINTS.assessments}/${encodeURIComponent(id)}`);
    },

    createAssessmentResult(data) {
      const idempotencyKey = data.client_submission_id || "";
      return request(API_ENDPOINTS.assessmentResults, {
        method: "POST",
        data: withDefaultUser(data),
        header: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
        requiresAuth: true,
      });
    },

    listAssessmentResults(params = {}) {
      return request(`${API_ENDPOINTS.assessmentResults}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    getAssessmentResult(id, params = {}) {
      return request(`${API_ENDPOINTS.assessmentResults}/${encodeURIComponent(id)}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    getAssessmentProfilePosition(id, params = {}) {
      return request(`${endpointWithId(API_ENDPOINTS.assessmentProfilePositionBase, id)}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    createRelationshipEnrollment(data) {
      return request(`${API_ENDPOINTS.relationshipPilot}/enrollments`, {
        method: "POST",
        data,
        requiresAuth: true,
      });
    },

    listRelationshipEnrollments() {
      return request(`${API_ENDPOINTS.relationshipPilot}/enrollments`, { requiresAuth: true });
    },

    getRelationshipEnrollment(id) {
      return request(`${API_ENDPOINTS.relationshipPilot}/enrollments/${encodeURIComponent(id)}`, { requiresAuth: true });
    },

    createRelationshipReport(enrollmentId) {
      return request(`${API_ENDPOINTS.relationshipPilot}/enrollments/${encodeURIComponent(enrollmentId)}/report`, {
        method: "POST",
        requiresAuth: true,
      });
    },

    getRelationshipReport(id) {
      return request(`${API_ENDPOINTS.relationshipPilot}/reports/${encodeURIComponent(id)}`, { requiresAuth: true });
    },

    saveRelationshipHypothesisFeedback(id, hypothesisIndex, response) {
      return request(`${API_ENDPOINTS.relationshipPilot}/reports/${encodeURIComponent(id)}/hypotheses/${encodeURIComponent(hypothesisIndex)}`, {
        method: "PUT",
        data: { response },
        requiresAuth: true,
      });
    },

    confirmRelationshipReport(id) {
      return request(`${API_ENDPOINTS.relationshipPilot}/reports/${encodeURIComponent(id)}/confirm`, {
        method: "POST",
        requiresAuth: true,
      });
    },

    updateRelationshipReport(id, data) {
      return request(`${API_ENDPOINTS.relationshipPilot}/reports/${encodeURIComponent(id)}`, {
        method: "PATCH",
        data,
        requiresAuth: true,
      });
    },

    sendRelationshipReport(id) {
      return request(`${API_ENDPOINTS.relationshipPilot}/reports/${encodeURIComponent(id)}/send`, {
        method: "POST",
        requiresAuth: true,
      });
    },

    createRelationshipTask(enrollmentId, data) {
      const payload = { ...data };
      const idempotencyKey = payload.idempotency_key || "";
      delete payload.idempotency_key;
      return request(`${API_ENDPOINTS.relationshipPilot}/enrollments/${encodeURIComponent(enrollmentId)}/tasks`, {
        method: "POST",
        data: payload,
        header: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
        requiresAuth: true,
      });
    },

    getRelationshipResearchDashboard() {
      return request(`${API_ENDPOINTS.relationshipPilot}/researcher/dashboard`, { requiresAuth: true });
    },

    createRelationshipResearchNote(enrollmentId, data) {
      return request(`${API_ENDPOINTS.relationshipPilot}/enrollments/${encodeURIComponent(enrollmentId)}/notes`, {
        method: "POST",
        data,
        requiresAuth: true,
      });
    },

    createRelationshipNarrative(enrollmentId, data = {}) {
      return request(`${API_ENDPOINTS.relationshipPilot}/enrollments/${encodeURIComponent(enrollmentId)}/narrative`, {
        method: "POST",
        data,
        requiresAuth: true,
      });
    },

    confirmRelationshipNarrative(id) {
      return request(`${API_ENDPOINTS.relationshipPilot}/narratives/${encodeURIComponent(id)}/confirm`, {
        method: "POST",
        requiresAuth: true,
      });
    },

    getRelationshipNarrative(id) {
      return request(`${API_ENDPOINTS.relationshipPilot}/narratives/${encodeURIComponent(id)}`, { requiresAuth: true });
    },

    createRelationshipLongitudinal(enrollmentId, data) {
      const payload = { ...data };
      const idempotencyKey = payload.idempotency_key || "";
      delete payload.idempotency_key;
      return request(`${API_ENDPOINTS.relationshipPilot}/enrollments/${encodeURIComponent(enrollmentId)}/longitudinal`, {
        method: "POST",
        data: payload,
        header: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
        requiresAuth: true,
      });
    },

    getRelationshipGrowth(params = {}) {
      return request(`${API_ENDPOINTS.relationshipPilot}/growth${queryString(params)}`, { requiresAuth: true });
    },

    trackProductEvent(eventName, metadata = {}, clientEventId = "") {
      return request(API_ENDPOINTS.productEvents, {
        method: "POST",
        data: { event_name: eventName, metadata, client_event_id: clientEventId || undefined },
        requiresAuth: true,
      });
    },

    createCheckin(data) {
      const idempotencyKey = data.client_submission_id || "";
      return request(API_ENDPOINTS.checkins, {
        method: "POST",
        data: withDefaultUser(data),
        header: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
        requiresAuth: true,
      });
    },

    listCheckins(params = {}) {
      return request(`${API_ENDPOINTS.checkins}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    getWeeklyReport(params = {}) {
      return request(`${API_ENDPOINTS.weeklyReport}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    getGrowthOverview(params = {}) {
      return request(`${API_ENDPOINTS.growthOverview}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    createSupervision(data) {
      const idempotencyKey = data.client_submission_id || "";
      return request(API_ENDPOINTS.supervision, {
        method: "POST",
        data: withDefaultUser(data),
        header: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
        requiresAuth: true,
      });
    },

    getResearchQueue(params = {}) {
      return request(`${API_ENDPOINTS.researchQueues}${queryString(params)}`, { requiresAuth: true });
    },

    getResearchWorkItem(id) {
      return request(`${API_ENDPOINTS.researchWorkItems}/${encodeURIComponent(id)}`, { requiresAuth: true });
    },

    actOnResearchWorkItem(id, data) {
      const idempotencyKey = data.idempotency_key || "";
      return request(`${API_ENDPOINTS.researchWorkItems}/${encodeURIComponent(id)}/actions`, {
        method: "POST",
        data,
        header: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
        requiresAuth: true,
      });
    },

    getResearchWorkItemMetrics(params = {}) {
      return request(`${API_ENDPOINTS.researchWorkItemMetrics}${queryString(params)}`, { requiresAuth: true });
    },

    getActiveContentDescriptor(contentType, itemId) {
      return request(`${API_ENDPOINTS.contentGovernanceActive}/${encodeURIComponent(contentType)}/${encodeURIComponent(itemId)}`);
    },

    getAiQaConfig() {
      return request(API_ENDPOINTS.aiQaConfig);
    },

    getOfflineBenchmarkConfig() {
      return request(`${API_ENDPOINTS.offlineBenchmarks}/config`, { requiresAuth: true });
    },

    getResearchMethodologyPublicStatus() {
      return request(`${API_ENDPOINTS.researchMethodology}/public-status`);
    },

    getSecurityPublicStatus() {
      return request(`${API_ENDPOINTS.securityControls}/public-status`);
    },

    getReliabilityPublicStatus() {
      return request(`${API_ENDPOINTS.reliability}/public-status`);
    },

    getUXGovernancePublicStatus() {
      return request(`${API_ENDPOINTS.uxGovernance}/public-status`);
    },

    getOperationsGovernancePublicStatus() {
      return request(`${API_ENDPOINTS.operationsGovernance}/public-status`);
    },

    getParentAssessmentResult(id, params = {}) {
      return request(`${API_ENDPOINTS.parentAssessments}/${encodeURIComponent(id)}${queryString(withDefaultUser(params))}`, { requiresAuth: true });
    },

    createParentReportAction(id, data) {
      return request(`${API_ENDPOINTS.parentAssessments}/${encodeURIComponent(id)}/actions`, {
        method: "POST",
        data: withDefaultUser(data),
        requiresAuth: true,
      });
    },

    buildAdminExportUrl(params = {}) {
      return `${httpBaseUrl}${API_ENDPOINTS.adminExport}${queryString(params)}`;
    },
  };
}

module.exports = {
  API_ENDPOINTS,
  DEFAULT_CLOUD_ENV_ID,
  DEFAULT_CONTAINER_SERVICE,
  DEFAULT_HTTP_BASE_URL,
  createSafeHomeApi,
};
