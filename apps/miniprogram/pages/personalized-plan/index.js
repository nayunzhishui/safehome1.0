const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

Page({
  data: {
    loading: true,
    plan: null,
    planItems: [],
    errorMessage: "",
    boundaryNotice: "个性化训练计划只用于阶段性练习建议，不构成诊断、筛查或治疗方案。",
  },

  onShow() {
    this.loadPlan();
  },

  loadPlan() {
    this.setData({ loading: true, errorMessage: "" });
    api
      .getTrainingPlan()
      .then((plan) => {
        this.setData({
          loading: false,
          plan,
          planItems: (plan.plan_items || []).map((item) => ({
            ...item,
            sourceLabel: item.source_type === "profile_cluster" ? "画像推荐" : "测评推荐",
            cardIdsText: Array.isArray(item.card_ids) ? item.card_ids.join(",") : "",
          })),
          boundaryNotice: plan.boundary_notice || this.data.boundaryNotice,
        });
      })
      .catch((error) => {
        this.setData({
          loading: false,
          errorMessage: error.message || "训练方案暂时没能读取，请检查网络后再试一次。",
        });
        wx.showToast({ title: error.message || "读取失败", icon: "none" });
      });
  },

  openAssessment() {
    wx.navigateTo({ url: "/pages/assessment/index" });
  },

  openCard(event) {
    const ids = event.currentTarget.dataset.cardIds || "";
    if (!ids) {
      wx.showToast({ title: "暂无可打开的训练卡", icon: "none" });
      return;
    }
    wx.navigateTo({ url: `/pages/training-card/index?card_ids=${encodeURIComponent(ids)}` });
  },
});
