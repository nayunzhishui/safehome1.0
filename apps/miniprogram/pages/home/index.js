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

function formatProgressSummary(summary) {
  if (!summary) {
    return null;
  }
  const statusTextMap = {
    insufficient: "记录还不够",
    fluctuating: "仍在观察",
    converging: "开始形成线索",
    stable: "较稳定",
    low_confidence: "暂不归纳",
  };
  const scenes = summary.diaries && Array.isArray(summary.diaries.frequent_scenes)
    ? summary.diaries.frequent_scenes
    : [];
  const emotions = summary.diaries && Array.isArray(summary.diaries.frequent_emotions)
    ? summary.diaries.frequent_emotions
    : [];
  const assessmentCount = summary.assessment ? summary.assessment.count || 0 : 0;
  const checkinCount = summary.checkins ? summary.checkins.completed_count || 0 : 0;
  const thermometerCount = summary.thermometer ? summary.thermometer.count || 0 : 0;
  return {
    status: summary.stability_status,
    statusText: statusTextMap[summary.stability_status] || "阶段复盘",
    summaryText: summary.summary_text || "记录还不够，先继续完成测评和练习。",
    periodText: `${summary.start_date || ""} 至 ${summary.end_date || ""}`,
    assessmentCount,
    checkinCount,
    thermometerCount,
    totalSignalCount: assessmentCount + checkinCount + thermometerCount,
    topScene: scenes.length ? scenes[0][0] : "待观察",
    topEmotion: emotions.length ? emotions[0][0] : "待观察",
    nextAction: summary.next_action || "先完成一次测一测或一张训练卡。",
    boundaryNotice: summary.boundary_notice || "阶段性反馈只用于整理近期记录和练习线索，不构成诊断。",
  };
}

Page({
  data: {
    todayRecordCount: 0,
    todayRecordCountReady: false,
    thermometerRecordCount: 0,
    thermometerRecordReady: false,
    unreadMessageCount: 0,
    latestRecord: null,
    progressSummary: null,
    progressSummaryReady: false,
    progressSummaryError: "",
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
        iconText: "记",
        accentColor: "#4E7C6B",
        accentBg: "#E7F0E2",
      },
      {
        key: "training",
        title: "训练中心",
        subtitle: "选择练习",
        iconText: "练",
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
    ],
  },

  onShow() {
    this.refreshHomeData();
  },

  async refreshHomeData() {
    try {
      const todayKey = formatLocalDate(new Date());
      const [result, stats, thermometerDay, progressSummary] = await Promise.all([
        api.listDiaries({ limit: 20 }).catch(() => ({ items: [] })),
        api.getProfileStats().catch(() => null),
        api.getEmotionThermometerDay({ date: todayKey }).catch(() => null),
        api.getProgressSummary({ range: "7d" }).catch((error) => ({ __error: error })),
      ]);
      const items = result && Array.isArray(result.items) ? result.items : [];
      const todayRecordCount = items.filter((item) => getDiaryDateKey(item) === todayKey).length;
      const thermometerRecordCount = thermometerDay && thermometerDay.summary ? thermometerDay.summary.count || 0 : 0;
      const latest = items[0] || null;
      const progressError = progressSummary && progressSummary.__error ? progressSummary.__error : null;
      this.setData({
        todayRecordCount,
        todayRecordCountReady: true,
        thermometerRecordCount,
        thermometerRecordReady: !!thermometerDay,
        unreadMessageCount: stats ? stats.unread_message_count || 0 : 0,
        progressSummary: progressError ? null : formatProgressSummary(progressSummary),
        progressSummaryReady: !progressError,
        progressSummaryError: progressError ? progressError.message || "登录后可以查看阶段性反馈。" : "",
        latestRecord: latest
          ? {
              mood: latest.parent_emotion || "一次记录",
              time: (latest.event_time || latest.created_at || "").slice(0, 16).replace("T", " "),
              trigger: latest.scene || latest.event_description || "亲子互动",
              status: "查看复盘",
            }
          : null,
      });
    } catch (error) {
      this.setData({
        todayRecordCount: 0,
        todayRecordCountReady: false,
        thermometerRecordCount: 0,
        thermometerRecordReady: false,
        progressSummary: null,
        progressSummaryReady: false,
        progressSummaryError: "联网后可以查看阶段性反馈。",
        latestRecord: null,
      });
    }
  },

  startGoalSetting() {
    wx.navigateTo({ url: "/pages/goal-setting/index" });
  },

  startDiary() {
    wx.navigateTo({ url: "/pages/diary-form/index" });
  },

  openThermometer() {
    wx.navigateTo({ url: "/pages/thermometer/index" });
  },

  openWeeklyReport() {
    wx.navigateTo({ url: "/pages/weekly-report/index" });
  },

  openAssessment() {
    wx.navigateTo({ url: "/pages/assessment/index" });
  },

  openMessages() {
    wx.navigateTo({ url: "/pages/messages/index" });
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
