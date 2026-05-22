const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

Page({
  data: {
    loading: true,
    errorMessage: "",
    diaryId: "",
    tags: [],
    cards: [],
    practiceMessage: "",
  },

  onLoad(options) {
    const tagsText = decodeURIComponent(options.tags || "");
    const tags = tagsText ? tagsText.split(",").filter(Boolean) : [];
    this.setData({
      tags,
      diaryId: decodeURIComponent(options.diary_id || ""),
    });
    this.loadCards(tags);
  },

  async loadCards(tags) {
    this.setData({ loading: true, errorMessage: "", practiceMessage: "" });

    try {
      const result = await api.recommendCards({ tags, limit: 3 });
      this.setData({
        cards: (result.items || []).map((card) => ({
          ...card,
          tagsText: (card.tags || []).join("、"),
          durationText: card.duration_minutes ? `${card.duration_minutes} 分钟` : "1 次小练习",
          reflectionPrompt: "练习后可以简单记一句：这次我先做了什么，情绪有没有一点变化？",
        })),
        loading: false,
      });
    } catch (error) {
      this.setData({
        loading: false,
        errorMessage: error.message || "训练卡获取失败，请确认 backend 是否已启动。",
      });
    }
  },

  choosePractice(event) {
    const cardId = event.currentTarget.dataset.id || "";
    const title = event.currentTarget.dataset.title || "这张训练卡";
    wx.navigateTo({
      url: `/pages/checkin/index?card_id=${encodeURIComponent(cardId)}&card_title=${encodeURIComponent(title)}&diary_id=${encodeURIComponent(this.data.diaryId)}`,
    });
  },
});
