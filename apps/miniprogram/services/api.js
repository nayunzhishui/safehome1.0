const { getAnonymousUserId } = require("./userIdentity");
const { DEFAULT_CLOUD_CONFIG, getCloudConfig } = require("./cloudConfig");

const DEFAULT_CONTAINER_SERVICE = DEFAULT_CLOUD_CONFIG.containerService;
const DEFAULT_CLOUD_ENV_ID = DEFAULT_CLOUD_CONFIG.cloudEnvId;
const DEFAULT_HTTP_BASE_URL = DEFAULT_CLOUD_CONFIG.httpBaseUrl;

const API_ENDPOINTS = {
  healthz: "/healthz",
  goals: "/api/goals",
  diaries: "/api/diaries",
  feedbackGenerate: "/api/feedback/generate",
  cards: "/api/cards",
  cardsRecommend: "/api/cards/recommend",
  assessments: "/api/assessments",
  assessmentResults: "/api/assessment-results",
  consent: "/api/consent",
  profile: "/api/profile",
  profileResults: "/api/profile-results",
  riskCheck: "/api/risk/check",
  riskReview: "/api/risk-review",
  modelInfo: "/api/model/info",
  parentAssessments: "/api/parent-assessments",
  checkins: "/api/checkins",
  weeklyReport: "/api/weekly-report",
  supervision: "/api/supervision",
  adminExport: "/api/admin/export",
};

