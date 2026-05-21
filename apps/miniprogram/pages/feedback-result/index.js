const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

Page({
  data: {
    diaryId: "",
    loading: true,
    errorMessage: "",
    feedback: null,
    labelsText: "",
  },

  onLoad(options) {
    const diaryId = decodeURIComponent(options.diary_id || "");
    this.setData({ diaryId });
    this.loadFeedback(diaryId);
  },

  async loadFeedback(diaryId) {
    if (!diaryId) {
      this.setData({ loading: false, errorMessage: "缺少记录 ID，请返回重新提交。" });
      return;
    }

    this.setData({ loading: true, errorMessage: "" });

    try {
      const feedback = await api.generateFeedback({ diary_id: diaryId });
      this.setData({
        feedback,
        labelsText: (feedback.labels || feedback.tags || []).join("、"),
        loading: false,
      });
    } catch (error) {
      this.setData({
        loading: false,
        errorMessage: error.message || "反馈生成失败，请确认 backend 是否已启动。",
      });
    }
  },

  openTrainingCard() {
    const tags = this.data.feedback && this.data.feedback.tags ? this.data.feedback.tags : [];
    wx.navigateTo({
      url: `/pages/training-card/index?tags=${encodeURIComponent(tags.join(","))}`,
    });
  },
});
