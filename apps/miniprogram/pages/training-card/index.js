const { createSafeHomeApi } = require("../../services/api");
const { joinRules, firstSentence } = require("../../utils/card-text");

const api = createSafeHomeApi();
const LATEST_TRAINING_RECOMMENDATION_KEY = "safehome:latestTrainingRecommendation";

const INTERNAL_TOKEN_RE = /(^|_)(SCS|RSCA|HPLP|PRFQ|RFQ|PSSS|student|self|scs|rsca|hplp|prfq|rfq|psss)(_|$)|^[a-z]+_[a-z0-9_]+$/;

function isUserFacingTag(tag) {
  if (!tag || typeof tag !== "string") {
    return false;
  }
  if (INTERNAL_TOKEN_RE.test(tag)) {
    return false;
  }
  return /[\u4e00-\u9fa5]/.test(tag);
}

function formatRecommendationSource(tags, cardIds, topic) {
  if (topic) {
    return `训练库 · ${topic}：按自己的节奏挑一张，不必全部做完。`;
  }
  if (cardIds && cardIds.length) {
    return "来自本次测评结果，先推荐一张最容易完成的小练习。";
  }
  const visibleTags = (tags || []).filter(isUserFacingTag).slice(0, 3);
  if (visibleTags.length) {
    return `来自这次记录中的${visibleTags.join("、")}线索。`;
  }
  return "来自这次记录或测评结果中的可练习线索。";
}

// 节奏一行（Figma 652:1651）：“每次约 5 分钟，每周 3 次，……”；数字与汉字之间留空格。
function formatDose(frequency, minutes) {
  const parts = [];
  if (minutes) parts.push(`每次约 ${minutes} 分钟`);
  if (frequency) parts.push(String(frequency).replace(/([一-龥])(\d)/g, "$1 $2").replace(/(\d)([一-龥])/g, "$1 $2"));
  return parts.length ? parts.join("，") : "按个人节奏练习";
}

// 第一张是唯一的优先卡，其余列在“也可以改练”；页面只保留一个实心按钮。
function splitCards(cards) {
  return {
    cards,
    primaryCard: cards[0] || null,
    alternativeCards: cards.slice(1),
  };
}

// 从测一测结果进入时，用保存下来的推荐理由第一句说明依据（Figma 652:1628）；对不上本次卡片时不借用。
function storedAssessmentReason(cardIds) {
  let stored = null;
  try {
    stored = wx.getStorageSync(LATEST_TRAINING_RECOMMENDATION_KEY);
  } catch (error) {
    stored = null;
  }
  if (!stored || !stored.reason || !Array.isArray(stored.cardIds)) return "";
  if (!cardIds.some((cardId) => stored.cardIds.includes(cardId))) return "";
  const lead = String(stored.reason).split("。")[0].trim();
  return lead ? `测一测结果：${lead}。` : "";
}

