const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

Page({
  data: {
    loading: true,
    programs: [],
    errorMessage: "",
    boundaryNotice: "项目测试内容只用于陪伴练习和自我观察，不构成诊断、筛查或治疗方案。",
  },

  onShow() {
    this.loadPrograms();
  },

  loadPrograms() {
    this.setData({ loading: true, errorMessage: "" });
    api
      .listPrograms()
      .then((data) => {
        this.setData({
          loading: false,
          programs: data.items || [],
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
    wx.navigateTo({ url: `/pages/program-detail/index?id=${encodeURIComponent(id)}` });
  },
});
