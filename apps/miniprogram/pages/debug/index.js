const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

function toText(value) {
  if (value === undefined || value === null) {
    return "";
  }
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value, null, 2);
}

function formatError(error) {
  return {
    code: error.code || "",
    message: error.message || "请求失败",
    debugText: toText(error.debug || {}),
    detailText: toText(error.detail || error.payload || {}),
  };
}

Page({
  data: {
    config: api.getDebugConfig(),
    status: "idle",
    resultTitle: "等待测试",
    resultText: "请点击下面按钮测试云托管入口。",
    lastError: null,
  },

  async runCheck(title, action) {
    this.setData({
      status: "running",
      resultTitle: title,
      resultText: "请求中...",
      lastError: null,
    });

    try {
      const result = await action();
      this.setData({
        status: "success",
        resultTitle: `${title}通过`,
        resultText: toText(result),
      });
    } catch (error) {
      this.setData({
        status: "error",
        resultTitle: `${title}失败`,
        resultText: "",
        lastError: formatError(error),
      });
    }
  },

  testHealthz() {
    return this.runCheck("healthz 测试", () => api.healthz());
  },

  testRiskCheck() {
    return this.runCheck("risk/check 测试", () =>
      api.checkRisk({
        text: "我今天有些着急，想先停下来观察一下。",
        source: "debug",
      }),
    );
  },

  testProfile() {
    return this.runCheck("profile 最小请求测试", () =>
      api.createProfile({
        scores: {
          test_anxiety: 3.2,
          iu_score: 3.1,
          f_score: 2.2,
          self_compassion: 3.4,
        },
        free_text: "考试前有些担心，想练习一次情绪命名。",
      }),
    );
  },
});
