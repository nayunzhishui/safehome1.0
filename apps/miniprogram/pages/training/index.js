const LATEST_TRAINING_RECOMMENDATION_KEY = "safehome:latestTrainingRecommendation";
const THREE_DAY_LIGHT_PLAN_KEY = "safehome:threeDayLightPlan";
const { createSafeHomeApi } = require("../../services/api");
const { getAuthUser } = require("../../utils/authGuard");
const { groupTrainingLibrary } = require("../../utils/training-library");

const api = createSafeHomeApi();

function recommendationMeta(card) {
  const minutes = card && Number(card.duration_minutes);
  return minutes > 0 ? `约 ${minutes} 分钟 · 今天只做第一步` : "今天只做第一步";
}

// “为什么推荐”展开后的几行；今天的做法已在 3 天时间线第一天出现时不再重复。
function reasonRows(recommendation, hasPlan) {
  const rows = [];
  if (recommendation.reason) rows.push({ label: "推荐理由", text: recommendation.reason });
  if (recommendation.todaySuggestion && !hasPlan) rows.push({ label: "今天可以这样做", text: recommendation.todaySuggestion });
  if (recommendation.longTermSuggestion) rows.push({ label: "长期方向", text: recommendation.longTermSuggestion });
  return rows;
}

// 时间线按天排列：近期练过的标为已完成，第一个没练过的是当前这一步。
function planDays(days, completed) {
  let currentAssigned = false;
  return days.map((day) => {
    const done = completed.has(day.cardId);
    const state = done ? "done" : currentAssigned ? "upcoming" : "current";
    if (!done) currentAssigned = true;
    return { ...day, kicker: `${day.title} · ${day.role}`, state };
  });
}

