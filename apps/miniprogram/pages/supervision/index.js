const { createSafeHomeApi } = require("../../services/api");

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
    this.setData({
      diaryId: decodeURIComponent(options.diary_id || ""),
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
        successMessage: "已提交给人工督导入口。老师后续可以基于这条记录补充练习建议。",
      });
    } catch (error) {
      this.setData({
        errorMessage: error.message || "提交失败，请确认 backend 是否已启动。",
      });
    } finally {
      this.setData({ submitting: false });
    }
  },

  goHome() {
    wx.reLaunch({ url: "/pages/home/index" });
  },
});
