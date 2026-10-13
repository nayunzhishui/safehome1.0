const { captureAuthSession, isCurrentAuthSession } = require("../../utils/authGuard");
const { createSafeHomeApi } = require("../../services/api");
const { buildDimensionVisualization } = require("../../utils/assessment-dimension-visualization");
const { buildEmotionInsightsView } = require("../../utils/emotion-insights-view");

const api = createSafeHomeApi();
// 图表颜色与 UIproduct3 令牌一致（画布里不能用 CSS 变量）。
const CHART_COLORS = {
  ink: "#173C43",
  muted: "#536E73",
  primary: "#23666E",
  primaryFill: "rgba(35, 102, 110, 0.16)",
  hairline: "#E7E1D6",
  soft: "#E2F0ED",
};
const RADAR_LABEL_SIZE = 13;
const LATEST_TRAINING_RECOMMENDATION_KEY = "safehome:latestTrainingRecommendation";
const THREE_DAY_LIGHT_PLAN_KEY = "safehome:threeDayLightPlan";

// 画布标签宽度估算：中文与全角符号按一个字宽，其余按 0.56 个字宽（Noto Sans SC 近似），不依赖各端 measureText 差异。
function estimateTextWidth(text, fontSize) {
  return String(text || "").split("").reduce((sum, char) => sum + (char.charCodeAt(0) > 0x2e7f ? fontSize : fontSize * 0.56), 0);
}

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
      recommendedCardIds.length ? "已为你准备练习建议" : "暂无普通训练卡推荐",
  };
}

// 后端计分方式有 sum、mean、mean_terms、mapped_mean_terms、mean_dimensions、
// mean_of_products 和 product；只有 sum 是题目分直接相加。
function scoreMethodText(method) {
  const value = String(method || "sum");
  if (value === "sum") return "合计";
  if (value.indexOf("mean") !== -1) return "均值";
  return "得分";
}

function buildScaleDimensions(result, profileSummary) {
  // 学生画像走 profileSummary，不在这里处理；其它多维量表（如 ERQ）从 scores_json.dimensions 读取。
  if (profileSummary || !result) return [];
  const scores = parseJsonSafe(result.scores_json, {});
  const dimensions = Array.isArray(scores.dimensions) ? scores.dimensions : [];
  const guideItems = result.dimension_guides && Array.isArray(result.dimension_guides.items) ? result.dimension_guides.items : [];
  const guides = {};
  guideItems.forEach((guide) => { if (guide && guide.key) guides[guide.key] = guide; });
  return dimensions
    .filter((item) => item && (item.label || item.key))
    .map((item) => {
      const methodText = scoreMethodText(item.score_method);
      const hasCount = item.item_count !== undefined && item.item_count !== null;
      const valueText = methodText === "均值" ? `平均 ${item.score} 分` : `${methodText} ${item.score} 分`;
      const countText = hasCount ? `${item.item_count} 题${methodText} ${item.score} 分` : valueText;
      const guide = guides[item.key] || {};
      return {
        key: item.key || item.label,
        label: item.label || item.key,
        score: item.score,
        itemCount: item.item_count,
        scoreMethod: item.score_method || "sum",
        scoreRange: item.score_range || null,
        summary: `${countText}（仅本维度内观察，不与其它维度相加比较）`,
        // What the dimension looks at, and a short hint for where this answer falls.
        definition: guide.definition || "",
        band: guide.band || "",
        bandLabel: guide.band_label || "",
        hint: guide.hint || "",
        composite: Boolean(guide.composite),
      };
    });
}

function formatScoreNumber(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return value === undefined || value === null ? "" : String(value);
  return Number.isInteger(number) ? String(number) : String(Math.round(number * 10) / 10);
}

