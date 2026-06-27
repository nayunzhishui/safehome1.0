const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

function formatLocalDate(date) {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getDiaryDateKey(item) {
  const raw = item.event_time || item.created_at || "";
  if (!raw) {
    return "";
  }
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) {
    return raw.slice(0, 10);
  }
  return formatLocalDate(parsed);
}

Page({
  data: {
    todayRecordCount: 0,
    todayRecordCountReady: false,
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
    startSteps: [
      {
        key: "diary",
        title: "第一步",
        text: "记录一次具体事件",
        detail: "写下发生了什么、我的情绪和当时回应。",
        actionText: "去记录",
      },
      {
        key: "feedback",
        title: "第二步",
        text: "查看支持性反馈",
        detail: "看看这次记录中的互动线索和可调整位置。",
        actionText: "了解反馈",
      },
      {
        key: "training",
        title: "第三步",
        text: "选择一个小练习并打卡",
        detail: "从推荐训练卡里选一个动作，记录一次尝试。",
        actionText: "去练习",
      },
    ],
    coreEntries: [
      {
        key: "assessment",
        title: "测一测",
        subtitle: "先了解自己",
        iconText: "测",
        accentColor: "#6A86B4",
        accentBg: "#E9F0FA",
      },
      {
        key: "diary",
        title: "情绪日记",
        subtitle: "记录一次",
        iconText: "✎",
        accentColor: "#4E7C6B",
        accentBg: "#E7F0E2",
      },
      {
        key: "training",
        title: "训练中心",
        subtitle: "选择练习",
        iconText: "⌁",
        accentColor: "#4E7C6B",
        accentBg: "#EEF4E8",
      },
      {
        key: "feedback",
        title: "支持性反馈",
        subtitle: "记录后查看",
        iconText: "馈",
        accentColor: "#8069A8",
        accentBg: "#F1ECF8",
      },
      {
        key: "supervision",
        title: "人工支持",
        subtitle: "需要时提交",
        iconText: "●",
        accentColor: "#6A86B4",
        accentBg: "#E9F0FA",
      },
    ],
    latestRecord: {
      mood: "有点烦",
      time: "昨天 21:30",
      trigger: "孩子写作业磨蹭",
      status: "支持性反馈已完成",
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

  onShow() {
    this.refreshTodayRecordCount();
  },

  async refreshTodayRecordCount() {
    try {
      const todayKey = formatLocalDate(new Date());
      const result = await api.listDiaries({ limit: 100 });
      const items = result && Array.isArray(result.items) ? result.items : [];
      const todayRecordCount = items.filter((item) => getDiaryDateKey(item) === todayKey).length;
      this.setData({
        todayRecordCount,
        todayRecordCountReady: true,
      });
    } catch (error) {
      this.setData({
        todayRecordCount: 0,
        todayRecordCountReady: false,
      });
    }
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

  openGettingStarted() {
    wx.navigateTo({ url: "/pages/getting-started/index" });
  },

  openStartStep(event) {
    const key = event.currentTarget.dataset.key;
    if (key === "diary") {
      this.startDiary();
      return;
    }
    if (key === "training") {
      wx.switchTab({ url: "/pages/training/index" });
      return;
    }
    wx.navigateTo({ url: "/pages/getting-started/index" });
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
      wx.showToast({
        title: "请先记录一次事件",
        icon: "none",
      });
      wx.navigateTo({ url: "/pages/diary-form/index" });
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
