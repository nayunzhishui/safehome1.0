const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

function groupByCategory(items) {
  const groups = [];
  (items || []).forEach((item) => {
    const normalizedItem = {
      ...item,
      is_student_profile: item.id === "student_profile_v1" || item.category === "学生画像",
      action_text: item.id === "student_profile_v1" || item.category === "学生画像" ? "开始支持性测评" : item.is_reference ? "查看示例" : "开始填写",
    };
    const category = item.category || "其他";
    let group = groups.find((entry) => entry.category === category);
    if (!group) {
      group = { category, items: [] };
      groups.push(group);
    }
    group.items.push(normalizedItem);
  });
  return groups;
}

Page({
  data: {
    loading: true,
    errorMessage: "",
    boundaryNotice: "",
    categories: [],
    recentResults: [],
    infoItems: [
      {
        label: "内容来源",
        value: "已授权工作表原文",
      },
      {
        label: "结果用途",
        value: "用于自我观察、阶段性画像和练习记录",
      },
      {
        label: "数据保存",
        value: "提交后保存到本地后端",
      },
      {
        label: "边界提示",
        value: "不用于诊断或替代专业帮助",
      },
    ],
  },

  onLoad() {
    this.loadAssessments();
  },

  onShow() {
    this.loadRecentResults();
  },

  async loadAssessments() {
    this.setData({ loading: true, errorMessage: "" });
    try {
      const result = await api.listAssessments();
      this.setData({
        loading: false,
        boundaryNotice: result.boundary_notice || "",
        categories: groupByCategory(result.items || []),
      });
    } catch (error) {
      this.setData({
        loading: false,
        errorMessage: error.message || "测一测内容获取失败，请确认 backend 是否已启动。",
      });
    }
  },

  async loadRecentResults() {
    try {
      const result = await api.listAssessmentResults({ limit: 3 });
      this.setData({ recentResults: result.items || [] });
    } catch (error) {
      this.setData({ recentResults: [] });
    }
  },

  openAssessmentEntry(event) {
    const id = event.currentTarget.dataset.id;
    if (!id) return;
    wx.navigateTo({
      url: `/pages/assessment-detail/index?id=${encodeURIComponent(id)}`,
    });
  },
});
