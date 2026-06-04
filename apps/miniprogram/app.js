const { getCloudConfig } = require("./services/cloudConfig");

App({
  onLaunch() {
    if (wx.cloud && wx.cloud.init) {
      const cloudConfig = getCloudConfig();
      wx.cloud.init({
        env: cloudConfig.cloudEnvId,
        traceUser: true,
      });
    }
  },
});