Page({
  data: {
    loading: true,
    errorMessage: "",
    errorDetail: "",
    diaryId: "",
    tags: [],
    tagsText: "",
    librarySource: false,
    cardIds: [],
    cards: [],
    primaryCard: null,
    alternativeCards: [],
    practiceMessage: "",
    expandedCardId: "",
    feedbackEvaluationSaving: false,
  },

  onLoad(options) {
    const tagsText = decodeURIComponent(options.tags || "");
    const tags = tagsText ? tagsText.split(",").filter(Boolean) : [];
    const cardIdsText = decodeURIComponent(options.card_ids || "");
    const cardIds = cardIdsText ? cardIdsText.split(",").filter(Boolean) : [];
    // 训练库类别打开时由用户自己挑选，不当作测评推荐记录来源。
    const librarySource = options.source === "library" && cardIds.length > 0;
    const topic = librarySource ? decodeURIComponent(options.topic || "") || "全部练习" : "";
    const reasonText = !librarySource && cardIds.length ? storedAssessmentReason(cardIds) : "";
    this.setData({
      tags,
      tagsText: reasonText || formatRecommendationSource(tags, cardIds, topic),
      librarySource,
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
      const cards = selectedCards.map((card, index) => this.formatCard(card, index, this.data.librarySource ? "library" : cardIds.length ? "assessment_rule" : "tag_match"));
      // 适用与安全说明默认展开（Figma 652:1642），停止规则不用再点一次才看到。
      this.setData({
        ...splitCards(cards),
        expandedCardId: cards[0] ? cards[0].id : "",
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

  formatCard(card, index, recommendationSource) {
    const dose = card.minimum_dose || {};
    const firstStep = (card.steps || [])[0] || "完成一个最容易开始的小动作。";
    const durationShort = card.duration_minutes ? `约 ${card.duration_minutes} 分钟` : "1 次小练习";
    const scenarioText = card.suitable_scene || (card.suitable_for || [])[0] || "适合这次记录中的互动线索";
    return {
      ...card,
      isPrimary: index === 0,
      typeLabel: this.getTypeLabel(card.type),
      tagsText: (card.tags || []).filter(isUserFacingTag).slice(0, 3).join("、"),
      durationText: card.duration_minutes ? `${card.duration_minutes} 分钟` : "1 次小练习",
      scenarioText,
      metaText: `${durationShort} · ${scenarioText}`,
      altMetaText: `${recommendationSource === "library" ? "可选" : "备选"} · ${durationShort} · 改练这张`,
      altScene: firstSentence(card.purpose),
      todayGoal: firstStep,
      examplePhrase: card.example_phrase || card.example || "",
      beforePrompt: card.before_note_prompt || card.pre_practice_prompt || "",
      afterPrompt: card.after_note_prompt || card.post_practice_prompt || "",
      boundaryNotice: card.boundary_notice || "这张卡只是陪伴练习建议，不替代专业咨询或紧急帮助。",
      doseText: formatDose(dose.suggested_frequency, card.duration_minutes),
      completionText: card.completion_criteria || "完成一个核心步骤，并记录一句练习后的观察。",
      stopText: joinRules(card.stop_rules || card.not_suitable_for || []),
      recommendationSource,
      sourceRecommendationId: `${recommendationSource}:${card.id}`,
      stepsList: (card.steps || []).map((step, stepIndex) => ({
        text: step,
        numberText: `${stepIndex + 1}`,
      })),
      reflectionPrompt: (card.reflection_questions || [])[0] || "练习后可以简单记一句：这次我先做了什么，情绪有没有一点变化？",
      feedbackEvaluation: "",
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
    const detail = event.detail || {};
    const cardId = detail.id || event.currentTarget.dataset.id || "";
    const title = detail.title || event.currentTarget.dataset.title || "这张训练卡";
    const selectedCard = this.data.cards.find((card) => card.id === cardId);
    if (selectedCard) {
      wx.setStorageSync("safehome:selectedTrainingCard", selectedCard);
    }
    wx.navigateTo({
      url: `/pages/task-detail/index?card_id=${encodeURIComponent(cardId)}&card_title=${encodeURIComponent(title)}&diary_id=${encodeURIComponent(this.data.diaryId)}`,
    });
  },

  toggleCardDetails(event) {
    const cardId = event.currentTarget.dataset.id || "";
    this.setData({ expandedCardId: this.data.expandedCardId === cardId ? "" : cardId });
  },

  retryLoadCards() {
    this.loadCards(this.data.tags, this.data.cardIds);
  },

  goDiary() {
    wx.navigateTo({ url: "/pages/diary-form/index" });
  },

  async submitTrainingFeedback(event) {
    const cardId = event.currentTarget.dataset.id || "";
    const evaluation = event.detail.evaluation;
    const card = this.data.cards.find((item) => item.id === cardId);
    if (!card || this.data.feedbackEvaluationSaving) return;
    this.setData({ feedbackEvaluationSaving: true });
    try {
      await api.createFeedbackLedgerEntry({
        source_type: "training_recommendation",
        source_id: cardId,
        content_version: card.version || card.sourceRecommendationId || cardId,
        evaluation,
        idempotency_key: `training:${cardId}:${Date.now()}`,
      });
      let cards = this.data.cards.map((item) => ({
        ...item,
        feedbackEvaluation: item.id === cardId ? evaluation : item.feedbackEvaluation,
      }));
      let expandedCardId = this.data.expandedCardId;
      if (["does_not_match", "uncomfortable"].includes(evaluation) && cards.length > 1 && cards[0].id === cardId) {
        cards = [...cards.slice(1), cards[0]].map((item, index) => ({ ...item, isPrimary: index === 0 }));
        if (expandedCardId === cardId) expandedCardId = cards[0].id;
      }
      this.setData({ ...splitCards(cards), expandedCardId });
      wx.showToast({
        title: evaluation === "uncomfortable" ? "已停止优先推荐并等待人工复核" : "已记录你的核对",
        icon: "none",
      });
    } catch (error) {
      wx.showToast({ title: error.message || "暂时没能保存", icon: "none" });
    } finally {
      this.setData({ feedbackEvaluationSaving: false });
    }
  },
});
