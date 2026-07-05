const { createSafeHomeApi } = require("../../services/api");
const { DEFAULT_CLOUD_CONFIG, saveCloudConfig } = require("../../services/cloudConfig");

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
    config: {},
    status: "idle",
    resultTitle: "等待测试",
    resultText: "请点击下面按钮测试云托管入口。",
    lastError: null,
  },

  onLoad() {
    this.refreshApi();
  },

  refreshApi() {
    this.api = createSafeHomeApi();
    this.setData({ config: this.api.getDebugConfig() });
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
    return this.runCheck("healthz 测试", () => this.api.healthz());
  },

  useLocalBackend() {
    saveCloudConfig({
      ...DEFAULT_CLOUD_CONFIG,
      useLocalHttp: true,
      transport: "local-http",
      localHttpBaseUrl: "http://127.0.0.1:5000",
    });
    this.refreshApi();
    this.setData({
      status: "idle",
      resultTitle: "已切换本地 5000",
      resultText: "现在会用 wx.request 请求 http://127.0.0.1:5000。请点击“测试 assessments”。",
      lastError: null,
    });
    wx.showToast({ title: "已切换本地后端", icon: "success" });
  },

  useCloudBackend() {
    saveCloudConfig({
      ...DEFAULT_CLOUD_CONFIG,
      useLocalHttp: false,
      transport: "cloud-container",
    });
    this.refreshApi();
    this.setData({
      status: "idle",
      resultTitle: "已切回云托管",
      resultText: "现在会用 wx.cloud.callContainer 请求 CloudBase 云托管。",
      lastError: null,
    });
    wx.showToast({ title: "已切回云托管", icon: "success" });
  },

  testAssessments() {
    return this.runCheck("assessments 测试", () => this.api.listAssessments());
  },

  testRiskCheck() {
    return this.runCheck("risk/check 测试", () =>
      this.api.checkRisk({
        text: "我今天有些着急，想先停下来观察一下。",
        source: "debug",
      }),
    );
  },

  testProfile() {
    return this.runCheck("profile 最小请求测试", () =>
      this.api.createProfile({
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
