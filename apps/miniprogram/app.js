App({
  onLaunch() {
    if (wx.cloud && wx.cloud.init) {
      wx.cloud.init({
        env: "prod-d3gl35otiaa7c8d24",
        traceUser: true,
      });
    }
  },
});
