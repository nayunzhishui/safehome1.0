const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

Page({
  data: {
    id: "",
    loading: true,
    errorMessage: "",
    message: null,
  },

  onLoad(options) {
    const id = decodeURIComponent(options.id || "");
    this.setData({ id });
    this.loadMessage(id);
  },

  async loadMessage(id) {
    if (!id) {
      this.setData({ loading: false, errorMessage: "缺少消息 ID。" });
      return;
    }
    this.setData({ loading: true, errorMessage: "" });
    try {
      const message = await api.getMessage(id);
      this.setData({ loading: false, message });
    } catch (error) {
      this.setData({
        loading: false,
        errorMessage: error.message || "消息暂时没能打开。",
      });
    }
  },

  goMessages() {
    wx.navigateBack();
  },
});
