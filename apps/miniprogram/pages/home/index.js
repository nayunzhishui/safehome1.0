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
        title: "情绪日记",
        subtitle: "记录此刻",
        iconText: "✎",
        accentColor: "#4E7C6B",
        accentBg: "#E7F0E2",
      },
      {
        key: "feedback",
        title: "AI分析",
        subtitle: "智能反馈",
        iconText: "AI",
        accentColor: "#8069A8",
        accentBg: "#F1ECF8",
      },
      {
        key: "training",
        title: "训练中心",
        subtitle: "提升自己",
        iconText: "⌁",
        accentColor: "#4E7C6B",
        accentBg: "#EEF4E8",
      },
      {
        key: "supervision",
        title: "专家支持",
        subtitle: "人工督导",
        iconText: "●",
        accentColor: "#6A86B4",
        accentBg: "#E9F0FA",
      },
      {
        key: "assessment",
        title: "测一测",
        subtitle: "家庭关系",
        iconText: "测",
        accentColor: "#6A86B4",
        accentBg: "#E9F0FA",
      },
    ],
    latestRecord: {
      mood: "有点烦",
      time: "昨天 21:30",
      trigger: "孩子写作业磨蹭",
      status: "AI 分析已完成",
    },
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
    if (key === "feedback") {
      wx.navigateTo({ url: "/pages/feedback-result/index" });
      return;
    }
    if (key === "supervision") {
      wx.navigateTo({ url: "/pages/supervision/index" });
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
