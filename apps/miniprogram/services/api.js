const DEFAULT_CONTAINER_SERVICE = "flask-gh3l";
const DEFAULT_CLOUD_ENV_ID = "prod-d3gl35otiaa7c8d24";
// 仅用于 wx.downloadFile / 分享链接 / 二维码等需要完整 HTTPS URL 的场景；
// 常规 API 调用仍通过 wx.cloud.callContainer，不走此域名。
const DEFAULT_HTTP_BASE_URL = "https://flask-gh3l-261352-9-1436233118.sh.run.tcloudbase.com";
const DEFAULT_USER_ID = "demo-parent";

const API_ENDPOINTS = {
  healthz: "/healthz",
  goals: "/api/goals",
  diaries: "/api/diaries",
  feedbackGenerate: "/api/feedback/generate",
  cards: "/api/cards",
  cardsRecommend: "/api/cards/recommend",
  assessments: "/api/assessments",
  assessmentResults: "/api/assessment-results",
  profile: "/api/profile",
  riskCheck: "/api/risk/check",
  modelInfo: "/api/model/info",
  checkins: "/api/checkins",
  weeklyReport: "/api/weekly-report",
  supervision: "/api/supervision",
  adminExport: "/api/admin/export",
};

function createSafeHomeApi(options = {}) {
  const containerService = options.containerService || DEFAULT_CONTAINER_SERVICE;
  const cloudEnvId = options.cloudEnvId || DEFAULT_CLOUD_ENV_ID;
  const httpBaseUrl = options.httpBaseUrl || DEFAULT_HTTP_BASE_URL;
  const defaultUserId = options.defaultUserId || DEFAULT_USER_ID;

  function withDefaultUser(data = {}) {
    return {
      ...data,
      user_id: data.user_id || defaultUserId,
    };
  }

  function request(path, options = {}) {
    return new Promise((resolve, reject) => {
      if (!wx.cloud || !wx.cloud.callContainer) {
        reject({
          code: "cloud_container_unavailable",
          message: "云托管调用不可用，请确认微信开发者工具已启用云开发环境。",
        });
        return;
      }

      wx.cloud.callContainer({
        config: {
          env: cloudEnvId,
        },
        path,
        method: options.method || "GET",
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
              statusCode,
              payload,
            });
            return;
          }

          if (payload && payload.ok === false) {
            reject({
              code: payload.error ? payload.error.code : "api_error",
              message: payload.error ? payload.error.message : "接口返回错误",
              statusCode,
            });
            return;
          }

          resolve(payload && payload.data !== undefined ? payload.data : payload);
        },
        fail(err) {
          reject({
            code: err.errCode || "network_error",
            message: err.errMsg || "云托管调用失败",
            detail: err,
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
      return request(`${API_ENDPOINTS.goals}${queryString(params)}`);
    },

    createDiary(data) {
      return request(API_ENDPOINTS.diaries, {
        method: "POST",
        data: withDefaultUser(data),
      });
    },

    listDiaries(params = {}) {
      return request(`${API_ENDPOINTS.diaries}${queryString(params)}`);
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

    checkRisk(data) {
      return request(API_ENDPOINTS.riskCheck, {
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
      return request(`${API_ENDPOINTS.assessmentResults}${queryString(params)}`);
    },

    createCheckin(data) {
      return request(API_ENDPOINTS.checkins, {
        method: "POST",
        data: withDefaultUser(data),
      });
    },

    listCheckins(params = {}) {
      return request(`${API_ENDPOINTS.checkins}${queryString(params)}`);
    },

    getWeeklyReport(params = {}) {
      return request(`${API_ENDPOINTS.weeklyReport}${queryString(params)}`);
    },

    createSupervision(data) {
      return request(API_ENDPOINTS.supervision, {
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
  DEFAULT_USER_ID,
  createSafeHomeApi,
};
