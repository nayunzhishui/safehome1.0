const { createSafeHomeApi } = require("../../services/api");
const { getAuthUser } = require("../../utils/authGuard");

const api = createSafeHomeApi();

Page({
  data: {
    loading: true,
    programs: [],
    availability: null,
    previewMode: false,
    errorMessage: "",
    boundaryNotice: "项目测试内容只用于陪伴练习和自我观察，不构成诊断、筛查或治疗方案。",
  },

  onShow() {
    this.loadPrograms();
  },

  loadPrograms() {
    this.setData({ loading: true, errorMessage: "" });
    const user = getAuthUser();
    const previewMode = !!(user && ["researcher", "supervisor", "admin"].includes(user.role));
    api
      .listPrograms(previewMode ? { include_drafts: true } : {})
      .then((data) => {
        this.setData({
          loading: false,
          programs: data.items || [],
          availability: data.availability || null,
          previewMode,
          boundaryNotice: data.boundary_notice || this.data.boundaryNotice,
        });
      })
      .catch((error) => {
        this.setData({
          loading: false,
          errorMessage: error.message || "项目测试内容暂时没能读取，请检查网络后再试一次。",
        });
        wx.showToast({ title: error.message || "读取失败", icon: "none" });
      });
  },

  openProgram(event) {
    const id = event.currentTarget.dataset.id;
    if (!id) {
      return;
    }
    const preview = event.currentTarget.dataset.preview === "true";
    wx.navigateTo({ url: `/pages/program-detail/index?id=${encodeURIComponent(id)}${preview ? "&preview=1" : ""}` });
  },
});
