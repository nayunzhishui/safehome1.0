const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();
const LATEST_TRAINING_RECOMMENDATION_KEY = "safehome:latestTrainingRecommendation";
const THREE_DAY_LIGHT_PLAN_KEY = "safehome:threeDayLightPlan";

function parseJsonSafe(value, fallback) {
  if (!value) return fallback;
  if (typeof value === "object") return value;
  try {
    return JSON.parse(value);
  } catch (error) {
    return fallback;
  }
}

function buildProfileSummary(result) {
  if (!result || result.category !== "学生画像") return null;
  const scores = parseJsonSafe(result.scores_json, {});
  const riskLevel = scores.risk_level || "low";
  const riskTextMap = {
    low: "普通关注",
    medium: "建议人工关注",
    high: "优先现实支持",
  };
  const recommendedCardIds = scores.risk_level === "high" || scores.allow_auto_feedback === false ? [] : scores.recommended_card_ids || [];
  return {
    profileName: scores.profile_name || "阶段性支持画像",
    profileCode: scores.profile_code || "",
    confidenceText: scores.confidence !== undefined && scores.confidence !== null ? `${Math.round(Number(scores.confidence) * 100)}%` : "暂未计算",
    riskLevel,
    riskLevelText: riskTextMap[riskLevel] || riskLevel,
    requiresReview: !!scores.requires_review,
    allowAutoFeedback: scores.allow_auto_feedback !== false,
    canOpenRecommendedCards: scores.risk_level !== "high" && scores.allow_auto_feedback !== false && recommendedCardIds.length > 0,
    dimensions: scores.dimensions || [],
    supportiveExplanation: scores.supportive_explanation || "",
    strengthNote: scores.strength_note || "",
    smallStep: scores.small_step || "",
    boundaryNotice: scores.boundary_notice || "",
    recommendedCardIds,
    recommendedCardsText:
      recommendedCardIds.length ? recommendedCardIds.join("、") : "暂无普通训练卡推荐",
  };
}

function buildSourceNotice(worksheet, profileSummary) {
  if (profileSummary) {
    return {
      title: "项目版支持性画像",
      statusText: "试点前复核",
      content: "本结果来自项目版学生支持性画像规则，用于理解本次填写中的阶段性线索。它不是临床诊断，也不是固定标签；如页面提示需要人工关注，应优先联系现实中的可信成年人、学校老师或专业支持。",
      reviewNote: worksheet && worksheet.review_note ? worksheet.review_note : "",
    };
  }

  const sourceType = worksheet && worksheet.source_type ? worksheet.source_type : "";
  const reviewStatus = worksheet && worksheet.review_status ? worksheet.review_status : "";
  const enabledForUser = worksheet ? worksheet.enabled_for_user !== false : true;
  const reviewNote = worksheet && worksheet.review_note ? worksheet.review_note : "";

  if (sourceType === "demo" || reviewStatus === "demo_only") {
    return {
      title: "示例参考",
      statusText: "示例未开放",
      content: "本结果来自示例参考内容，只适合查看格式和理解记录方式，不作为正式测评结果，也不用于训练推荐或结论判断。",
      reviewNote,
    };
  }

  if (sourceType === "simplified_worksheet" || reviewStatus === "draft_only") {
    return {
      title: "电子版简化工作表",
      statusText: enabledForUser ? "可填写" : "草稿待审核",
      content: "本结果来自电子版简化工作表，仅供自我观察和讨论准备。完整题项、来源、计分和解释在人工核验前，不应被理解为正式量表报告。",
      reviewNote,
    };
  }

  if (!enabledForUser || ["draft", "pending_review", "metadata_only", "needs_ethics_review"].includes(reviewStatus)) {
    return {
      title: "真实量表草稿",
      statusText: "待人工复核",
      content: "本结果来自仍在整理或复核中的量表资料，只能作为草稿记录。正式开放前需要继续核对题项来源、计分规则、解释边界和伦理风险。",
      reviewNote,
    };
  }

  return {
    title: "支持性测评结果",
    statusText: "可填写",
    content: "本结果用于自我观察和后续练习参考，不替代心理咨询、医学诊断、危机干预或法律判断。",
    reviewNote,
  };
}

function buildTrainingRecommendation(worksheet, profileSummary, cardsPayload) {
  if (profileSummary && !profileSummary.allowAutoFeedback) {
    return null;
  }

  const rules = worksheet && Array.isArray(worksheet.training_recommendation_rules) ? worksheet.training_recommendation_rules : [];
  if (!rules.length) {
    return null;
  }

  const matchedRule = rules.find((rule) => {
    const condition = rule.trigger_condition || {};
    if (condition.profile_code && profileSummary && profileSummary.profileCode) {
      return condition.profile_code === profileSummary.profileCode;
    }
    return true;
  });
  if (!matchedRule) {
    return null;
  }

  const cards = cardsPayload && Array.isArray(cardsPayload.items) ? cardsPayload.items : [];
  const cardMap = cards.reduce((acc, card) => {
    acc[card.id] = card;
    return acc;
  }, {});
  const roleMap = (matchedRule.card_roles || []).reduce((acc, item) => {
    if (item && item.card_id) {
      acc[item.card_id] = item.role || "";
    }
    return acc;
  }, {});
  const recommendedCards = (matchedRule.recommended_card_ids || []).slice(0, 3).map((cardId) => ({
    id: cardId,
    title: cardMap[cardId] ? cardMap[cardId].title : cardId,
    purpose: cardMap[cardId] ? cardMap[cardId].purpose : "",
    role: roleMap[cardId] || "推荐练习",
  }));

  if (!recommendedCards.length) {
    return null;
  }

  return {
    reason: matchedRule.reason || "",
    todaySuggestion: matchedRule.today_suggestion || "",
    longTermSuggestion: matchedRule.long_term_suggestion || "",
    boundaryNotice: matchedRule.boundary_notice || "",
    notSuitableWhen: matchedRule.not_suitable_when || "",
    recommendedCards,
    cardIds: recommendedCards.map((card) => card.id),
  };
}

