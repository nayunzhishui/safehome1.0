const { createSafeHomeApi } = require("../../services/api");
const { requireLogin } = require("../../utils/authGuard");

const api = createSafeHomeApi();

Page({
  data: {
    diaryId: "",
    message: "",
    contact: "",
    riskHint: "",
    submitting: false,
    successMessage: "",
    errorMessage: "",
  },

  onLoad(options) {
    const diaryId = decodeURIComponent(options.diary_id || "");
    if (!requireLogin({
      redirectUrl: `/pages/supervision/index?diary_id=${encodeURIComponent(diaryId)}`,
      message: "请先登录后再提交人工督导。",
    })) {
      return;
    }
    this.setData({
      diaryId,
    });
  },

  onTextInput(event) {
    const key = event.currentTarget.dataset.key;
    this.setData({ [key]: event.detail.value, successMessage: "", errorMessage: "" });
  },

  async submitSupervision() {
    const message = this.data.message.trim();

    if (!message) {
      this.setData({ errorMessage: "请先写下你想请老师进一步看的内容。" });
      return;
    }

    this.setData({ submitting: true, successMessage: "", errorMessage: "" });

    try {
      await api.createSupervision({
        diary_id: this.data.diaryId || undefined,
        message,
        contact: this.data.contact.trim(),
        risk_hint: this.data.riskHint.trim(),
        risk_level: "low",
      });

      this.setData({
        successMessage: "已提交。老师后续可以基于这条记录补充理解和练习建议，请不要把这里当作紧急求助入口。",
      });
    } catch (error) {
      this.setData({
        errorMessage: error.message || "这次提交暂时没能成功，请检查网络后再试一次。",
      });
    } finally {
      this.setData({ submitting: false });
    }
  },

  goHome() {
    wx.reLaunch({ url: "/pages/home/index" });
  },
});
