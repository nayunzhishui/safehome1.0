const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();
const LATEST_TRAINING_RECOMMENDATION_KEY = "safehome:latestTrainingRecommendation";

Page({
  data: {
    diaryId: "",
    loading: true,
    errorMessage: "",
    feedback: null,
    isHighRisk: false,
    canShowTraining: true,
    missingDiaryId: false,
    nextAction: null,
    labelsText: "",
    patternCards: [],
    emotionOverview: null,
    trainingRecommendation: null,
    recommendedTrainings: [],
    riskSupportText: "",
    feedbackEvaluation: "",
    feedbackEvaluationSaving: false,
  },

  onLoad(options) {
    const diaryId = decodeURIComponent(options.diary_id || "");
    this.setData({ diaryId });
    this.loadFeedback(diaryId);
  },

  async loadFeedback(diaryId) {
    if (!diaryId) {
      this.setData({
        loading: false,
        missingDiaryId: true,
        errorMessage: "缺少记录 ID。支持性反馈需要先提交一条情绪记录。",
      });
      return;
    }

    this.setData({ loading: true, errorMessage: "", missingDiaryId: false });

    try {
      const feedback = await api.generateFeedback({ diary_id: diaryId });
      const cardResponse = await api.listCards().catch(() => ({ items: [] }));
      const cards = Array.isArray(cardResponse.items) ? cardResponse.items : [];
      const isHighRisk = feedback.risk_level === "high" || (feedback.risk && feedback.risk.allow_recommended_training_cards === false);
      const canShowTraining = !isHighRisk;
      const trainingRecommendation = this.buildTrainingRecommendation(feedback, canShowTraining);
      const recommendedTrainings = this.buildRecommendedTrainings(trainingRecommendation, cards);
      this.saveLatestTrainingRecommendation(trainingRecommendation, recommendedTrainings);
      this.setData({
        feedback,
        isHighRisk,
        canShowTraining,
        labelsText: (feedback.labels || feedback.tags || []).join("、"),
        patternCards: this.buildPatternCards(feedback),
        emotionOverview: this.buildEmotionOverview(feedback, isHighRisk),
        nextAction: this.buildNextAction(feedback, isHighRisk),
        trainingRecommendation,
        recommendedTrainings,
        riskSupportText:
          (feedback.risk && feedback.risk.safe_response) ||
          "如果这次记录涉及现实安全风险，请先联系现实中的可信成年人、学校老师、专业机构或当地紧急服务。本系统不能替代危机干预。",
        loading: false,
      });
    } catch (error) {
      this.setData({
        loading: false,
        errorMessage: error.message || "反馈暂时没能生成，请检查网络后再试一次。你的这次记录已经保存好了。",
      });
    }
  },

  buildPatternCards(feedback) {
    const labelsText = (feedback.labels || feedback.tags || []).join("、");

    return [
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

  buildNextAction(feedback, isHighRisk) {
    if (isHighRisk) {
      return {
        title: "先联系现实支持",
        text:
          (feedback.risk && feedback.risk.safe_response) ||
          "如果这次记录涉及现实安全风险，请优先联系现实中的可信成年人、学校老师、专业机构或当地紧急服务。",
        buttonText: "提交人工关注",
      };
    }

    const cardCount = (feedback.recommended_card_ids || []).length;
    return {
      title: "开始一个小练习",
      text: cardCount > 0 ? "系统已为这次记录匹配到可练习动作，建议先选 1 个完成。" : "可以先从暂停和一句短回应开始，不需要一次做很多。",
      buttonText: "开始一个小练习",
    };
  },

  buildEmotionOverview(feedback, isHighRisk) {
    const overview = feedback.emotion_overview || {};

    if (isHighRisk) {
      return {
        mainEmotion: "需要优先关注安全",
        intensity: "建议人工关注",
        trigger: feedback.trigger_summary || "本次记录包含需要优先现实支持的线索。",
      };
    }

    return {
      mainEmotion: overview.primary_emotion || "这次记录中的感受",
      intensity: overview.intensity_text || "未记录",
      trigger: feedback.trigger_summary || "这次记录发生在“" + (overview.scene || "具体互动") + "”场景。",
    };
  },

  buildTrainingRecommendation(feedback, canShowTraining) {
    if (!canShowTraining) {
      return null;
    }

    const rules = feedback.training_recommendation_rules || [];
    return rules.length > 0 ? rules[0] : null;
  },

  getCardRole(rule, cardId, index) {
    const roles = Array.isArray(rule.card_roles) ? rule.card_roles : [];
    const matchedRole = roles.find((item) => item.card_id === cardId);
    if (matchedRole && matchedRole.role) {
      return matchedRole.role;
    }
    return ["今日练习", "备用练习", "长期练习"][index] || "推荐练习";
  },

  buildRecommendedTrainings(rule, cards) {
    if (!rule) {
      return [];
    }

    const cardMap = {};
    cards.forEach((card) => {
      cardMap[card.id] = card;
    });

    return (rule.recommended_card_ids || []).slice(0, 3).map((cardId, index) => {
      const card = cardMap[cardId] || {};
      const role = this.getCardRole(rule, cardId, index);
      const minutes = card.duration_minutes ? `${card.duration_minutes} 分钟` : "3-10 分钟";
      return {
        cardId,
        title: card.title || cardId,
        subtitle: card.purpose || rule.today_suggestion || "今日轻量练习",
        stage: role,
        duration: minutes,
        scenario: "今天先选 1 张完成即可",
        reason: rule.reason || "与这次日记中的互动线索相关。",
        tag: role,
      };
    });
  },

  saveLatestTrainingRecommendation(rule, trainings) {
    if (!rule || !trainings || !trainings.length) {
      return;
    }

    wx.setStorageSync(LATEST_TRAINING_RECOMMENDATION_KEY, {
      sourceType: "diary",
      sourceTitle: "情绪日记今日建议",
      reason: rule.reason || "",
      todaySuggestion: rule.today_suggestion || "",
      longTermSuggestion: "",
      boundaryNotice: rule.boundary_notice || "",
      cardIds: trainings.map((item) => item.cardId).filter(Boolean),
      cards: trainings.map((item) => ({
        id: item.cardId,
        title: item.title,
        purpose: item.subtitle,
        role: item.stage,
      })),
      updatedAt: new Date().toISOString(),
    });
  },

  saveFeedback() {
    wx.showToast({
      title: "本次反馈已保留在当前记录中",
      icon: "none",
    });
  },

  async submitFeedbackEvaluation(event) {
    const evaluation = event.detail.evaluation;
    const feedback = this.data.feedback;
    if (!feedback || !feedback.id || this.data.feedbackEvaluationSaving) return;
    this.setData({ feedbackEvaluationSaving: true });
    try {
      await api.createFeedbackLedgerEntry({
        source_type: "instant_feedback",
        source_id: feedback.id,
        content_version: feedback.rules_version || feedback.id,
        evaluation,
        idempotency_key: `instant:${feedback.id}:${Date.now()}`,
      });
      this.setData({ feedbackEvaluation: evaluation });
      wx.showToast({ title: evaluation === "uncomfortable" ? "已记录并等待人工复核" : "已记录你的核对", icon: "none" });
    } catch (error) {
      wx.showToast({ title: error.message || "暂时没能保存", icon: "none" });
    } finally {
      this.setData({ feedbackEvaluationSaving: false });
    }
  },

  goToDiaryForm() {
    wx.navigateTo({ url: "/pages/diary-form/index" });
  },

  openTrainingCard() {
    if (!this.data.canShowTraining) {
      wx.showToast({
        title: "当前提示需要优先现实支持，不进入普通训练卡。",
        icon: "none",
      });
      return;
    }

    const tags = this.data.feedback && this.data.feedback.tags ? this.data.feedback.tags : [];
    const rule = this.data.trainingRecommendation || {};
    const cardIds = Array.isArray(rule.recommended_card_ids) ? rule.recommended_card_ids.join(",") : "";
    wx.navigateTo({
      url: `/pages/training-card/index?tags=${encodeURIComponent(tags.join(","))}&card_ids=${encodeURIComponent(cardIds)}&diary_id=${encodeURIComponent(this.data.diaryId)}`,
    });
  },

  openSupervision() {
    wx.navigateTo({
      url: `/pages/supervision/index?diary_id=${encodeURIComponent(this.data.diaryId)}`,
    });
  },
});
