Page({
  data: {
    user: {
      nickname: "温暖的家长",
      loginState: "当前为试点体验模式",
      streakText: "连续打卡 7 天",
      growthLevel: "本周有记录",
    },
    recordEntries: [
      {
        title: "周报入口",
        subtitle: "查看本周变化",
        iconText: "周",
        accentColor: "#4CAF7D",
        accentBg: "#EEF8E9",
        url: "/pages/weekly-report/index",
      },
      {
        title: "历次反馈",
        subtitle: "后续接入反馈记录",
        iconText: "反",
        accentColor: "#2F86DF",
        accentBg: "#EEF6FF",
        url: "",
      },
      {
        title: "训练记录",
        subtitle: "后续接入练习轨迹",
        iconText: "练",
        accentColor: "#4CAF7D",
        accentBg: "#EEF8E9",
        url: "",
      },
      {
        title: "测评记录",
        subtitle: "回顾支持性测评",
        iconText: "测",
        accentColor: "#7A5BEF",
        accentBg: "#F2EDFF",
        url: "",
      },
    ],
    supportEntries: [
      {
        title: "人工督导",
        subtitle: "获得专业补充反馈",
        iconText: "督",
        accentColor: "#F28B38",
        accentBg: "#FFF2DF",
        url: "/pages/supervision/index",
      },
      {
        title: "专业资源说明",
        subtitle: "了解线下支持边界",
        iconText: "询",
        accentColor: "#2F86DF",
        accentBg: "#EEF6FF",
        url: "",
      },
    ],
    safetyEntries: [
      {
        title: "紧急安全指引",
        subtitle: "出现安全风险时先找现实帮助",
        iconText: "急",
        accentColor: "#FF6B6B",
        accentBg: "#FFF0ED",
        url: "",
      },
      {
        title: "紧急帮助说明",
        subtitle: "了解可用现实资源",
        iconText: "助",
        accentColor: "#F28B38",
        accentBg: "#FFF2DF",
        url: "",
      },
    ],
    settingsEntries: [
      {
        title: "知情与边界",
        subtitle: "了解本工具能做什么",
        iconText: "知",
        accentColor: "#4CAF7D",
        accentBg: "#EEF8E9",
        url: "",
      },
      {
        title: "隐私说明",
        subtitle: "后续接入隐私文本",
        iconText: "隐",
        accentColor: "#2F86DF",
        accentBg: "#EEF6FF",
        url: "",
      },
    ],
  },

  openEntry(event) {
    const group = event.currentTarget.dataset.group || "recordEntries";
    const index = event.currentTarget.dataset.index;
    const list = this.data[group] || [];
    const entry = list[index];
    if (!entry) return;
    if (!entry.url) {
      wx.showToast({
        title: `${entry.title}后续接入`,
        icon: "none",
      });
      return;
    }
    wx.navigateTo({ url: entry.url });
  },
});
