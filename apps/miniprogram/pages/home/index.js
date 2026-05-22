Page({
  startGoalSetting() {
    wx.navigateTo({ url: "/pages/goal-setting/index" });
  },

  startDiary() {
    wx.navigateTo({ url: "/pages/diary-form/index" });
  },

  openWeeklyReport() {
    wx.navigateTo({ url: "/pages/weekly-report/index" });
  },

  openIntegrationTest() {
    wx.navigateTo({ url: "/pages/integration-test/index" });
  },
});
