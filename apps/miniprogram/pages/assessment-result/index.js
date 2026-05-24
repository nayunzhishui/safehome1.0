const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

Page({
  data: {
    resultId: "",
    worksheetId: "",
    result: null,
    worksheet: null,
    loading: true,
    errorMessage: "",
    totalScoreText: "",
    recommendedCardsText: "",
  },

  onLoad(options) {
    this.setData({
      resultId: decodeURIComponent(options.id || ""),
      worksheetId: decodeURIComponent(options.worksheet_id || ""),
    });
    this.loadResult();
  },

  async loadResult() {
    this.setData({ loading: true, errorMessage: "" });
    try {
      const [results, worksheet] = await Promise.all([
        api.listAssessmentResults({ limit: 20 }),
        this.data.worksheetId ? api.getAssessment(this.data.worksheetId) : Promise.resolve(null),
      ]);
      const result = (results.items || []).find((item) => item.id === this.data.resultId) || (results.items || [])[0];
      this.setData({
        result,
        worksheet,
        loading: false,
        totalScoreText: result && result.total_score !== null && result.total_score !== undefined ? `${result.total_score}` : "本工作表不自动计分",
        recommendedCardsText: worksheet && worksheet.recommended_card_ids && worksheet.recommended_card_ids.length ? worksheet.recommended_card_ids.join("、") : "暂无固定推荐",
      });
    } catch (error) {
      this.setData({
        loading: false,
        errorMessage: error.message || "结果读取失败，请确认 backend 是否已启动。",
      });
    }
  },

  openRecommendedCards() {
    wx.switchTab({ url: "/pages/training/index" });
  },

  backToAssessment() {
    wx.navigateBack({ delta: 2 });
  },
});
