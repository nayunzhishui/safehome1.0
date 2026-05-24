Page({
  data: {
    hotTopics: [
      {
        id: "exam-setback",
        title: "孩子考试失利后，家长第一句话怎么说？",
        tag: "考试压力",
        readTime: "4分钟阅读",
      },
      {
        id: "emotion-outburst",
        title: "孩子发脾气时，为什么讲道理没用？",
        tag: "情绪爆发",
        readTime: "4分钟阅读",
      },
      {
        id: "repair-after-conflict",
        title: "亲子冲突后，如何重新连接？",
        tag: "关系修复",
        readTime: "5分钟阅读",
      },
    ],
    coreEntries: [
      {
        key: "diary",
        title: "写一篇情绪日记",
        subtitle: "记录情绪",
        iconText: "记",
        accentColor: "#4CAF7D",
        accentBg: "#EEF8E9",
      },
      {
        key: "training",
        title: "完成今日UP训练",
        subtitle: "稳定回应",
        iconText: "练",
        accentColor: "#F28B38",
        accentBg: "#FFF2DF",
      },
      {
        key: "assessment",
        title: "测一测家庭关系",
        subtitle: "互动反馈",
        iconText: "测",
        accentColor: "#2F86DF",
        accentBg: "#EEF6FF",
      },
    ],
    growthStats: [
      {
        label: "连续打卡",
        value: "7天",
      },
      {
        label: "情绪日记",
        value: "12篇",
      },
      {
        label: "训练完成",
        value: "8次",
      },
    ],
    recommendedTask: {
      title: "情绪命名练习",
      subtitle: "先把感受说清楚，再选择下一步回应",
      stage: "今日推荐",
      duration: "3-5 分钟",
      scenario: "亲子冲突前、语气升高前",
      tag: "推荐",
    },
  },

  startGoalSetting() {
    wx.navigateTo({ url: "/pages/goal-setting/index" });
  },

  startDiary() {
    wx.navigateTo({ url: "/pages/diary-form/index" });
  },

  openWeeklyReport() {
    wx.navigateTo({ url: "/pages/weekly-report/index" });
  },

  openIntegrationTest() {
    wx.navigateTo({ url: "/pages/integration-test/index" });
  },

  openCoreEntry(event) {
    const key = event.currentTarget.dataset.key;
    if (key === "diary") {
      this.startDiary();
      return;
    }
    if (key === "training") {
      wx.switchTab({ url: "/pages/training/index" });
      return;
    }
    if (key === "assessment") {
      wx.navigateTo({ url: "/pages/assessment/index" });
    }
  },

  openRecommendedTraining() {
    wx.navigateTo({
      url: `/pages/training-card/index?tags=${encodeURIComponent("high_demand_language,emotional_behavior")}`,
    });
  },

  openHotTopics() {
    wx.navigateTo({ url: "/pages/hot-topics/index" });
  },

  openHotTopic(event) {
    const id = event.currentTarget.dataset.id || "";
    wx.navigateTo({
      url: `/pages/hot-topics/index?id=${encodeURIComponent(id)}`,
    });
  },

  showComingSoon(title) {
    wx.showToast({
      title,
      icon: "none",
    });
  },
});
