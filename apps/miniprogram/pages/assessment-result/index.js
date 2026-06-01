const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

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
  return {
    profileName: scores.profile_name || "阶段性支持画像",
    profileCode: scores.profile_code || "",
    confidenceText: scores.confidence !== undefined && scores.confidence !== null ? `${Math.round(Number(scores.confidence) * 100)}%` : "暂未计算",
    riskLevel: scores.risk_level || "low",
    requiresReview: !!scores.requires_review,
    allowAutoFeedback: scores.allow_auto_feedback !== false,
    dimensions: scores.dimensions || [],
    supportiveExplanation: scores.supportive_explanation || "",
    strengthNote: scores.strength_note || "",
    smallStep: scores.small_step || "",
    boundaryNotice: scores.boundary_notice || "",
    recommendedCardIds: scores.recommended_card_ids || [],
    recommendedCardsText:
      scores.recommended_card_ids && scores.recommended_card_ids.length ? scores.recommended_card_ids.join("、") : "暂无普通训练卡推荐",
  };
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
      const [results, worksheet] = await Promise.all([
        api.listAssessmentResults({ limit: 20 }),
        this.data.worksheetId ? api.getAssessment(this.data.worksheetId) : Promise.resolve(null),
      ]);
      const result = (results.items || []).find((item) => item.id === this.data.resultId) || (results.items || [])[0];
      const profileSummary = buildProfileSummary(result);
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