function createSafeHomeApi(options = {}) {
  const cloudConfig = getCloudConfig(options);
  const containerService = cloudConfig.containerService;
  const cloudEnvId = cloudConfig.cloudEnvId;
  const httpBaseUrl = cloudConfig.httpBaseUrl;
  const defaultUserId = options.defaultUserId || getAnonymousUserId();

  function withDefaultUser(data = {}) {
    return {
      ...data,
      user_id: data.user_id || defaultUserId,
    };
  }

  function request(path, options = {}) {
    const method = options.method || "GET";
    const debug = {
      env: cloudEnvId,
      service: containerService,
      path,
      method,
    };

    return new Promise((resolve, reject) => {
      if (!wx.cloud || !wx.cloud.callContainer) {
        reject({
          code: "cloud_container_unavailable",
          message: `云托管调用不可用，请确认微信开发者工具已启用云开发环境。当前 env=${cloudEnvId}，service=${containerService}，path=${path}。`,
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
          ...(options.header || {}),
          "X-WX-SERVICE": containerService,
        },
        success(res) {
          const statusCode = res.statusCode || 0;
          const payload = res.data;

          if (statusCode < 200 || statusCode >= 300) {
            reject({
              code: payload && payload.error ? payload.error.code : "http_error",
              message: buildErrorMessage("请求失败", statusCode, payload),
              path,
              method,
              status: statusCode,
              statusCode,
              payload,
              debug,
            });
            return;
          }

          if (payload && payload.ok === false) {
            reject({
              code: payload.error ? payload.error.code : "api_error",
              message: payload.error ? payload.error.message : "接口返回错误",
              path,
              method,
              status: statusCode,
              statusCode,
              payload,
              debug,
            });
            return;
          }

          resolve(payload && payload.data !== undefined ? payload.data : payload);
        },
        fail(err) {
          reject({
            code: err.errCode || "network_error",
            message: `云托管调用失败，请检查云环境 ID、云托管服务名和服务状态。当前 env=${cloudEnvId}，service=${containerService}，path=${path}。`,
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

  function buildErrorMessage(prefix, statusCode, payload) {
    if (payload && payload.error && payload.error.message) {
      return `${prefix}（${statusCode}）：${payload.error.message}`;
    }
    if (payload && payload.message) {
      return `${prefix}（${statusCode}）：${payload.message}`;
    }
    if (typeof payload === "string" && payload) {
      return `${prefix}（${statusCode}）：${payload.slice(0, 80)}`;
    }
    return `${prefix}（${statusCode || "未知状态"}）`;
  }

  function queryString(params = {}) {
    const query = Object.keys(params)
      .filter((key) => params[key] !== undefined && params[key] !== "")
      .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
      .join("&");
    return query ? `?${query}` : "";
  }

  return {
    getDebugConfig() {
      return {
        cloudEnvId,
        containerService,
        httpBaseUrl,
        defaultUserId,
      };
    },

    healthz() {
      return request(API_ENDPOINTS.healthz);
    },

    createGoal(data) {
      return request(API_ENDPOINTS.goals, {
        method: "POST",
        data: withDefaultUser(data),
      });
    },

    listGoals(params = {}) {
      return request(`${API_ENDPOINTS.goals}${queryString(withDefaultUser(params))}`);
    },

    createConsent(data) {
      return request(API_ENDPOINTS.consent, {
        method: "POST",
        data: withDefaultUser(data),
      });
    },

    listConsentRecords(params = {}) {
      return request(`${API_ENDPOINTS.consent}${queryString(withDefaultUser(params))}`);
    },

    createDiary(data) {
      return request(API_ENDPOINTS.diaries, {
        method: "POST",
        data: withDefaultUser(data),
      });
    },

    listDiaries(params = {}) {
      return request(`${API_ENDPOINTS.diaries}${queryString(withDefaultUser(params))}`);
    },

    generateFeedback(data) {
      return request(API_ENDPOINTS.feedbackGenerate, {
        method: "POST",
        data: withDefaultUser(data),
      });
    },

    createProfile(data) {
      return request(API_ENDPOINTS.profile, {
        method: "POST",
        data: withDefaultUser(data),
      });
    },

    getProfileResult(id, params = {}) {
      return request(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}${queryString(withDefaultUser(params))}`);
    },

    getProfileVisuals(id, params = {}) {
      return request(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/visuals${queryString(withDefaultUser(params))}`);
    },

    listProfileFollowups(id, params = {}) {
      return request(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/followups${queryString(withDefaultUser(params))}`);
    },

    createProfileFollowup(id, data) {
      return request(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/followups`, {
        method: "POST",
        data: withDefaultUser(data),
      });
    },

    listProfileSandplay(id, params = {}) {
      return request(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/sandplay${queryString(withDefaultUser(params))}`);
    },

    createProfileSandplay(id, data) {
      return request(`${API_ENDPOINTS.profileResults}/${encodeURIComponent(id)}/sandplay`, {
        method: "POST",
        data: withDefaultUser(data),
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

    listAssessments(params = {}) {
      return request(`${API_ENDPOINTS.assessments}${queryString(params)}`);
    },

    getAssessment(id) {
      return request(`${API_ENDPOINTS.assessments}/${encodeURIComponent(id)}`);
    },

    createAssessmentResult(data) {
      return request(API_ENDPOINTS.assessmentResults, {
        method: "POST",
        data: withDefaultUser(data),
      });
    },

    listAssessmentResults(params = {}) {
      return request(`${API_ENDPOINTS.assessmentResults}${queryString(withDefaultUser(params))}`);
    },

    createCheckin(data) {
      return request(API_ENDPOINTS.checkins, {
        method: "POST",
        data: withDefaultUser(data),
      });
    },

    listCheckins(params = {}) {
      return request(`${API_ENDPOINTS.checkins}${queryString(withDefaultUser(params))}`);
    },

    getWeeklyReport(params = {}) {
      return request(`${API_ENDPOINTS.weeklyReport}${queryString(withDefaultUser(params))}`);
    },

    createSupervision(data) {
      return request(API_ENDPOINTS.supervision, {
        method: "POST",
        data: withDefaultUser(data),
      });
    },

    getParentAssessmentResult(id, params = {}) {
      return request(`${API_ENDPOINTS.parentAssessments}/${encodeURIComponent(id)}${queryString(withDefaultUser(params))}`);
    },

    createParentReportAction(id, data) {
      return request(`${API_ENDPOINTS.parentAssessments}/${encodeURIComponent(id)}/actions`, {
        method: "POST",
        data: withDefaultUser(data),
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