function decorateDimensionRow(item) {
  const methodText = scoreMethodText(item.scoreMethod);
  const countText = item.itemCount !== undefined && item.itemCount !== null ? `${item.itemCount} 题${methodText}` : methodText;
  return {
    ...item,
    scoreText: formatScoreNumber(item.score),
    maxText: item.hasComparableRange ? `/ ${formatScoreNumber(item.maxScore)}` : "",
    metaText: item.hasComparableRange
      ? `量尺 ${formatScoreNumber(item.minScore)}–${formatScoreNumber(item.maxScore)} · ${countText} · 竖线为中点`
      : "量尺范围暂未核定",
    positionShort: item.hasComparableRange ? `位置 ${item.positionPercent}%` : "保留原始得分",
    // 中间区没有单独标签时只显示统一句，用浅色字。
    plainHint: !item.bandLabel,
  };
}

function decorateVisualization(visualization) {
  if (!visualization) return visualization;
  return {
    ...visualization,
    dimensions: (visualization.dimensions || []).map(decorateDimensionRow),
    composites: (visualization.composites || []).map(decorateDimensionRow),
  };
}

// “10月10日 20:40 · 10 题”
function buildResultMeta(result, worksheet) {
  if (!result) return "";
  const matched = String(result.created_at || "").match(/^(\d{4})-(\d{2})-(\d{2})(?:[T\s](\d{2}):(\d{2}))?/);
  const parts = [];
  if (matched) parts.push(`${Number(matched[2])}月${Number(matched[3])}日${matched[4] ? ` ${matched[4]}:${matched[5]}` : ""}`);
  const answers = parseJsonSafe(result.answers_json, null);
  const questionCount = worksheet && Array.isArray(worksheet.questions) && worksheet.questions.length
    ? worksheet.questions.length
    : Array.isArray(result.answers) ? result.answers.length : Array.isArray(answers) ? answers.length : 0;
  if (questionCount) parts.push(`${questionCount} 题`);
  return parts.join(" · ");
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
  // Item-level triggers carry their own participant message; text-signal results keep the generic copy.
  const genericText =
    risk.risk_level === "high"
      ? "本次填写中出现需要优先关注的安全线索，系统不生成普通训练建议。请优先联系现实中的可信成年人、学校老师、专业机构或当地紧急服务。"
      : "本次填写中出现建议人工关注的线索。结果仅用于分流和复核，不构成风险评估结论。";
  return {
    riskLevel: risk.risk_level,
    title: riskTextMap[risk.risk_level] || "需要关注",
    text: risk.participant_message || genericText,
  };
}

function normalizePlotPosition(value, min, max, invert = false) {
  if (min === max) return 50;
  const ratio = (value - min) / (max - min);
  const percent = 10 + ratio * 80;
  return invert ? 100 - percent : percent;
}

function compactFeatureLabel(label) {
  const text = String(label || "").trim();
  // Some source labels carry the questionnaire's block number before the item number
  // ("15、1、…", "14、5. …"); the item's own number is the last one, and "1a" keeps its letter.
  const prefix = text.match(/^(?:\d+[a-z]?\s*[.、，,．]?\s*)+/);
  if (prefix) {
    const numbers = prefix[0].match(/\d+[a-z]?/g);
    return `题${numbers[numbers.length - 1]}`;
  }
  return text.slice(0, 10);
}

function matchingClarityText(position, interpretation) {
  const status = interpretation.status || position.interpretation_status;
  if (status === "outlier") return "样本范围外";
  if (status === "low_confidence") return "较低，暂不归纳";
  if (status === "pending_approval") return "待研究者审核";
  const posterior = Number(position.posterior ?? position.confidence);
  if (!Number.isFinite(posterior)) return "仅作参考";
  // Distance-margin models report how much nearer the closest group is (0.15 is the usable floor);
  // mixture models report a probability. The two need different bands.
  const marginBased = String(position.assignment_version || "").startsWith("euclidean");
  const [high, middle] = marginBased ? [0.4, 0.25] : [0.8, 0.6];
  if (posterior >= high) return "较高";
  if (posterior >= middle) return "中等";
  return "较低";
}

