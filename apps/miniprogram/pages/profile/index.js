Page({
  data: {
    user: {
      nickname: "温暖的家长",
      loginState: "登录后查看个人周报和训练记录",
      streakText: "连续打卡 7 天",
      growthLevel: "家庭成长值 680",
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
        subtitle: "回顾训练建议",
        iconText: "反",
        accentColor: "#2F86DF",
        accentBg: "#EEF6FF",
        url: "",
      },
      {
        title: "训练记录",
        subtitle: "查看练习轨迹",
        iconText: "练",
        accentColor: "#4CAF7D",
        accentBg: "#EEF8E9",
        url: "",
      },
      {
        title: "测评记录",
        subtitle: "回顾互动反馈",
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
        title: "心理咨询",
        subtitle: "预约进一步支持",
        iconText: "询",
        accentColor: "#2F86DF",
        accentBg: "#EEF6FF",
        url: "",
      },
    ],
    safetyEntries: [
      {
        title: "危机干预",
        subtitle: "紧急情况下获得帮助指引",
        iconText: "急",
        accentColor: "#FF6B6B",
        accentBg: "#FFF0ED",
        url: "",
      },
      {
        title: "紧急帮助说明",
        subtitle: "了解可用安全资源",
        iconText: "助",
        accentColor: "#F28B38",
        accentBg: "#FFF2DF",
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
