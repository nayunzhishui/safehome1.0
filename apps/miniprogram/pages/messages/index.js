const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

Page({
  data: {
    loading: true,
    errorMessage: "",
    needsLogin: false,
    messages: [],
    unreadCount: 0,
  },

  onShow() {
    this.loadMessages();
  },

  async loadMessages() {
    this.setData({ loading: true, errorMessage: "", needsLogin: false });
    try {
      // CloudBase currently rejects the legacy `limit` response headers at
      // the gateway. `page_size` is the canonical equivalent and avoids 502.
      const result = await api.listMessages({ page: 1, page_size: 50 });
      this.setData({
        loading: false,
        messages: result.items || [],
        unreadCount: result.unread_count || 0,
      });
    } catch (error) {
      const needsLogin = error && (
        error.statusCode === 401
        || error.status === 401
        || error.code === "auth_required"
        || error.code === "unauthorized"
      );
      this.setData({
        loading: false,
        errorMessage: error.message || "消息暂时没能加载，请检查网络后再试一次。",
        needsLogin,
      });
    }
  },

  openMessage(event) {
    const id = event.currentTarget.dataset.id;
    if (!id) return;
    wx.navigateTo({ url: `/pages/message-detail/index?id=${encodeURIComponent(id)}` });
  },

  handleStateAction() {
    if (this.data.needsLogin) {
      this.goLogin();
      return;
    }
    this.loadMessages();
  },

  goHome() {
    wx.reLaunch({ url: "/pages/home/index" });
  },

  goLogin() {
    wx.navigateTo({ url: "/pages/login/index?redirect=%2Fpages%2Fmessages%2Findex" });
  },

  goRegister() {
    wx.navigateTo({ url: "/pages/register/index?redirect=%2Fpages%2Fmessages%2Findex" });
  },
});
