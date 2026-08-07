const {
  getMinorSafeguardStatus,
  confirmAge,
  updateChildAssent,
} = require("../../services/minorSafeguardsApi");

function nextStep(status) {
  if (!status) return "";
  if (status.age_verification_required) return "age";
  if (status.status === "guardian_link_required") return "guardian_link";
  if (status.status === "guardian_consent_required") return "guardian_consent";
  if (status.status === "child_assent_required") return "child_assent";
  if (status.status === "blocked_withdrawn_or_refused") return "blocked";
  return "complete";
}

Page({
  data: {
    loading: true,
    submitting: false,
    status: null,
    step: "age",
    errorMessage: "",
    boundaryNotice: "年龄确认只用于参与者保护和数据处理门禁，不用于诊断、能力判断或人格标签。",
  },

  onLoad() {
    this.refresh();
  },

  refresh() {
    this.setData({ loading: true, errorMessage: "" });
    getMinorSafeguardStatus()
      .then((status) => {
        const step = nextStep(status);
        this.setData({ status, step, loading: false });
        if (step === "complete") {
          this.finish();
        }
      })
      .catch((error) => {
        this.setData({
          loading: false,
          errorMessage: error.message || "暂时无法读取年龄保护状态，请稍后重试。",
        });
      });
  },

  chooseUnder14() {
    this.submitAge("under_14");
  },

  choose14OrOver() {
    this.submitAge("14_or_over");
  },

  submitAge(ageBand) {
    if (this.data.submitting) return;
    this.setData({ submitting: true, errorMessage: "" });
    confirmAge(ageBand)
      .then((status) => {
        this.setData({
          status,
          step: nextStep(status),
          submitting: false,
        });
        if (nextStep(status) === "complete") this.finish();
      })
      .catch((error) => {
        this.setData({ submitting: false, errorMessage: error.message || "年龄确认没有完成，请重试。" });
      });
  },

  acceptChildAssent() {
    if (this.data.submitting) return;
    this.setData({ submitting: true, errorMessage: "" });
    updateChildAssent(true)
      .then((status) => {
        this.setData({ status, step: nextStep(status), submitting: false });
        if (nextStep(status) === "complete") this.finish();
      })
      .catch((error) => this.setData({ submitting: false, errorMessage: error.message || "确认没有完成，请重试。" }));
  },

  refuseChildAssent() {
    if (this.data.submitting) return;
    wx.showModal({
      title: "确认暂不继续？",
      content: "选择暂不继续后，测评、研究参与和画像等受保护功能会停止。以后如需继续，需要重新确认。",
      confirmText: "暂不继续",
      cancelText: "返回",
      success: (result) => {
        if (!result.confirm) return;
        this.setData({ submitting: true, errorMessage: "" });
        updateChildAssent(false)
          .then((status) => this.setData({ status, step: nextStep(status), submitting: false }))
          .catch((error) => this.setData({ submitting: false, errorMessage: error.message || "操作没有完成，请重试。" }));
      },
    });
  },

  goBindGuardian() {
    wx.switchTab({ url: "/pages/profile/index" });
  },

  goHome() {
    wx.switchTab({ url: "/pages/home/index" });
  },

  finish() {
    wx.showToast({ title: "保护设置已完成", icon: "success" });
    setTimeout(() => wx.switchTab({ url: "/pages/home/index" }), 350);
  },
});
