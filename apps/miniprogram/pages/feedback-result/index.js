const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

Page({
  data: {
    diaryId: "",
    loading: true,
    errorMessage: "",
    feedback: null,
    labelsText: "",
    patternCards: [],
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
        patternCards: this.buildPatternCards(feedback),
        loading: false,
      });
    } catch (error) {
      this.setData({
        loading: false,
        errorMessage: error.message || "反馈生成失败，请确认 backend 是否已启动。",
      });
    }
  },

  buildPatternCards(feedback) {
    const labelsText = (feedback.labels || feedback.tags || []).join("、");

    return [
      {
        title: "这次的触发点",
        text: feedback.trigger_summary || "这次记录中可以先从具体场景开始观察。",
      },
      {
        title: "可能出现的互动线索",
        text: feedback.pattern_summary || labelsText || "暂时没有明显线索，可以先观察情绪强度和当时回应。",
      },
      {
        title: "可以练习的位置",
        text: feedback.alternative_response || "下次可以先停一下，再用一句更短的话表达期待。",
      },
    ];
  },

  openTrainingCard() {
    const tags = this.data.feedback && this.data.feedback.tags ? this.data.feedback.tags : [];
    wx.navigateTo({
      url: `/pages/training-card/index?tags=${encodeURIComponent(tags.join(","))}&diary_id=${encodeURIComponent(this.data.diaryId)}`,
    });
  },

  openSupervision() {
    wx.navigateTo({
      url: `/pages/supervision/index?diary_id=${encodeURIComponent(this.data.diaryId)}`,
    });
  },
});
