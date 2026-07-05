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
  programs: "/api/programs",
  programDetailBase: "/api/programs/:id",
  assessments: "/api/assessments",
  assessmentResults: "/api/assessment-results",
  assessmentProfilePositionBase: "/api/assessment-results/:id/profile-position",
  consent: "/api/consent",
  profile: "/api/profile",
  profileStats: "/api/profile/stats",
  profileResults: "/api/profile-results",
  messages: "/api/messages",
  riskCheck: "/api/risk/check",
  riskReview: "/api/risk-review",
  modelInfo: "/api/model/info",
  authRegister: "/api/auth/register",
  authLogin: "/api/auth/login",
  authWechatLogin: "/api/auth/wechat-login",
  authLogout: "/api/auth/logout",
  authMe: "/api/auth/me",
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

    login(data) {
      return request(API_ENDPOINTS.authLogin, {
        method: "POST",
        data,
      }).then((result) => {
        if (result && result.token) {
          wx.setStorageSync("auth_token", result.token);
          wx.setStorageSync("auth_user", result.user || null);
          wx.removeStorageSync("safehome_anonymous_user_id");
        }
        return result;
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

    createEmotionThermometer(data) {
      return request(API_ENDPOINTS.emotionThermometer, {
        method: "POST",
        data: withDefaultUser(data),
      });
    },

    getEmotionThermometerDay(params = {}) {
      return request(`${API_ENDPOINTS.emotionThermometerDay}${queryString(withDefaultUser(params))}`);
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

    getProfileStats(params = {}) {
      return request(`${API_ENDPOINTS.profileStats}${queryString(withDefaultUser(params))}`);
    },

    listMessages(params = {}) {
      return request(`${API_ENDPOINTS.messages}${queryString(withDefaultUser(params))}`);
    },

    getMessage(id, params = {}) {
      return request(`${API_ENDPOINTS.messages}/${encodeURIComponent(id)}${queryString(withDefaultUser(params))}`);
    },

    markMessageRead(id, data = {}) {
      return request(`${API_ENDPOINTS.messages}/${encodeURIComponent(id)}/read`, {
        method: "POST",
        data: withDefaultUser(data),
      });
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

    getTrainingPlan(params = {}) {
      return request(`${API_ENDPOINTS.trainingPlan}${queryString(withDefaultUser(params))}`);
    },

    listPrograms() {
      return request(API_ENDPOINTS.programs);
    },

    getProgram(id) {
      return request(endpointWithId(API_ENDPOINTS.programDetailBase, id));
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

    getAssessmentProfilePosition(id, params = {}) {
      return request(`${endpointWithId(API_ENDPOINTS.assessmentProfilePositionBase, id)}${queryString(withDefaultUser(params))}`);
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
