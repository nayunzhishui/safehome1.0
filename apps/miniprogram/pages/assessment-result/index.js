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

function buildScaleDimensions(result, profileSummary) {
  // 学生画像走 profileSummary，不在这里处理；其它多维量表（如 ERQ）从 scores_json.dimensions 读取。
  if (profileSummary || !result) return [];
  const scores = parseJsonSafe(result.scores_json, {});
  const dimensions = Array.isArray(scores.dimensions) ? scores.dimensions : [];
  return dimensions
    .filter((item) => item && (item.label || item.key))
    .map((item) => {
      const isMean = item.score_method === "mean";
      const hasCount = item.item_count !== undefined && item.item_count !== null;
      const valueText = isMean ? `平均 ${item.score} 分` : `合计 ${item.score} 分`;
      const countText = hasCount ? `${item.item_count} 题${isMean ? "均值" : "合计"} ${item.score} 分` : valueText;
      return {
        key: item.key || item.label,
        label: item.label || item.key,
        score: item.score,
        itemCount: item.item_count,
        summary: `${countText}（仅本维度内观察，不与其它维度相加比较）`,
      };
    });
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
    content: worksheet && worksheet.result_disclaimer
      ? worksheet.result_disclaimer
      : "本结果用于自我观察和后续练习参考，不替代心理咨询、医学诊断、危机干预或法律判断。",
    reviewNote,
  };
}

function buildRiskSummary(result) {
  if (!result) return null;
  const scores = parseJsonSafe(result.scores_json, {});
  const risk = scores.risk || null;
  if (!risk || risk.risk_level === "low") return null;
  const riskTextMap = {
    medium: "建议人工关注",
    high: "优先现实支持",
  };
  return {
    riskLevel: risk.risk_level,
    title: riskTextMap[risk.risk_level] || "需要关注",
    text:
      risk.risk_level === "high"
        ? "本次填写中出现需要优先关注的安全线索，系统不生成普通训练建议。请优先联系现实中的可信成年人、学校老师、专业机构或当地紧急服务。"
        : "本次填写中出现建议人工关注的线索。结果仅用于分流和复核，不构成风险评估结论。",
  };
}

function normalizePlotPosition(value, min, max, invert = false) {
  if (min === max) return 50;
  const ratio = (value - min) / (max - min);
  const percent = 10 + ratio * 80;
  return invert ? 100 - percent : percent;
}

function compactFeatureLabel(label) {
  return String(label || "")
    .replace(/^\d+[.、，,]?\s*/, "")
    .slice(0, 8);
}

function buildRadarFeatures(payload) {
  const features = Array.isArray(payload.feature_profile) ? payload.feature_profile : [];
  return features
    .filter((item) => item && typeof item.z_score === "number")
    .sort((a, b) => Math.abs(b.z_score) - Math.abs(a.z_score))
    .slice(0, 6)
    .map((item) => {
      const value = Math.max(0.08, Math.min(1, (Number(item.z_score) + 2) / 4));
      return {
        id: item.feature_id,
        label: compactFeatureLabel(item.label || item.feature_id),
        zScore: Number(item.z_score),
        value,
      };
    });
}

