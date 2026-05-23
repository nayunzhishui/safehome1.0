Page({
  data: {
    infoItems: [
      {
        label: "测评时长",
        value: "约3-5分钟",
      },
      {
        label: "结果用途",
        value: "仅用于自我了解",
      },
      {
        label: "系统反馈",
        value: "生成家庭互动反馈和训练建议",
      },
      {
        label: "隐私提示",
        value: "记录仅用于生成个人反馈",
      },
    ],
    assessmentEntries: [
      {
        key: "communication",
        title: "家庭沟通状态",
        subtitle: "了解沟通节奏",
        iconText: "沟",
        accentColor: "#4CAF7D",
        accentBg: "#EEF8E9",
      },
      {
        key: "emotion",
        title: "亲子情绪互动",
        subtitle: "观察情绪回应",
        iconText: "情",
        accentColor: "#F28B38",
        accentBg: "#FFF2DF",
      },
      {
        key: "pressure",
        title: "家长压力与调节方式",
        subtitle: "看见压力线索",
        iconText: "压",
        accentColor: "#2F86DF",
        accentBg: "#EEF6FF",
      },
    ],
  },

  startAssessment() {
    wx.showToast({
      title: "测评题目后续接入",
      icon: "none",
    });
  },

  openAssessmentEntry(event) {
    const title = event.currentTarget.dataset.title || "测评";
    wx.showToast({
      title: `${title}后续接入`,
      icon: "none",
    });
  },
});
