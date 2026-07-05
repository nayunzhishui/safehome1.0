const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

Page({
  data: {
    loading: true,
    errorMessage: "",
    errorDetail: "",
    diaryId: "",
    tags: [],
    tagsText: "",
    cardIds: [],
    cards: [],
    practiceMessage: "",
  },

  onLoad(options) {
    const tagsText = decodeURIComponent(options.tags || "");
    const tags = tagsText ? tagsText.split(",").filter(Boolean) : [];
    const cardIdsText = decodeURIComponent(options.card_ids || "");
    const cardIds = cardIdsText ? cardIdsText.split(",").filter(Boolean) : [];
    this.setData({
      tags,
      tagsText: tags.join("、"),
      cardIds,
      diaryId: decodeURIComponent(options.diary_id || ""),
    });
    this.loadCards(tags, cardIds);
  },

  async loadCards(tags, cardIds = []) {
    this.setData({ loading: true, errorMessage: "", errorDetail: "", practiceMessage: "" });

    try {
      const result = cardIds.length ? await api.listCards() : await api.recommendCards({ tags, limit: 3 });
      const allCards = result.items || [];
      const cardMap = {};
      allCards.forEach((card) => {
        cardMap[card.id] = card;
      });
      const selectedCards = cardIds.length ? cardIds.map((cardId) => cardMap[cardId]).filter(Boolean) : allCards.slice(0, 3);
      this.setData({
        cards: selectedCards.map((card, index) => this.formatCard(card, index)),
        loading: false,
      });
    } catch (error) {
      this.setData({
        loading: false,
        errorMessage: "训练卡暂时没有加载成功",
        errorDetail: error.message || "请检查网络后再试一次。",
      });
    }
  },

  formatCard(card, index) {
    return {
      ...card,
      orderText: `0${index + 1}`,
      typeLabel: this.getTypeLabel(card.type),
      tagsText: (card.tags || []).join("、"),
      durationText: card.duration_minutes ? `${card.duration_minutes} 分钟` : "1 次小练习",
      scenarioText: (card.suitable_for || [])[0] || "适合这次记录中的互动线索",
      todayGoal: card.purpose || "今天先完成一个能做到的小回应动作。",
      stepsList: (card.steps || []).map((step, stepIndex) => ({
        text: step,
        numberText: `${stepIndex + 1}`,
      })),
      reflectionPrompt: (card.reflection_questions || [])[0] || "练习后可以简单记一句：这次我先做了什么，情绪有没有一点变化？",
    };
  },

  getTypeLabel(type) {
    const labels = {
      emotion_awareness: "情绪觉察",
      behavior_substitution: "行为替代",
      cognitive_flexibility: "想法调整",
      nonjudgmental_response: "非评判回应",
    };
    return labels[type] || "陪伴练习";
  },

  choosePractice(event) {
    const cardId = event.currentTarget.dataset.id || "";
    const title = event.currentTarget.dataset.title || "这张训练卡";
    const selectedCard = this.data.cards.find((card) => card.id === cardId);
    if (selectedCard) {
      wx.setStorageSync("safehome:selectedTrainingCard", selectedCard);
    }
    wx.navigateTo({
      url: `/pages/task-detail/index?card_id=${encodeURIComponent(cardId)}&card_title=${encodeURIComponent(title)}&diary_id=${encodeURIComponent(this.data.diaryId)}`,
    });
  },

  retryLoadCards() {
    this.loadCards(this.data.tags, this.data.cardIds);
  },
});
