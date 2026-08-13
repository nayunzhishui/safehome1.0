const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();
const PROTECTION_URL = "/pages/settings-detail/index?type=protection";

function trackJourneyEvent(eventName, journey, status, extra = {}) {
  if (!journey) return;
  const clientEventId = [eventName, journey.type || "unknown", journey.sourceId || "none", formatLocalDate(new Date())].join(":");
  api.trackProductEvent(eventName, {
    action: journey.type,
    stage: journey.type === "read_feedback" || journey.type === "read_message" ? "message" : "journey",
    status,
    source: "today_journey",
    ...extra,
  }, clientEventId).catch(() => {});
}

function formatLocalDate(date) {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
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

const JOURNEY_STATE_LABELS = {
  ready: "可以继续",
  paused: "已暂停",
  completed: "今日完成",
  not_due: "按节奏进行",
};

function formatTodayJourney(payload) {
  const action = payload && payload.primary_action ? payload.primary_action : null;
  if (!action) {
    return null;
  }
  const state = payload.state || "ready";
  return {
    state,
    stateLabel: JOURNEY_STATE_LABELS[state] || "可以继续",
    type: action.type || "continue",
    title: action.title || "继续今天的一小步",
    description: action.description || "选择一个现在容易完成的小动作。",
    buttonLabel: action.button_label || "继续",
    url: action.url || "",
    sourceType: action.source_type || "",
    sourceId: action.source_id || "",
    estimatedMinutes: action.estimated_minutes || null,
    metaText: action.estimated_minutes ? `约 ${action.estimated_minutes} 分钟` : "按自己的节奏",
    actionAriaLabel: `${action.button_label || "继续"}：${action.title || "今天的一小步"}`,
    boundaryNotice: payload.boundary_notice || "这只是一个可选建议，可按自己的节奏决定是否继续。",
  };
}

function hasDraftContent(stored) {
  if (!stored) return false;
  if (typeof stored === "string") return !!stored.trim();
  if (typeof stored !== "object") return false;
  if (String(stored.draftText || "").trim()) return true;
  return Object.values(stored.reflectionAnswers || {}).some((value) => String(value || "").trim());
}

function findLocalDraftAction() {
  let keys = [];
  try {
    const storageInfo = wx.getStorageInfoSync();
    keys = Array.isArray(storageInfo.keys) ? storageInfo.keys : [];
  } catch (error) {
    return null;
  }

  for (const key of keys) {
    if (!key.startsWith("relationship_task_draft:")) continue;
    const stored = wx.getStorageSync(key);
    if (!hasDraftContent(stored)) continue;
    const [, enrollmentId, type] = key.split(":");
    if (!enrollmentId || !type) continue;
    return {
      state: "ready",
      primary_action: {
        type: "continue_relationship_draft",
        title: "继续未完成的关系探索记录",
        description: "本机还有一份未提交的草稿，可以从上次停下的位置继续。",
        button_label: "继续填写",
        url: `/pages/relationship-task/index?enrollment_id=${encodeURIComponent(enrollmentId)}&type=${encodeURIComponent(type)}`,
        source_type: "local_draft",
        source_id: key,
        estimated_minutes: 3,
      },
      boundary_notice: "草稿只保存在本机，提交前不会发送其中的文字。",
    };
  }

  for (const key of keys) {
    if (!key.startsWith("safehome:programDraft:")) continue;
    const stored = wx.getStorageSync(key);
    if (!hasDraftContent(stored)) continue;
    const parts = key.split(":");
    const programId = parts[2];
    const sessionNo = parts[3];
    if (!programId || !sessionNo) continue;
    return {
      state: "ready",
      primary_action: {
        type: "continue_program_draft",
        title: "继续未完成的项目记录",
        description: "本机还有一份未提交的项目草稿，可以接着填写。",
        button_label: "继续填写",
        url: `/pages/program-detail/index?id=${encodeURIComponent(programId)}&session=${encodeURIComponent(sessionNo)}`,
        source_type: "local_draft",
        source_id: key,
        estimated_minutes: 3,
      },
      boundary_notice: "草稿只保存在本机，提交前不会发送其中的文字。",
    };
  }
  return null;
}

Page({
  data: {
    todayRecordCount: 0,
    todayRecordCountReady: false,
    thermometerRecordCount: 0,
    thermometerRecordReady: false,
    unreadMessageCount: 0,
    latestRecord: null,
    latestRecordReady: false,
    latestRecordError: "",
    progressSummary: null,
    progressSummaryReady: false,
    progressSummaryError: "",
    todayJourney: null,
    todayJourneyLoading: true,
    todayJourneyError: "",
    hotTopics: [
      { id: "exam-setback", title: "孩子考试失利后，家长第一句话怎么说？", tag: "考试压力", readTime: "4分钟阅读" },
      { id: "emotion-outburst", title: "孩子发脾气时，为什么讲道理没用？", tag: "情绪爆发", readTime: "4分钟阅读" },
      { id: "repair-after-conflict", title: "亲子冲突后，如何重新连接？", tag: "关系修复", readTime: "5分钟阅读" },
    ],
    startSteps: [
      { key: "diary", title: "第一步", text: "记录一次具体事件", detail: "写下发生了什么、我的情绪和当时回应。", actionText: "去记录" },
      { key: "feedback", title: "第二步", text: "查看支持性反馈", detail: "看看这次记录中的互动线索和可调整位置。", actionText: "了解反馈" },
      { key: "training", title: "第三步", text: "选择一个小练习并打卡", detail: "从推荐训练卡里选一个动作，记录一次尝试。", actionText: "去练习" },
    ],
    coreEntries: [
      { key: "assessment", title: "测一测", subtitle: "先了解自己", iconText: "测", accentColor: "#6A86B4", accentBg: "#E9F0FA" },
      { key: "diary", title: "情绪日记", subtitle: "记录一次", iconText: "记", accentColor: "#4E7C6B", accentBg: "#E7F0E2" },
      { key: "training", title: "训练中心", subtitle: "选择练习", iconText: "练", accentColor: "#4E7C6B", accentBg: "#EEF4E8" },
      { key: "feedback", title: "支持性反馈", subtitle: "记录后查看", iconText: "馈", accentColor: "#8069A8", accentBg: "#F1ECF8" },
    ],
  },

  onShow() {
    this.refreshHomeData();
  },

  async refreshHomeData() {
    this.loadTodayJourney();
    try {
      const todayKey = formatLocalDate(new Date());
      const [todayResult, latestResult, stats, thermometerDay, progressSummary] = await Promise.all([
        api.listDiaries({ date: todayKey, limit: 100 }).catch(() => ({ items: [] })),
        api.listDiaries({ limit: 1 }).catch((error) => ({ items: [], __error: error })),
        api.getProfileStats().catch(() => null),
        api.getEmotionThermometerDay({ date: todayKey }).catch(() => null),
        api.getProgressSummary({ range: "7d" }).catch((error) => ({ __error: error })),
      ]);
      const todayItems = todayResult && Array.isArray(todayResult.items) ? todayResult.items : [];
      const latestItems = latestResult && Array.isArray(latestResult.items) ? latestResult.items : [];
      const latestError = latestResult && latestResult.__error ? latestResult.__error : null;
      const thermometerRecordCount = thermometerDay && thermometerDay.summary ? thermometerDay.summary.count || 0 : 0;
      const latest = latestItems[0] || null;
      const progressError = progressSummary && progressSummary.__error ? progressSummary.__error : null;
      this.setData({
        todayRecordCount: todayItems.length,
        todayRecordCountReady: true,
        thermometerRecordCount,
        thermometerRecordReady: !!thermometerDay,
        unreadMessageCount: stats ? stats.unread_message_count || 0 : 0,
        latestRecordReady: !latestError,
        latestRecordError: latestError ? latestError.message || "暂时无法读取最近记录。" : "",
        progressSummary: progressError ? null : formatProgressSummary(progressSummary),
        progressSummaryReady: !progressError,
        progressSummaryError: progressError ? progressError.message || "登录后可以查看阶段性反馈。" : "",
        latestRecord: latest
          ? {
              mood: latest.parent_emotion || "一次记录",
              time: (latest.event_time || latest.created_at || "").slice(0, 16).replace("T", " "),
              trigger: latest.scene || latest.event_description || "亲子互动",
              status: "查看记录",
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
        latestRecordReady: false,
        latestRecordError: "联网后可以查看最近记录。",
      });
    }
  },

  startGoalSetting() { wx.navigateTo({ url: "/pages/goal-setting/index" }); },
  startDiary() { wx.navigateTo({ url: "/pages/diary-form/index" }); },
  openDiaryHistory() { wx.navigateTo({ url: "/pages/diary-history/index" }); },
  openThermometer() { wx.navigateTo({ url: "/pages/thermometer/index" }); },
  openWeeklyReport() { wx.navigateTo({ url: "/pages/weekly-report/index" }); },
  retryHomeData() { this.refreshHomeData(); },

  async loadTodayJourney() {
    this.setData({ todayJourneyLoading: true, todayJourneyError: "" });
    try {
      const payload = await api.getTodayJourney();
      const protectedTypes = new Set(["read_feedback", "read_message", "training_paused", "training_stage_completed", "today_completed"]);
      const localDraft = findLocalDraftAction();
      const serverType = payload && payload.primary_action ? payload.primary_action.type : "";
      const selectedPayload = localDraft && !protectedTypes.has(serverType) ? localDraft : payload;
      const todayJourney = formatTodayJourney(selectedPayload);
      this.setData({ todayJourney, todayJourneyLoading: false, todayJourneyError: "" });
      trackJourneyEvent("journey_action_impression", todayJourney, "shown");
    } catch (error) {
      if (error && error.code === "auth_required") {
        this.setData({
          todayJourney: formatTodayJourney({
            state: "not_due",
            primary_action: {
              type: "login_required",
              title: "登录后查看今天的一小步",
              description: "登录后才能根据你的记录和练习节奏整理下一步。",
              button_label: "去登录",
              url: "/pages/login/index",
              source_type: "auth",
            },
            boundary_notice: "登录前不会读取或上传本机草稿内容。",
          }),
          todayJourneyLoading: false,
          todayJourneyError: "",
        });
        return;
      }
      if (error && ["age_verification_required", "guardian_link_required", "guardian_consent_required", "child_assent_required", "blocked_withdrawn_or_refused"].includes(error.code)) {
        this.setData({
          todayJourney: formatTodayJourney({
            state: "ready",
            primary_action: {
              type: "participant_safeguard",
              title: "先完成参与者保护设置",
              description: "完成年龄确认和必要的监护人/本人确认后，再继续受保护功能。",
              button_label: "去完成",
              url: PROTECTION_URL,
              source_type: "minor_safeguards",
              estimated_minutes: 2,
            },
            boundary_notice: "年龄信息只用于保护门禁，不用于诊断或能力判断。",
          }),
          todayJourneyLoading: false,
          todayJourneyError: "",
        });
        return;
      }
      this.setData({ todayJourney: null, todayJourneyLoading: false, todayJourneyError: error && error.message ? error.message : "暂时没能整理今天的一小步。" });
    }
  },

  retryTodayJourney() {
    const journey = this.data.todayJourney;
    if (journey) trackJourneyEvent("journey_action_recovery", journey, "recovered", { recovery_mode: "manual_retry" });
    this.loadTodayJourney();
  },

  openTodayAction() {
    if (this.data.todayJourneyError) { this.retryTodayJourney(); return; }
    const url = this.data.todayJourney ? this.data.todayJourney.url : "";
    if (!url) return;
    trackJourneyEvent("journey_action_clicked", this.data.todayJourney, "clicked");
    if (url.startsWith("/pages/training/index")) { wx.switchTab({ url: "/pages/training/index" }); return; }
    wx.navigateTo({ url });
  },

  openAssessment() { wx.navigateTo({ url: "/pages/assessment/index" }); },
  openMessages() { wx.navigateTo({ url: "/pages/messages/index" }); },
  openIntegrationTest() { wx.navigateTo({ url: "/pages/integration-test/index" }); },
  openGettingStarted() { wx.navigateTo({ url: "/pages/getting-started/index" }); },

  openStartStep(event) {
    const key = (event.detail && event.detail.key) || event.currentTarget.dataset.key;
    if (key === "diary") { this.startDiary(); return; }
    if (key === "training") { wx.switchTab({ url: "/pages/training/index" }); return; }
    wx.navigateTo({ url: "/pages/getting-started/index" });
  },

  openCoreEntry(event) {
    const key = (event.detail && event.detail.key) || event.currentTarget.dataset.key;
    if (key === "diary") { this.startDiary(); return; }
    if (key === "training") { wx.switchTab({ url: "/pages/training/index" }); return; }
    if (key === "feedback") {
      wx.showToast({ title: "请先记录一次事件", icon: "none" });
      wx.navigateTo({ url: "/pages/diary-form/index" });
      return;
    }
    if (key === "supervision") { wx.navigateTo({ url: "/pages/supervision/index" }); return; }
    if (key === "assessment") wx.navigateTo({ url: "/pages/assessment/index" });
  },

  openRecommendedTraining() {
    wx.navigateTo({ url: `/pages/training-card/index?tags=${encodeURIComponent("high_demand_language,emotional_behavior")}` });
  },
  openHotTopics() { wx.navigateTo({ url: "/pages/hot-topics/index" }); },
  openHotTopic(event) {
    const id = event.currentTarget.dataset.id || "";
    wx.navigateTo({ url: `/pages/hot-topics/index?id=${encodeURIComponent(id)}` });
  },
  showComingSoon(title) { wx.showToast({ title, icon: "none" }); },
});
