const { getCloudConfig } = require("./cloudConfig");

function request(path, method = "GET", data = {}) {
  const cloudConfig = getCloudConfig();
  const token = wx.getStorageSync("auth_token") || "";
  if (!token) {
    return Promise.reject({ code: "auth_required", message: "请先登录后继续。" });
  }

  return new Promise((resolve, reject) => {
    const header = {
      "content-type": "application/json",
      Authorization: `Bearer ${token}`,
    };
    const handle = (res) => {
      const payload = res.data || {};
      if (res.statusCode >= 200 && res.statusCode < 300 && payload.ok !== false) {
        resolve(payload.data !== undefined ? payload.data : payload);
        return;
      }
      const error = payload.error || {};
      reject({
        code: error.code || "minor_safeguard_error",
        message: error.message || "年龄保护设置暂未完成，请稍后重试。",
        status: res.statusCode || 0,
        details: error.details || null,
      });
    };

    if (cloudConfig.useLocalHttp) {
      wx.request({
        url: `${cloudConfig.localHttpBaseUrl}${path}`,
        method,
        data,
        header,
        success: handle,
        fail: () => reject({ code: "network_error", message: "现在没能连上服务，请检查网络后再试。" }),
      });
      return;
    }

    if (!wx.cloud || !wx.cloud.callContainer) {
      reject({ code: "cloud_container_unavailable", message: "当前环境暂时不能连接云服务。" });
      return;
    }
    wx.cloud.callContainer({
      config: { env: cloudConfig.cloudEnvId },
      path,
      method,
      data,
      header: { ...header, "X-WX-SERVICE": cloudConfig.containerService },
      success: handle,
      fail: () => reject({ code: "network_error", message: "现在没能连上服务，请检查网络后再试。" }),
    });
  });
}

module.exports = {
  getMinorSafeguardStatus(childUserId = "") {
    const query = childUserId ? `?child_user_id=${encodeURIComponent(childUserId)}` : "";
    return request(`/api/minor-safeguards/status${query}`);
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
