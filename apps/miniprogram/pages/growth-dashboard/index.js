const { createSafeHomeApi } = require("../../services/api");
const { requireLogin } = require("../../utils/authGuard");

const api = createSafeHomeApi();

function formatDate(value) {
  return value ? String(value).slice(0, 10) : "";
}

Page({
  data: {
    loading: true,
    errorMessage: "",
    growth: null,
    timeline: [],
    thermometer: [],
    assessmentGroups: [],
  },

  onLoad() {
    if (!requireLogin({ redirectUrl: "/pages/growth-dashboard/index" })) return;
    this.loadGrowth();
  },

  async loadGrowth() {
    this.setData({ loading: true, errorMessage: "" });
    try {
      const growth = await api.getGrowthOverview();
      this.setData({
        loading: false,
        growth,
        thermometer: (growth.thermometer || []).map((item) => ({
          ...item,
          dateText: formatDate(item.created_at),
          width: `${Math.max(10, Number(item.intensity_level || 0) * 10)}%`,
        })),
        assessmentGroups: (growth.assessment_groups || []).map((group) => ({
          ...group,
          items: (group.items || []).map((item) => ({ ...item, dateText: formatDate(item.created_at) })),
        })),
        timeline: (growth.timeline || []).map((item) => ({ ...item, dateText: formatDate(item.created_at) })),
      });
    } catch (error) {
      this.setData({ loading: false, errorMessage: error.message || "成长记录暂时无法读取。" });
    }
  },
});