function buildRadarFeatures(payload) {
  const features = Array.isArray(payload.feature_profile) ? payload.feature_profile : [];
  return features
    .filter((item) => item && typeof item.z_score === "number")
    .map((item) => ({
      ...item,
      // Show every item in the direction of its wording: further out means agreeing more.
      wordingZ: item.reverse_scored ? -Number(item.z_score) : Number(item.z_score),
    }))
    .sort((a, b) => Math.abs(b.wordingZ) - Math.abs(a.wordingZ))
    .slice(0, 6)
    .map((item, index) => ({
      id: item.feature_id,
      label: compactFeatureLabel(item.label || item.feature_id),
      axisLabel: String(index + 1),
      zScore: item.wordingZ,
      value: Math.max(0.08, Math.min(1, (item.wordingZ + 2) / 4)),
    }));
}

function buildDimensionRadarFeatures(payload, position, clusters) {
  const selected = clusters.find((cluster) => Number(cluster.cluster_id) === Number(position.cluster_id));
  const dimensionRows = payload.radar_support && Array.isArray(payload.radar_support.dimensions)
    ? payload.radar_support.dimensions
    : [];
  if (!selected || !selected.dimension_z || dimensionRows.length < 3) return [];
  return dimensionRows
    .filter((dimension) => typeof selected.dimension_z[dimension.code] === "number")
    .sort((a, b) => Math.abs(selected.dimension_z[b.code]) - Math.abs(selected.dimension_z[a.code]))
    .slice(0, 6)
    .map((dimension, index) => {
      const zScore = Number(selected.dimension_z[dimension.code]);
      return {
        id: dimension.code,
        label: compactFeatureLabel(dimension.label || dimension.code),
        axisLabel: String(index + 1),
        zScore,
        value: Math.max(0.08, Math.min(1, (zScore + 2) / 4)),
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
  const dimensionRadarFeatures = buildDimensionRadarFeatures(payload, position, clusters);
  const radarFeatures = dimensionRadarFeatures.length >= 3 ? dimensionRadarFeatures : buildRadarFeatures(payload);
  // 图例先排满左列再排右列（Figma 679:3889「两列」）。
  const legendSplit = Math.ceil(radarFeatures.length / 2);
  const radarLegendColumns = [radarFeatures.slice(0, legendSplit), radarFeatures.slice(legendSplit)].filter((column) => column.length);
  const radarCaption = dimensionRadarFeatures.length >= 3
    ? "轮廓显示这一画像组在各维度上的特点，与既往样本平均水平比较。"
    : "轮廓显示你这次在差异最大的几道题上的作答，与既往样本平均水平比较；越靠外表示越认同该题的说法。";
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
      confidenceText: matchingClarityText(position, interpretation),
      canUseInterpretation,
      visualizationState: interpretation.status && interpretation.status !== "usable" ? interpretation.status : "data",
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
      radarLegendColumns,
      radarCaption,
      strengthNote: payload.strength_note || "",
      smallStep: payload.small_step || "",
      suggestedQuestions: payload.suggested_assessment_questions || [],
      projectTasks: payload.recommended_project_tasks || [],
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
    .map((cluster, index) => {
      const left = normalizePlotPosition(cluster.pca_centroid.pc1, minX, maxX);
      const top = normalizePlotPosition(cluster.pca_centroid.pc2, minY, maxY, true);
      return {
        ...cluster,
        label: cluster.display_name || `画像${Number(cluster.cluster_id) + 1}`,
        axisLabel: String(index + 1),
        xPercent: left,
        yPercent: top,
        style: `left:${left}%;top:${top}%;`,
      };
    });
  const hasUserPoint = typeof position.pc1 === "number" && typeof position.pc2 === "number";
  const userLeft = hasUserPoint ? normalizePlotPosition(position.pc1, minX, maxX) : null;
  const userTop = hasUserPoint ? normalizePlotPosition(position.pc2, minY, maxY, true) : null;
  return {
    modelId: payload.model_id || "",
    researchDir: payload.research_dir || "",
    nCasesText: payload.n_cases ? `${payload.n_cases} 份既往样本` : "",
    profileName: position.display_name || position.profile_name || "阶段性画像位置",
    confidenceText: matchingClarityText(position, interpretation),
    canUseInterpretation,
    visualizationState: interpretation.status && interpretation.status !== "usable" ? interpretation.status : "data",
    reliabilityText: canUseInterpretation ? "" : interpretation.message || "本次结果只作为位置参考，不做明确画像解释。",
    explanation: payload.explanation || "",
    boundaryNotice: payload.boundary_notice || "",
    featureText:
      payload.feature_summary && payload.feature_summary.total_features
        ? `${payload.feature_summary.answered_features}/${payload.feature_summary.total_features} 个题项用于定位`
        : "",
    clusterPoints,
    userPoint: hasUserPoint
      ? {
          xPercent: userLeft,
          yPercent: userTop,
          style: `left:${userLeft}%;top:${userTop}%;`,
        }
      : null,
    radarFeatures,
    radarLegendColumns,
    radarCaption,
    strengthNote: payload.strength_note || "",
    smallStep: payload.small_step || "",
    suggestedQuestions: payload.suggested_assessment_questions || [],
    projectTasks: payload.recommended_project_tasks || [],
  };
}

function matchedRulesFromResult(result) {
  if (!result) return [];
  // The server evaluates dimension conditions against this result and freezes the matched rules in the snapshot.
  const snapshot = result.content_snapshot || parseJsonSafe(result.content_snapshot_json, {});
  const recommendation = (snapshot && snapshot.recommendation) || {};
  return Array.isArray(recommendation.rules) ? recommendation.rules : [];
}

function buildTrainingRecommendation(worksheet, profileSummary, cardsPayload, result) {
  if (profileSummary && !profileSummary.allowAutoFeedback) {
    return null;
  }

  const matchedRules = matchedRulesFromResult(result);
  const worksheetRules = worksheet && Array.isArray(worksheet.training_recommendation_rules) ? worksheet.training_recommendation_rules : [];
  const rules = matchedRules.length ? matchedRules : worksheetRules.filter((rule) => !(rule.trigger_condition || {}).dimension);
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
  const recommendedCards = (matchedRule.recommended_card_ids || []).slice(0, 3).map((cardId, index) => ({
    id: cardId,
    title: cardMap[cardId] ? cardMap[cardId].title : `练习卡 ${index + 1}`,
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
  onShow() {
    this._hidden = false;
    if (this._readSession && !isCurrentAuthSession(this._readSession)) {
      this.setData({ result: null, worksheet: null, profileSummary: null, profilePosition: null, exploratoryAnalysis: null, scaleDimensions: [], scaleVisualization: null, trainingRecommendation: null, riskSummary: null, sourceNotice: null, totalScoreText: "", recommendedCardsText: "" });
      this.loadResult();
    } else if (this.data.loading && this._readSession) { this.loadResult(); }
  },
  onHide() { this._hidden = true; },
  onUnload() { this._consentDisposed = true; this._hidden = true; },
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
    scaleVisualization: null,
    riskSummary: null,
    profilePosition: null,
    exploratoryAnalysis: null,
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
    this.drawScaleDimensionChart();
  },

  async loadResult() {
    const session = captureAuthSession();
    this._readSession = session;
    const requestId = this._resultRequestId = (this._resultRequestId || 0) + 1;
    const isCurrent = () => !this._hidden && !this._consentDisposed && requestId === this._resultRequestId && isCurrentAuthSession(session);
    this.setData({ loading: true, errorMessage: "" });
    try {
      const [result, worksheet, cards, exploratoryPayload] = await Promise.all([
        api.getAssessmentResult(this.data.resultId),
        this.data.worksheetId ? api.getAssessment(this.data.worksheetId).catch(() => null) : Promise.resolve(null),
        api.listCards().catch(() => ({ items: [] })),
        api.getAssessmentExploratoryAnalysis(this.data.resultId).catch(() => null),
      ]);
      if (!isCurrent()) return;
      const profileSummary = buildProfileSummary(result);
      let profilePosition = null;
      if (result && !profileSummary) {
        const positionPayload = await api.getAssessmentProfilePosition(result.id).catch(() => null);
      if (!isCurrent()) return;
        profilePosition = buildProfilePositionSummary(positionPayload);
      }
      const scaleDimensions = buildScaleDimensions(result, profileSummary);
      const scaleVisualization = decorateVisualization(buildDimensionVisualization(scaleDimensions, worksheet));
      const sourceNotice = buildSourceNotice(worksheet, profileSummary);
      const riskSummary = buildRiskSummary(result);
      // Apply the existing high-risk boundary before display and local recommendation caching.
      const highRisk = (riskSummary && riskSummary.riskLevel === "high")
        || (profileSummary && profileSummary.riskLevel === "high");
      const trainingRecommendation = highRisk ? null : buildTrainingRecommendation(worksheet, profileSummary, cards, result);
      if (highRisk || (profileSummary && !profileSummary.allowAutoFeedback)) {
        // These are derived suggestions, not the user's assessment or diary records.
        wx.removeStorageSync(LATEST_TRAINING_RECOMMENDATION_KEY);
        wx.removeStorageSync(THREE_DAY_LIGHT_PLAN_KEY);
      }
      const exploratoryAnalysis = buildEmotionInsightsView(exploratoryPayload);
      saveLatestTrainingRecommendation(trainingRecommendation);
      this.setData(
        {
          result,
          worksheet,
          resultMetaText: buildResultMeta(result, worksheet),
          loading: false,
          totalScoreText: result && result.total_score !== null && result.total_score !== undefined ? `${result.total_score}` : "本工作表不自动计分",
          recommendedCardsText: profileSummary
            ? profileSummary.recommendedCardsText
            : worksheet && worksheet.recommended_card_ids && worksheet.recommended_card_ids.length
              ? "已为你准备练习建议"
              : "暂无固定推荐",
          profileSummary,
          scaleDimensions,
          scaleVisualization,
          dimensionGuideBoundary: result && result.dimension_guides ? String(result.dimension_guides.boundary || "") : "",
          // Scale-specific reading guide saved with the result (what it observes, what it is not).
          resultSummaryText: !profileSummary && result && result.result_summary ? String(result.result_summary) : "",
          sourceNotice,
          trainingRecommendation,
          riskSummary,
          profilePosition,
          exploratoryAnalysis,
        },
        () => {
          this.drawProfilePositionCharts();
          this.drawScaleDimensionChart();
        },
      );
    } catch (error) {
      if (!isCurrent()) return;
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
    // 散点（Figma 679:3894）：纸色底由外框提供；十字细线；参照组 16px 浅青瓷圆 + 编号；当前位置 20px 青瓷圆。
    this.withCanvasSize(".position-canvas", { width: 310, height: 180 }, ({ width, height }) => {
      const ctx = wx.createCanvasContext("profilePlotCanvas", this);
      ctx.clearRect(0, 0, width, height);
      ctx.setStrokeStyle(CHART_COLORS.hairline);
      ctx.setLineWidth(1);
      ctx.beginPath();
      ctx.moveTo(24, height / 2);
      ctx.lineTo(width - 24, height / 2);
      ctx.moveTo(width / 2, 20);
      ctx.lineTo(width / 2, height - 20);
      ctx.stroke();

      ctx.setTextBaseline("middle");
      (profilePosition.clusterPoints || []).forEach((point) => {
        const x = (Number(point.xPercent) / 100) * width;
        const y = (Number(point.yPercent) / 100) * height;
        ctx.setFillStyle(CHART_COLORS.soft);
        ctx.beginPath();
        ctx.arc(x, y, 8, 0, Math.PI * 2);
        ctx.fill();
        ctx.setFillStyle(CHART_COLORS.muted);
        ctx.setFontSize(13);
        ctx.setTextAlign("center");
        ctx.fillText(point.axisLabel || "", x, y);
      });

      const ux = (Number(profilePosition.userPoint.xPercent) / 100) * width;
      const uy = (Number(profilePosition.userPoint.yPercent) / 100) * height;
      ctx.setFillStyle(CHART_COLORS.primary);
      ctx.beginPath();
      ctx.arc(ux, uy, 10, 0, Math.PI * 2);
      ctx.fill();
      ctx.setFillStyle(CHART_COLORS.ink);
      ctx.setFontSize(13);
      ctx.setTextAlign(ux > width * 0.7 ? "right" : "left");
      ctx.fillText("当前位置", ux > width * 0.7 ? ux - 14 : ux + 14, Math.max(uy - 18, 12));
      ctx.draw();
    });
  },

  drawRadarCanvas(profilePosition) {
    const features = profilePosition.radarFeatures || [];
    if (features.length < 3) return;
    // 画像轮廓（Figma 679:3920）：33/66/100% 三圈细线，编号轴；本次轮廓青瓷 2px + 16% 填充 + 5px 点。
    this.withCanvasSize(".radar-canvas", { width: 310, height: 200 }, ({ width, height }) => {
      const ctx = wx.createCanvasContext("profileRadarCanvas", this);
      const centerX = width / 2;
      const centerY = height / 2;
      const radius = Math.min(width * 0.23, height * 0.33);
      const pointAt = (index, distance) => {
        const angle = (Math.PI * 2 * index) / features.length - Math.PI / 2;
        return { angle, x: centerX + Math.cos(angle) * distance, y: centerY + Math.sin(angle) * distance };
      };
      ctx.clearRect(0, 0, width, height);

      ctx.setStrokeStyle(CHART_COLORS.hairline);
      ctx.setLineWidth(1);
      [0.33, 0.66, 1].forEach((ratio) => {
        ctx.beginPath();
        features.forEach((_item, index) => {
          const point = pointAt(index, radius * ratio);
          if (index === 0) ctx.moveTo(point.x, point.y);
          else ctx.lineTo(point.x, point.y);
        });
        ctx.closePath();
        ctx.stroke();
      });
      features.forEach((_item, index) => {
        const point = pointAt(index, radius);
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(point.x, point.y);
        ctx.stroke();
      });

      ctx.setStrokeStyle(CHART_COLORS.primary);
      ctx.setFillStyle(CHART_COLORS.primaryFill);
      ctx.setLineWidth(2);
      ctx.beginPath();
      features.forEach((item, index) => {
        const point = pointAt(index, radius * item.value);
        if (index === 0) ctx.moveTo(point.x, point.y);
        else ctx.lineTo(point.x, point.y);
      });
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.setFillStyle(CHART_COLORS.primary);
      features.forEach((item, index) => {
        const point = pointAt(index, radius * item.value);
        ctx.beginPath();
        ctx.arc(point.x, point.y, 2.5, 0, Math.PI * 2);
        ctx.fill();
      });

      ctx.setFillStyle(CHART_COLORS.muted);
      ctx.setFontSize(13);
      ctx.setTextAlign("center");
      ctx.setTextBaseline("middle");
      features.forEach((item, index) => {
        const point = pointAt(index, radius + 16);
        ctx.fillText(item.axisLabel || String(index + 1), Math.max(10, Math.min(point.x, width - 10)), Math.max(10, Math.min(point.y, height - 10)));
      });
      ctx.draw();
    });
  },

  drawScaleDimensionChart() {
    const visualization = this.data.scaleVisualization;
    const features = visualization && visualization.radarFeatures ? visualization.radarFeatures : [];
    if (!visualization || !visualization.showRadar || features.length < 3) return;
    // 维度雷达（Figma 679:3649）：H228，R = min(.23W, .33H)；25/75/100% 细线圈；量尺中点 50% 虚线；
    // 本次填写青瓷 2px + 16% 填充 + 5px 点；标签 13px 墨色，距外圈 12，按方向左/中/右对齐，7 字截断。
    this.withCanvasSize(".dimension-radar-canvas", { width: 314, height: 228 }, ({ width, height }) => {
      const ctx = wx.createCanvasContext("dimensionRadarCanvas", this);
      const centerX = width / 2;
      const centerY = height / 2;
      const axisAngle = (index) => (Math.PI * 2 * index) / features.length - Math.PI / 2;
      const labelWidths = features.map((item) => estimateTextWidth(item.axisLabel, RADAR_LABEL_SIZE));
      // 侧向长标签收回画布内后与外圈顶点至少留 2px；设计宽度下不触发，窄屏时才缩小半径。
      const fittedRadius = features.reduce((limit, _item, index) => {
        const cos = Math.abs(Math.cos(axisAngle(index)));
        return cos > 0.25 ? Math.min(limit, (centerX - labelWidths[index] - 2) / cos) : limit;
      }, Math.min(width * 0.23, height * 0.33));
      const radius = Math.max(width * 0.15, fittedRadius);
      const pointAt = (index, distance) => {
        const angle = axisAngle(index);
        return { angle, x: centerX + Math.cos(angle) * distance, y: centerY + Math.sin(angle) * distance };
      };
      const tracePolygon = (distanceOf) => {
        ctx.beginPath();
        features.forEach((item, index) => {
          const point = pointAt(index, distanceOf(item));
          if (index === 0) ctx.moveTo(point.x, point.y);
          else ctx.lineTo(point.x, point.y);
        });
        ctx.closePath();
      };

      ctx.clearRect(0, 0, width, height);
      ctx.setStrokeStyle(CHART_COLORS.hairline);
      ctx.setLineWidth(1);
      [0.25, 0.75, 1].forEach((ratio) => {
        tracePolygon(() => radius * ratio);
        ctx.stroke();
      });
      features.forEach((_item, index) => {
        const point = pointAt(index, radius);
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(point.x, point.y);
        ctx.stroke();
      });

      // 量尺中点（参考线）：虚线，不是常模或目标值。
      ctx.setStrokeStyle(CHART_COLORS.muted);
      ctx.setLineWidth(1.25);
      ctx.setLineDash([4, 3], 0);
      tracePolygon((item) => radius * Number(item.referenceValue === undefined ? 0.5 : item.referenceValue));
      ctx.stroke();
      ctx.setLineDash([], 0);

      ctx.setStrokeStyle(CHART_COLORS.primary);
      ctx.setFillStyle(CHART_COLORS.primaryFill);
      ctx.setLineWidth(2);
      tracePolygon((item) => radius * Number(item.value));
      ctx.fill();
      ctx.stroke();
      ctx.setFillStyle(CHART_COLORS.primary);
      features.forEach((item, index) => {
        const point = pointAt(index, radius * Number(item.value));
        ctx.beginPath();
        ctx.arc(point.x, point.y, 2.5, 0, Math.PI * 2);
        ctx.fill();
      });

      ctx.setFillStyle(CHART_COLORS.ink);
      ctx.setFontSize(RADAR_LABEL_SIZE);
      ctx.setTextBaseline("middle");
      features.forEach((item, index) => {
        const point = pointAt(index, radius + 12);
        const cos = Math.cos(point.angle);
        const align = cos > 0.25 ? "left" : cos < -0.25 ? "right" : "center";
        const labelWidth = labelWidths[index];
        // 贴边标签整段收回画布（Figma 中「较少被情绪卷入」左缘对齐画布左缘），不截字。
        let x = point.x;
        if (align === "right") x = Math.max(x, labelWidth);
        else if (align === "left") x = Math.min(x, width - labelWidth);
        else x = Math.max(labelWidth / 2, Math.min(x, width - labelWidth / 2));
        ctx.setTextAlign(align);
        ctx.fillText(item.axisLabel, x, Math.max(10, Math.min(point.y, height - 10)));
      });
      ctx.draw();
    });
  },

  openRecommendedCards() {
    const profileSummary = this.data.profileSummary;
    if ((this.data.riskSummary && this.data.riskSummary.riskLevel === "high")
      || (profileSummary && !profileSummary.canOpenRecommendedCards)) {
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

  openEmergencyResources() {
    wx.navigateTo({ url: "/pages/emergency-resources/index" });
  },

  backToAssessment() {
    wx.navigateBack({ delta: 2 });
  },
});
