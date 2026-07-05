const CLOUD_CONFIG_STORAGE_KEY = "safehome_cloud_config";

const DEFAULT_CLOUD_CONFIG = {
  cloudEnvId: "prod-d3gl35otiaa7c8d24",
  containerService: "flask-gh3l",
  httpBaseUrl: "https://flask-gh3l-261352-9-1436233118.sh.run.tcloudbase.com",
  localHttpBaseUrl: "http://127.0.0.1:5000",
  useLocalHttp: false,
};

function readExtConfig() {
  try {
    if (typeof wx === "undefined" || !wx.getExtConfigSync) {
      return {};
    }
    const extConfig = wx.getExtConfigSync() || {};
    return extConfig.safehomeCloud || extConfig.cloudConfig || {};
  } catch (error) {
    return {};
  }
}

function readStorageConfig() {
  try {
    if (typeof wx === "undefined" || !wx.getStorageSync) {
      return {};
    }
    return wx.getStorageSync(CLOUD_CONFIG_STORAGE_KEY) || {};
  } catch (error) {
    return {};
  }
}

function normalizeConfig(config = {}) {
  return {
    cloudEnvId: config.cloudEnvId || config.env || DEFAULT_CLOUD_CONFIG.cloudEnvId,
    containerService: config.containerService || config.service || DEFAULT_CLOUD_CONFIG.containerService,
    httpBaseUrl: config.httpBaseUrl || config.baseUrl || DEFAULT_CLOUD_CONFIG.httpBaseUrl,
    localHttpBaseUrl: config.localHttpBaseUrl || DEFAULT_CLOUD_CONFIG.localHttpBaseUrl,
    useLocalHttp: config.useLocalHttp === true || config.transport === "local-http",
  };
}

function getCloudConfig(overrides = {}) {
  return normalizeConfig({
    ...readExtConfig(),
    ...readStorageConfig(),
    ...overrides,
  });
}

function saveCloudConfig(config = {}) {
  const nextConfig = normalizeConfig(config);
  if (typeof wx !== "undefined" && wx.setStorageSync) {
    wx.setStorageSync(CLOUD_CONFIG_STORAGE_KEY, nextConfig);
  }
  return nextConfig;
}

module.exports = {
  CLOUD_CONFIG_STORAGE_KEY,
  DEFAULT_CLOUD_CONFIG,
  getCloudConfig,
  saveCloudConfig,
};
