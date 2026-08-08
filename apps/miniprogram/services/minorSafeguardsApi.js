const { getCloudConfig } = require("./cloudConfig");

function createRequestId() {
  return `minor-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

function normalizeError({ payload = {}, statusCode = 0, path = "", method = "GET", requestId = "" }) {
  const error = payload.error || {};
  const code = String(error.code || (statusCode === 401 ? "auth_required" : "minor_safeguard_error"));
  const fallback = statusCode === 401
    ? "请先登录后继续。"
    : statusCode === 403
      ? "当前账号没有权限执行这个操作。"
      : statusCode === 429
        ? "操作有点频繁，请稍后再试。"
        : statusCode >= 500
          ? "服务暂时没有响应，请稍后再试。"
          : "参与者保护设置暂未完成，请稍后重试。";
  return {
    code,
    message: error.message || fallback,
    status: statusCode,
    statusCode,
    details: error.details || null,
    path,
    method,
    requestId: String(payload.request_id || requestId || ""),
    retryable: statusCode === 0 || statusCode === 429 || statusCode >= 500,
  };
}

function clearAuthSession() {
  wx.removeStorageSync("auth_token");
  wx.removeStorageSync("auth_user");
}

function request(path, method = "GET", data = {}) {
  const cloudConfig = getCloudConfig();
  const token = wx.getStorageSync("auth_token") || "";
  const requestId = createRequestId();
  if (!token) {
    return Promise.reject(normalizeError({
      payload: { error: { code: "auth_required", message: "请先登录后继续。" } },
      statusCode: 401,
      path,
      method,
      requestId,
    }));
  }

  return new Promise((resolve, reject) => {
    const header = {
      "content-type": "application/json",
      Authorization: `Bearer ${token}`,
      "X-Request-ID": requestId,
    };
    const handle = (res) => {
      const payload = res.data || {};
      if (res.statusCode >= 200 && res.statusCode < 300 && payload.ok !== false) {
        resolve(payload.data !== undefined ? payload.data : payload);
        return;
      }
      if (res.statusCode === 401 && String(payload.error && payload.error.code || "") !== "invalid_credentials") {
        clearAuthSession();
      }
      reject(normalizeError({ payload, statusCode: res.statusCode || 0, path, method, requestId }));
    };
    const fail = () => reject(normalizeError({
      payload: { error: { code: "network_error", message: "现在没能连上服务，请检查网络后再试。" } },
      statusCode: 0,
      path,
      method,
      requestId,
    }));

    if (cloudConfig.useLocalHttp) {
      wx.request({
        url: `${cloudConfig.localHttpBaseUrl}${path}`,
        method,
        data,
        header,
        success: handle,
        fail,
      });
      return;
    }

    if (!wx.cloud || !wx.cloud.callContainer) {
      reject(normalizeError({
        payload: { error: { code: "cloud_container_unavailable", message: "当前环境暂时不能连接云服务。" } },
        statusCode: 0,
        path,
        method,
        requestId,
      }));
      return;
    }
    wx.cloud.callContainer({
      config: { env: cloudConfig.cloudEnvId },
      path,
      method,
      data,
      header: { ...header, "X-WX-SERVICE": cloudConfig.containerService },
      success: handle,
      fail,
    });
  });
}

module.exports = {
  getMinorSafeguardStatus(childUserId = "") {
    const query = childUserId ? `?child_user_id=${encodeURIComponent(childUserId)}` : "";
    return request(`/api/minor-safeguards/status${query}`);
  },
  listFamilyMembers() {
    return request("/api/family/members");
  },
  createFamilyBindCode(relationLabel = "家长") {
    return request("/api/family/create-bind-code", "POST", { relation_label: relationLabel });
  },
  bindStudent(bindCode) {
    return request("/api/family/bind-student", "POST", { bind_code: String(bindCode || "").trim() });
  },
  confirmAge(ageBand) {
    return request("/api/minor-safeguards/age-confirmation", "POST", { age_band: ageBand });
  },
  updateChildAssent(assented, withdraw = false) {
    return request("/api/minor-safeguards/child-assent", "POST", { assented: !!assented, withdraw: !!withdraw });
  },
  updateGuardianConsent(childUserId, agreed) {
    return request("/api/minor-safeguards/guardian-consent", "POST", { child_user_id: childUserId, agreed: !!agreed });
  },
};
