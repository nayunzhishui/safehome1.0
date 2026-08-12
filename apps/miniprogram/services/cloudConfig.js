const CLOUD_CONFIG_STORAGE_KEY = "safehome_cloud_config";

const DEFAULT_CLOUD_CONFIG = Object.freeze({
  profile: "development",
  cloudEnvId: "",
  containerService: "local-flask",
  httpBaseUrl: "",
  localHttpBaseUrl: "http://127.0.0.1:5000",
  transport: "local-http",
  useLocalHttp: true,
});

const DEVELOPMENT_CLOUD_TARGET = Object.freeze({
  profile: "development",
  cloudEnvId: "prod-d3gl35otiaa7c8d24",
  containerService: "flask-gh3l",
  httpBaseUrl: "https://flask-gh3l-261352-9-1436233118.sh.run.tcloudbase.com",
  localHttpBaseUrl: "http://127.0.0.1:5000",
  transport: "cloud-container",
  useLocalHttp: false,
});

function configError(detail) {
  const error = new Error("连接配置不可用，请在调试页检查目标后重试。");
  error.code = "cloud_config_invalid";
  error.userMessage = "连接配置不可用，请检查配置后重试。";
  error.detail = detail;
  error.recoverable = true;
  return error;
}

function readExtConfig() {
  try {
    if (typeof wx === "undefined" || !wx.getExtConfigSync) return {};
    const extConfig = wx.getExtConfigSync() || {};
    return extConfig.safehomeCloud || extConfig.cloudConfig || {};
  } catch (error) {
    throw configError("无法读取 extConfig");
  }
}

function readStorageConfig() {
  try {
    if (typeof wx === "undefined" || !wx.getStorageSync) return {};
    return wx.getStorageSync(CLOUD_CONFIG_STORAGE_KEY) || {};
  } catch (error) {
    throw configError("无法读取本地连接配置");
  }
}

function isLoopbackUrl(value) {
  return /^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?\/?$/i.test(String(value || ""));
}

function normalizeDevelopmentConfig(config = {}) {
  const transport = config.transport || (config.useLocalHttp === false ? "cloud-container" : "local-http");
  if (transport === "cloud-container") {
    const cloudEnvId = config.cloudEnvId || "";
    const containerService = config.containerService || "";
    if (
      cloudEnvId !== DEVELOPMENT_CLOUD_TARGET.cloudEnvId
      || containerService !== DEVELOPMENT_CLOUD_TARGET.containerService
    ) {
      throw configError("development 云目标未登记");
    }
    return DEVELOPMENT_CLOUD_TARGET;
  }
  if (transport !== "local-http") {
    throw configError("development transport 不受支持");
  }
  const localHttpBaseUrl = config.localHttpBaseUrl || DEFAULT_CLOUD_CONFIG.localHttpBaseUrl;
  if (!isLoopbackUrl(localHttpBaseUrl)) {
    throw configError("development 本地 HTTP 必须使用 loopback 地址");
  }
  return {
    ...DEFAULT_CLOUD_CONFIG,
    localHttpBaseUrl: localHttpBaseUrl.replace(/\/$/, ""),
  };
}

function getCloudConfig(overrides = {}) {
  return normalizeDevelopmentConfig({
    ...readExtConfig(),
    ...readStorageConfig(),
    ...overrides,
  });
}

function saveCloudConfig(config = {}) {
  const nextConfig = normalizeDevelopmentConfig(config);
  if (typeof wx !== "undefined" && wx.setStorageSync) {
    wx.setStorageSync(CLOUD_CONFIG_STORAGE_KEY, nextConfig);
  }
  return nextConfig;
}

function migrateLegacyCloudConfig() {
  return false;
}

module.exports = {
  CLOUD_CONFIG_STORAGE_KEY,
  DEFAULT_CLOUD_CONFIG,
  DEVELOPMENT_CLOUD_TARGET,
  getCloudConfig,
  saveCloudConfig,
  migrateLegacyCloudConfig,
};
