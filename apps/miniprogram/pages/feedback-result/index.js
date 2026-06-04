const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

Page({
  data: {
    diaryId: "",
    loading: true,
    errorMessage: "",
    feedback: null,
    isHighRisk: false,
    canShowTraining: true,
    nextAction: null,
    labelsText: "",
    patternCards: [],
    emotionOverview: null,
    recommendedTrainings: [],
    riskSupportText: "",
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
      const isHighRisk = feedback.risk_level === "high" || (feedback.risk && feedback.risk.allow_recommended_training_cards === false);
      const canShowTraining = !isHighRisk;
      this.setData({
        feedback,
        isHighRisk,
        canShowTraining,
        labelsText: (feedback.labels || feedback.tags || []).join("、"),
        patternCards: this.buildPatternCards(feedback),
        emotionOverview: this.buildEmotionOverview(feedback, isHighRisk),
        nextAction: this.buildNextAction(feedback, isHighRisk),
        recommendedTrainings: this.buildRecommendedTrainings(feedback, canShowTraining),
        riskSupportText:
          (feedback.risk && feedback.risk.safe_response) ||
          "如果这次记录涉及现实安全风险，请先联系现实中的可信成年人、学校老师、专业机构或当地紧急服务。本系统不能替代危机干预。",
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
    const tags = feedback.tags || [];
    const labels = feedback.labels || [];
    const labelsText = labels.join("、");

    if (isHighRisk) {
      return {
        mainEmotion: "需要优先关注安全",
        intensity: "建议人工关注",
        trigger: feedback.trigger_summary || "本次记录包含需要优先现实支持的线索。",
      };
    }

    return {
      mainEmotion: tags.includes("high_emotion_intensity") ? "着急 / 生气 / 委屈" : "焦虑 / 着急 / 困惑",
      intensity: tags.includes("high_emotion_intensity") ? "中等偏高" : "中等",
      trigger: feedback.trigger_summary || labelsText || "一次具体亲子互动事件",
    };
  },

  buildRecommendedTrainings(feedback, canShowTraining) {
    if (!canShowTraining) {
      return [];
    }

    const tags = feedback.tags || [];
    const trainings = [
      {
        title: "暂停训练",
        subtitle: "先稳定身体反应，再进入沟通",
        stage: "推荐训练",
        duration: "3-5 分钟",
        scenario: "情绪升高、准备催促前",
        tag: "推荐",
      },
    ];

    if (tags.includes("judgmental_language") || tags.includes("parent_child_conflict")) {
      trainings.push({
        title: "非评判陪伴",
        subtitle: "先接住孩子的情绪，再讨论问题",
        stage: "推荐训练",
        duration: "5-10 分钟",
        scenario: "孩子委屈、生气或不愿说话时",
        tag: "推荐",
      });
    }

    trainings.push({
      title: "关系修复",
      subtitle: "冲突后重新连接",
      stage: "推荐训练",
      duration: "8-10 分钟",
      scenario: "刚发生争吵或冷处理后",
      tag: "进阶",
    });

    return trainings;
  },

  saveFeedback() {
    wx.showToast({
      title: "本次反馈已保留在当前记录中",
      icon: "none",
    });
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
