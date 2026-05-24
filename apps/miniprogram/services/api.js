const DEFAULT_BASE_URL = "https://flask-gh3l-261352-9-1436233118.sh.run.tcloudbase.com";
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
  checkins: "/api/checkins",
  weeklyReport: "/api/weekly-report",
  supervision: "/api/supervision",
  adminExport: "/api/admin/export",
};

function createSafeHomeApi(options = {}) {
  const baseUrl = options.baseUrl || DEFAULT_BASE_URL;
  const defaultUserId = options.defaultUserId || DEFAULT_USER_ID;

  function withDefaultUser(data = {}) {
    return {
      ...data,
      user_id: data.user_id || defaultUserId,
    };
  }

  function request(path, options = {}) {
    return new Promise((resolve, reject) => {
      wx.request({
        url: `${baseUrl}${path}`,
        method: options.method || "GET",
        data: options.data || {},
        header: {
          "content-type": "application/json",
          ...(options.header || {}),
        },
        success(res) {
          const statusCode = res.statusCode || 0;
          const payload = res.data;

          if (statusCode < 200 || statusCode >= 300) {
            reject({
              code: payload && payload.error ? payload.error.code : "http_error",
              message: payload && payload.error ? payload.error.message : "请求失败",
              statusCode,
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
        fail(error) {
          reject({
            code: "network_error",
            message: error.errMsg || "网络请求失败",
            detail: error,
          });
        },
      });
    });
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
      return `${baseUrl}${API_ENDPOINTS.adminExport}${queryString(params)}`;
    },
  };
}

module.exports = {
  API_ENDPOINTS,
  DEFAULT_BASE_URL,
  DEFAULT_USER_ID,
  createSafeHomeApi,
};