Page({
  data: {
    relationshipPilotAvailable: false,
    latestRecommendation: null,
    recommendationReasonOpen: false,
    threeDayPlan: null,
    libraryStages: [],
    cardsLoading: true,
    cardsError: "",
  },

  async loadAvailableCards() {
    const loadId = this._cardsLoadId = (this._cardsLoadId || 0) + 1;
    const token = wx.getStorageSync("auth_token");
    this._availableCards = [];
    this._completedCardIds = new Set();
    this.setData({ cardsLoading: true, cardsError: "", libraryStages: [], latestRecommendation: null, threeDayPlan: null });
    try {
      const result = await api.listCards();
      if (loadId !== this._cardsLoadId || token !== wx.getStorageSync("auth_token")) return;
      const cards = result.items || [];
      this._availableCards = cards;
      this.setData({ cardsLoading: false, libraryStages: groupTrainingLibrary(cards) });
      this.loadLatestRecommendation();
      this.loadThreeDayPlan();
      this.filterCompletedRecommendations(getAuthUser());
    } catch (error) {
      if (loadId === this._cardsLoadId && token === wx.getStorageSync("auth_token")) this.setData({ cardsLoading: false, cardsError: error.message || "可用练习暂时无法读取，请重试。" });
    }
  },
  onHide() { this._cardsLoadId = (this._cardsLoadId || 0) + 1; this._availableCards = []; this.setData({ libraryStages: [], latestRecommendation: null, threeDayPlan: null }); },
  onUnload() { this.onHide(); },

  async onShow() {
    const cardsReady = this.loadAvailableCards();
    const loadId = this._cardsLoadId;
    const token = wx.getStorageSync("auth_token");
    const user = getAuthUser();
    const showcase = await api.getShowcaseAccess().catch(() => ({ enabled: false }));
    if (loadId === this._cardsLoadId && token === wx.getStorageSync("auth_token")) this.setData({ relationshipPilotAvailable: !!showcase.enabled || !!(user && user.role === "student") });
    await cardsReady;
  },

  async filterCompletedRecommendations(user) {
    if (!user) return;
    const loadId = this._cardsLoadId;
    const token = wx.getStorageSync("auth_token");
    try {
      const plan = await api.getTrainingPlan();
      if (loadId !== this._cardsLoadId || token !== wx.getStorageSync("auth_token")) return;
      const completed = new Set(plan.recently_completed_card_ids || []);
      if (!completed.size) return;
      this._completedCardIds = completed;
      const recommendation = this.data.latestRecommendation;
      const lightPlan = this.data.threeDayPlan;
      const cardIds = recommendation
        ? [...recommendation.cardIds.filter((id) => !completed.has(id)), ...recommendation.cardIds.filter((id) => completed.has(id))]
        : [];
      const cardById = {};
      if (recommendation) recommendation.cards.forEach((card) => { cardById[card.id] = card; });
      const cards = cardIds.map((id) => ({ ...cardById[id], recentlyCompleted: completed.has(id) })).filter((card) => card.id);
      const primaryCard = cards[0] || null;
      this.setData({
        latestRecommendation: recommendation
          ? { ...recommendation, cardIds, cards, primaryCard, metaText: recommendationMeta(primaryCard), cardIdsText: cardIds.slice(0, 3).join(",") }
          : null,
        threeDayPlan: lightPlan ? { ...lightPlan, days: planDays(lightPlan.days, completed) } : null,
      });
    } catch (error) {
      // Keep the training center usable when completion state is temporarily unavailable.
    }
  },

  loadLatestRecommendation() {
    let recommendation = wx.getStorageSync(LATEST_TRAINING_RECOMMENDATION_KEY);
    if (!recommendation || !Array.isArray(recommendation.cardIds) || !recommendation.cardIds.length) {
      this.setData({ latestRecommendation: null });
      return;
    }
    const available = new Map((this._availableCards || []).map(card => [card.id, card]));
    const cardIds = recommendation.cardIds.filter(id => available.has(id));
    if (!cardIds.length) { this.setData({ latestRecommendation: null }); return; }
    recommendation = { ...recommendation, cardIds, cards: cardIds.map(id => available.get(id)) };
    const primaryCard = recommendation.cards[0] || null;
    const plan = wx.getStorageSync(THREE_DAY_LIGHT_PLAN_KEY);
    const hasPlan = !!(plan && plan.sourceType === "assessment" && Array.isArray(plan.days) && plan.days.length);
    this.setData({
      recommendationReasonOpen: false,
      latestRecommendation: {
        ...recommendation,
        cards: recommendation.cards.slice(0, 3),
        primaryCard,
        metaText: recommendationMeta(primaryCard),
        reasonRows: reasonRows(recommendation, hasPlan),
        cardIdsText: recommendation.cardIds.slice(0, 3).join(","),
        sourceLabel: recommendation.sourceTitle || "最近推荐",
      },
    });
  },

  loadThreeDayPlan() {
    let plan = wx.getStorageSync(THREE_DAY_LIGHT_PLAN_KEY);
    if (!plan || plan.sourceType !== "assessment" || !Array.isArray(plan.days) || !plan.days.length) {
      this.setData({ threeDayPlan: null });
      return;
    }
    const available = new Map((this._availableCards || []).map(card => [card.id, card]));
    const days = plan.days.filter(day => available.has(day.cardId)).map(day => ({ ...day, cardTitle: available.get(day.cardId).title }));
    if (!days.length) { this.setData({ threeDayPlan: null }); return; }
    plan = { ...plan, days: planDays(days.slice(0, 3), this._completedCardIds || new Set()) };
    this.setData({ threeDayPlan: plan });
  },

  openPlanDay(event) {
    const cardId = event.currentTarget.dataset.cardId || "";
    if (!cardId) {
      wx.showToast({
        title: "这一天还没有对应训练卡。",
        icon: "none",
      });
      return;
    }

    wx.navigateTo({
      url: `/pages/training-card/index?card_ids=${encodeURIComponent(cardId)}`,
    });
  },

  openLatestRecommendation() {
    const recommendation = this.data.latestRecommendation;
    if (!recommendation || !recommendation.cardIdsText) {
      wx.showToast({
        title: "还没有最近推荐，可以先完成一次测一测或情绪日记。",
        icon: "none",
      });
      return;
    }

    wx.navigateTo({
      url: `/pages/training-card/index?card_ids=${encodeURIComponent(recommendation.cardIdsText)}`,
    });
  },

  toggleRecommendationReason() {
    this.setData({ recommendationReasonOpen: !this.data.recommendationReasonOpen });
  },

  // 训练库类别只带开放清单里实际存在的卡；训练卡页按“自己从训练库选”记录来源。
  openLibraryCategory(event) {
    const { ids, label } = event.currentTarget.dataset;
    if (!ids) return;
    wx.navigateTo({
      url: `/pages/training-card/index?card_ids=${encodeURIComponent(ids)}&source=library&topic=${encodeURIComponent(label || "")}`,
    });
  },

  openAssessment() {
    wx.navigateTo({ url: "/pages/assessment/index" });
  },

  openPersonalizedPlan() {
    wx.navigateTo({ url: "/pages/personalized-plan/index" });
  },

  openProgramList() {
    wx.navigateTo({ url: "/pages/program-list/index" });
  },

  openRelationshipPilot() {
    wx.navigateTo({ url: "/pages/relationship-pilot/index" });
  },
});
