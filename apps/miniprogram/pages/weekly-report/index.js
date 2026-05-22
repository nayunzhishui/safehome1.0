const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

function formatPairs(items = []) {
  return items.map((item) => ({
    name: item[0],
    count: item[1],
  }));
}

Page({
  data: {
    loading: true,
    errorMessage: "",
    report: null,
    frequentScenes: [],
    frequentEmotions: [],
    commonPatterns: [],
    completedCardsText: "",
  },

  onLoad() {
    this.loadReport();
  },

  async loadReport() {
    this.setData({ loading: true, errorMessage: "" });

    try {
      const report = await api.getWeeklyReport();
      this.setData({
        report,
        frequentScenes: formatPairs(report.frequent_scenes || []),
        frequentEmotions: formatPairs(report.frequent_emotions || []),
        commonPatterns: formatPairs(report.common_patterns || []),
        completedCardsText: (report.completed_cards || []).join("、"),
        loading: false,
      });
    } catch (error) {
      this.setData({
        loading: false,
        errorMessage: error.message || "周度复盘获取失败，请确认 backend 是否已启动。",
      });
    }
  },

  refreshReport() {
    this.loadReport();
  },

  goHome() {
    wx.reLaunch({ url: "/pages/home/index" });
  },
});