function buildProfilePositionSummary(payload) {
  if (!payload || payload.available === false || !payload.position) {
    return null;
  }
  const position = payload.position;
  const interpretation = payload.interpretation || {};
  const canUseInterpretation = interpretation.can_use_interpretation !== false && position.can_use_interpretation !== false;
  const clusters = Array.isArray(payload.clusters) ? payload.clusters : [];
  const radarFeatures = buildRadarFeatures(payload);
  const coordinates = clusters
    .map((cluster) => cluster.pca_centroid || {})
    .concat([{ pc1: position.pc1, pc2: position.pc2 }])
    .filter((item) => typeof item.pc1 === "number" && typeof item.pc2 === "number");
  if (!coordinates.length) {
    return {
      modelId: payload.model_id || "",
      researchDir: payload.research_dir || "",
      nCasesText: payload.n_cases ? `${payload.n_cases} 份既往样本` : "",
      profileName: position.display_name || position.profile_name || "阶段性画像位置",
      confidenceText: position.confidence !== undefined && position.confidence !== null ? `${Math.round(Number(position.confidence) * 100)}%` : "仅作参考",
      canUseInterpretation,
      reliabilityText: canUseInterpretation ? "" : interpretation.message || "本次结果只作为位置参考，不做明确画像解释。",
      explanation: payload.explanation || "",
      boundaryNotice: payload.boundary_notice || "",
      featureText:
        payload.feature_summary && payload.feature_summary.total_features
          ? `${payload.feature_summary.answered_features}/${payload.feature_summary.total_features} 个题项用于定位`
          : "",
      clusterPoints: [],
      userPoint: null,
      radarFeatures,
      strengthNote: payload.strength_note || "",
      smallStep: payload.small_step || "",
    };
  }
  const xs = coordinates.map((item) => item.pc1);
  const ys = coordinates.map((item) => item.pc2);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const clusterPoints = clusters
    .filter((cluster) => cluster.pca_centroid && typeof cluster.pca_centroid.pc1 === "number" && typeof cluster.pca_centroid.pc2 === "number")
    .map((cluster) => {
      const left = normalizePlotPosition(cluster.pca_centroid.pc1, minX, maxX);
      const top = normalizePlotPosition(cluster.pca_centroid.pc2, minY, maxY, true);
      return {
        ...cluster,
        label: cluster.display_name || `画像${Number(cluster.cluster_id) + 1}`,
        xPercent: left,
        yPercent: top,
        style: `left:${left}%;top:${top}%;`,
      };
    });
  const userLeft = normalizePlotPosition(position.pc1, minX, maxX);
  const userTop = normalizePlotPosition(position.pc2, minY, maxY, true);
  return {
    modelId: payload.model_id || "",
    researchDir: payload.research_dir || "",
    nCasesText: payload.n_cases ? `${payload.n_cases} 份既往样本` : "",
    profileName: position.display_name || position.profile_name || "阶段性画像位置",
    confidenceText: position.confidence !== undefined && position.confidence !== null ? `${Math.round(Number(position.confidence) * 100)}%` : "仅作参考",
    canUseInterpretation,
    reliabilityText: canUseInterpretation ? "" : interpretation.message || "本次结果只作为位置参考，不做明确画像解释。",
    explanation: payload.explanation || "",
    boundaryNotice: payload.boundary_notice || "",
    featureText:
      payload.feature_summary && payload.feature_summary.total_features
        ? `${payload.feature_summary.answered_features}/${payload.feature_summary.total_features} 个题项用于定位`
        : "",
    clusterPoints,
    userPoint: {
      xPercent: userLeft,
      yPercent: userTop,
      style: `left:${userLeft}%;top:${userTop}%;`,
    },
    radarFeatures,
    strengthNote: payload.strength_note || "",
    smallStep: payload.small_step || "",
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
    scaleDimensions: [],
    riskSummary: null,
    profilePosition: null,
  },

  onLoad(options) {
    this.setData({
      resultId: decodeURIComponent(options.id || ""),
      worksheetId: decodeURIComponent(options.worksheet_id || ""),
    });
    this.loadResult();
  },

  onReady() {
    this.drawProfilePositionCharts();
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
      let profilePosition = null;
      if (result && !profileSummary) {
        const positionPayload = await api.getAssessmentProfilePosition(result.id).catch(() => null);
        profilePosition = buildProfilePositionSummary(positionPayload);
      }
      const scaleDimensions = buildScaleDimensions(result, profileSummary);
      const sourceNotice = buildSourceNotice(worksheet, profileSummary);
      const riskSummary = buildRiskSummary(result);
      const trainingRecommendation = buildTrainingRecommendation(worksheet, profileSummary, cards);
      saveLatestTrainingRecommendation(trainingRecommendation);
      this.setData(
        {
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
          scaleDimensions,
          sourceNotice,
          trainingRecommendation,
          riskSummary,
          profilePosition,
        },
        () => this.drawProfilePositionCharts(),
      );
    } catch (error) {
      this.setData({
        loading: false,
        errorMessage: error.message || "结果暂时没能读取，请检查网络后再试一次。",
      });
    }
  },

  drawProfilePositionCharts() {
    const profilePosition = this.data.profilePosition;
    if (!profilePosition) return;
    this.drawPositionCanvas(profilePosition);
    this.drawRadarCanvas(profilePosition);
  },

  withCanvasSize(selector, fallback, draw) {
    wx.createSelectorQuery()
      .in(this)
      .select(selector)
      .boundingClientRect((rect) => {
        draw({
          width: rect && rect.width ? rect.width : fallback.width,
          height: rect && rect.height ? rect.height : fallback.height,
        });
      })
      .exec();
  },

  drawPositionCanvas(profilePosition) {
    if (!profilePosition.userPoint) return;
    this.withCanvasSize(".position-canvas", { width: 320, height: 180 }, ({ width, height }) => {
      const ctx = wx.createCanvasContext("profilePlotCanvas", this);
      ctx.clearRect(0, 0, width, height);
      ctx.setFillStyle("#f8fbf5");
      ctx.fillRect(0, 0, width, height);
      ctx.setStrokeStyle("#dfe5dc");
      ctx.setLineWidth(1);
      ctx.beginPath();
      ctx.moveTo(24, height / 2);
      ctx.lineTo(width - 24, height / 2);
      ctx.moveTo(width / 2, 20);
      ctx.lineTo(width / 2, height - 20);
      ctx.stroke();

      (profilePosition.clusterPoints || []).forEach((point) => {
        const x = (Number(point.xPercent) / 100) * width;
        const y = (Number(point.yPercent) / 100) * height;
        ctx.setFillStyle("#e8f0ea");
        ctx.beginPath();
        ctx.arc(x, y, 8, 0, Math.PI * 2);
        ctx.fill();
        ctx.setFillStyle("#5d725f");
        ctx.setFontSize(10);
        ctx.fillText(point.label || "画像", x + 10, y + 4);
      });

      const ux = (Number(profilePosition.userPoint.xPercent) / 100) * width;
      const uy = (Number(profilePosition.userPoint.yPercent) / 100) * height;
      ctx.setFillStyle("#4f7c6b");
      ctx.beginPath();
      ctx.arc(ux, uy, 10, 0, Math.PI * 2);
      ctx.fill();
      ctx.setFillStyle("#202622");
      ctx.setFontSize(11);
      ctx.fillText("当前位置", Math.min(ux + 12, width - 62), Math.max(uy - 12, 18));
      ctx.draw();
    });
  },

  drawRadarCanvas(profilePosition) {
    const features = profilePosition.radarFeatures || [];
    if (features.length < 3) return;
    this.withCanvasSize(".radar-canvas", { width: 320, height: 220 }, ({ width, height }) => {
      const ctx = wx.createCanvasContext("profileRadarCanvas", this);
      const centerX = width / 2;
      const centerY = height / 2 + 6;
      const radius = Math.min(width, height) * 0.34;
      ctx.clearRect(0, 0, width, height);
      ctx.setFillStyle("#ffffff");
      ctx.fillRect(0, 0, width, height);

      [0.33, 0.66, 1].forEach((ratio) => {
        ctx.setStrokeStyle("#dfe5dc");
        ctx.beginPath();
        features.forEach((_item, index) => {
          const angle = (Math.PI * 2 * index) / features.length - Math.PI / 2;
          const x = centerX + Math.cos(angle) * radius * ratio;
          const y = centerY + Math.sin(angle) * radius * ratio;
          if (index === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        });
        ctx.closePath();
        ctx.stroke();
      });

      ctx.setStrokeStyle("#4f7c6b");
      ctx.setFillStyle("rgba(79, 124, 107, 0.18)");
      ctx.beginPath();
      features.forEach((item, index) => {
        const angle = (Math.PI * 2 * index) / features.length - Math.PI / 2;
        const x = centerX + Math.cos(angle) * radius * item.value;
        const y = centerY + Math.sin(angle) * radius * item.value;
        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      ctx.setFillStyle("#596a5b");
      ctx.setFontSize(10);
      features.forEach((item, index) => {
        const angle = (Math.PI * 2 * index) / features.length - Math.PI / 2;
        const x = centerX + Math.cos(angle) * (radius + 18);
        const y = centerY + Math.sin(angle) * (radius + 18);
        ctx.fillText(item.label, Math.max(4, Math.min(x - 18, width - 46)), Math.max(12, Math.min(y + 4, height - 8)));
      });
      ctx.draw();
    });
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
