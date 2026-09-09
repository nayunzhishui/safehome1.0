const LATEST_TRAINING_RECOMMENDATION_KEY = "safehome:latestTrainingRecommendation";
const THREE_DAY_LIGHT_PLAN_KEY = "safehome:threeDayLightPlan";
const { createSafeHomeApi } = require("../../services/api");
const { getAuthUser } = require("../../utils/authGuard");

const api = createSafeHomeApi();

Page({
  data: {
    relationshipPilotAvailable: false,
    latestRecommendation: null,
    threeDayPlan: null,
    lightPlanExpanded: false,
    libraryExpanded: false,
    trainingStages: [],
    cardsLoading: true,
    cardsError: "",
  },

  async loadAvailableCards() {
    const loadId = this._cardsLoadId = (this._cardsLoadId || 0) + 1;
    const token = wx.getStorageSync("auth_token");
    this._availableCards = [];
    this.setData({ cardsLoading: true, cardsError: "", trainingStages: [], latestRecommendation: null, threeDayPlan: null });
    try {
      const result = await api.listCards();
      if (loadId !== this._cardsLoadId || token !== wx.getStorageSync("auth_token")) return;
      const cards = result.items || [];
      this._availableCards = cards;
      this.setData({ cardsLoading: false, trainingStages: cards.length ? [{
        title: "当前可用练习", subtitle: "", tasks: cards.map(card => ({
          id: card.id, title: card.title, subtitle: card.purpose || "",
          duration: card.duration_minutes ? `${card.duration_minutes} 分钟` : "按个人节奏",
          scenario: card.suitable_scene || (card.suitable_for || [])[0] || "",
          stage: "", tag: "", tagsText: "",
        })),
      }] : [] });
      this.loadLatestRecommendation();
      this.loadThreeDayPlan();
      this.filterCompletedRecommendations(getAuthUser());
    } catch (error) {
      if (loadId === this._cardsLoadId && token === wx.getStorageSync("auth_token")) this.setData({ cardsLoading: false, cardsError: error.message || "可用练习暂时无法读取，请重试。" });
    }
  },
  onHide() { this._cardsLoadId = (this._cardsLoadId || 0) + 1; this._availableCards = []; this.setData({ trainingStages: [], latestRecommendation: null, threeDayPlan: null }); },
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
      const recommendation = this.data.latestRecommendation;
      const lightPlan = this.data.threeDayPlan;
      const cardIds = recommendation
        ? [...recommendation.cardIds.filter((id) => !completed.has(id)), ...recommendation.cardIds.filter((id) => completed.has(id))]
        : [];
      const cardById = {};
      if (recommendation) recommendation.cards.forEach((card) => { cardById[card.id] = card; });
      const cards = cardIds.map((id) => ({ ...cardById[id], recentlyCompleted: completed.has(id) })).filter((card) => card.id);
      const days = lightPlan
        ? [...lightPlan.days.filter((day) => !completed.has(day.cardId)), ...lightPlan.days.filter((day) => completed.has(day.cardId))]
        : [];
      this.setData({
        latestRecommendation: recommendation
          ? { ...recommendation, cardIds, cards, primaryCard: cards[0] || null, cardIdsText: cardIds.slice(0, 3).join(",") }
          : null,
        threeDayPlan: lightPlan ? { ...lightPlan, days } : null,
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
    this.setData({
      latestRecommendation: {
        ...recommendation,
        cards: Array.isArray(recommendation.cards) ? recommendation.cards.slice(0, 3) : [],
        primaryCard: Array.isArray(recommendation.cards) ? recommendation.cards[0] || null : null,
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
    plan = { ...plan, days };
    this.setData({
      threeDayPlan: {
        ...plan,
        days: plan.days.slice(0, 3),
      },
    });
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

  openPersonalizedPlan() {
    wx.navigateTo({ url: "/pages/personalized-plan/index" });
  },

  openProgramList() {
    wx.navigateTo({ url: "/pages/program-list/index" });
  },

  toggleLightPlan() {
    this.setData({ lightPlanExpanded: !this.data.lightPlanExpanded });
  },

  toggleLibrary() {
    this.setData({ libraryExpanded: !this.data.libraryExpanded });
  },

  openRelationshipPilot() {
    wx.navigateTo({ url: "/pages/relationship-pilot/index" });
  },

  openTrainingCard(event) {
    const id = (event.detail && event.detail.id) || event.currentTarget.dataset.id || event.target.dataset.id || "";
    wx.navigateTo({
      url: `/pages/task-detail/index?card_id=${encodeURIComponent(id)}`,
    });
  },
});