function saveLatestTrainingRecommendation(trainingRecommendation) {
  if (!trainingRecommendation || !trainingRecommendation.cardIds || !trainingRecommendation.cardIds.length) {
    return;
  }

  wx.setStorageSync(LATEST_TRAINING_RECOMMENDATION_KEY, {
    sourceType: "assessment",
    sourceTitle: "测一测结果推荐",
    reason: trainingRecommendation.reason || "",
    todaySuggestion: trainingRecommendation.todaySuggestion || "",
    longTermSuggestion: trainingRecommendation.longTermSuggestion || "",
    boundaryNotice: trainingRecommendation.boundaryNotice || "",
    cardIds: trainingRecommendation.cardIds,
    cards: trainingRecommendation.recommendedCards || [],
    updatedAt: new Date().toISOString(),
  });
  saveThreeDayLightPlan(trainingRecommendation);
}

function saveThreeDayLightPlan(trainingRecommendation) {
  if (
    !trainingRecommendation.longTermSuggestion ||
    !Array.isArray(trainingRecommendation.recommendedCards) ||
    !trainingRecommendation.recommendedCards.length
  ) {
    return;
  }

  const cards = trainingRecommendation.recommendedCards;
  const days = [0, 1, 2].map((index) => {
    const card = cards[index] || cards[cards.length - 1];
    return {
      day: index + 1,
      title: `第 ${index + 1} 天`,
      cardId: card.id,
      cardTitle: card.title,
      role: card.role || ["今日练习", "备用练习", "长期练习"][index],
      purpose: card.purpose || "",
      suggestion:
        index === 0
          ? trainingRecommendation.todaySuggestion || "先完成一张最轻量的练习卡。"
          : index === 1
            ? "延续昨天的观察，换一张备用练习卡试一次。"
            : "回到长期方向，只保留一个最容易坚持的小动作。",
    };
  });

  wx.setStorageSync(THREE_DAY_LIGHT_PLAN_KEY, {
    sourceType: "assessment",
    sourceTitle: "测一测 3 天轻量计划",
    longTermSuggestion: trainingRecommendation.longTermSuggestion,
    boundaryNotice: trainingRecommendation.boundaryNotice || "3 天轻量计划只作为支持性练习建议，不构成诊断或治疗方案。",
    days,
    updatedAt: new Date().toISOString(),
  });
}

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
    profileSummary: null,
    sourceNotice: null,
    trainingRecommendation: null,
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
      const [results, worksheet, cards] = await Promise.all([
        api.listAssessmentResults({ limit: 20 }),
        this.data.worksheetId ? api.getAssessment(this.data.worksheetId) : Promise.resolve(null),
        api.listCards().catch(() => ({ items: [] })),
      ]);
      const result = (results.items || []).find((item) => item.id === this.data.resultId) || (results.items || [])[0];
      const profileSummary = buildProfileSummary(result);
      const sourceNotice = buildSourceNotice(worksheet, profileSummary);
      const trainingRecommendation = buildTrainingRecommendation(worksheet, profileSummary, cards);
      saveLatestTrainingRecommendation(trainingRecommendation);
      this.setData({
        result,
        worksheet,
        loading: false,
        totalScoreText: result && result.total_score !== null && result.total_score !== undefined ? `${result.total_score}` : "本工作表不自动计分",
        recommendedCardsText: profileSummary
          ? profileSummary.recommendedCardsText
          : worksheet && worksheet.recommended_card_ids && worksheet.recommended_card_ids.length
            ? worksheet.recommended_card_ids.join("、")
            : "暂无固定推荐",
        profileSummary,
        sourceNotice,
        trainingRecommendation,
      });
    } catch (error) {
      this.setData({
        loading: false,
        errorMessage: error.message || "结果读取失败，请确认 backend 是否已启动。",
      });
    }
  },

  openRecommendedCards() {
    const profileSummary = this.data.profileSummary;
    if (profileSummary && !profileSummary.canOpenRecommendedCards) {
      wx.showToast({
        title: "当前没有普通训练卡推荐，请先查看现实支持提示。",
        icon: "none",
      });
      return;
    }

    const trainingRecommendation = this.data.trainingRecommendation;
    if (trainingRecommendation && trainingRecommendation.cardIds && trainingRecommendation.cardIds.length) {
      wx.navigateTo({
        url: `/pages/training-card/index?card_ids=${encodeURIComponent(trainingRecommendation.cardIds.join(","))}`,
      });
      return;
    }
    if (profileSummary && profileSummary.recommendedCardIds && profileSummary.recommendedCardIds.length) {
      wx.navigateTo({
        url: `/pages/training-card/index?card_ids=${encodeURIComponent(profileSummary.recommendedCardIds.join(","))}`,
      });
      return;
    }
    wx.switchTab({ url: "/pages/training/index" });
  },

  backToAssessment() {
    wx.navigateBack({ delta: 2 });
  },
});
