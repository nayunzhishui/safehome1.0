Page({
  startGoalSetting() {
    wx.navigateTo({ url: "/pages/goal-setting/index" });
  },

  startDiary() {
    wx.navigateTo({ url: "/pages/diary-form/index" });
  },

  openIntegrationTest() {
    wx.navigateTo({ url: "/pages/integration-test/index" });
  },
});
