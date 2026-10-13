const { createSafeHomeApi } = require("../../services/api");
const { captureAuthSession, isCurrentAuthSession, isLoggedIn } = require("../../utils/authGuard");
const { buildGreeting } = require("../../utils/greeting");
const { navMetrics } = require("../../utils/nav-metrics");

const api = createSafeHomeApi();
const PRIVACY_NOTICE_VERSION = "2026.10-privacy-notice-v1";
const PRIVACY_NOTICE_KEY = "safehome_privacy_notice_seen";
// The spotlight tour (components/onboarding-guide, ported from the
// codex/cloudrun-login-onboarding branch) runs once after the privacy reminder is
// acknowledged; “重看使用教程” replays it, and the longer three-step guide stays
// under “如何开始”. It only points at entries and never records consent.
const HOME_TOUR_VERSION = "2026.10-home-tour-v1";
const HOME_TOUR_KEY = "safehome_home_tour_seen";
const HOME_TOUR_STEPS = [
  { selector: "#guide-today", title: "每天先看这里", text: "“今天的一小步”会根据你的记录和练习节奏，提示今天可以做的一件事。还没登录时，它会先带你登录。" },
  { selector: "#guide-capture", title: "两种开始方式，选一个就行", text: "想先了解自己，点“测一测”，大约 5 分钟；想处理刚发生的事，点“写日记”记一件小事，大约 3 分钟，只有“发生了什么”必须写。没时间写的话，在上方“情绪温度计”点一个刻度记下此刻的感受也可以。第一次提交前会先说明数据用途，请你单独确认。" },
  { selector: "#guide-start", title: "想了解完整用法", text: "页面底部的“三步开始”有完整说明：记一件小事、看一条支持性反馈、做一个小练习。" },
  { tabBarIndex: 1, title: "选一个小练习", text: "训练卡和三个分节书写的练习项目都在底部的“训练”里。按自己的节奏选一个，做完记下感受。" },
  { selector: "#guide-support", title: "需要时，找人帮忙", text: "这里可以提交人工支持请求。它不是实时聊天，也不是紧急救助；遇到紧急情况，请先联系身边可信任的人或当地紧急服务。" },
  { selector: "#guide-replay", title: "随时可以重看", text: "点“重看使用教程”可以再走一遍。教程只介绍入口，不会替你填写、提交或同意任何用途。" },
];
const TAB_COUNT = 4;
// 常用入口与页尾链接是页面配置（Figma 643:553、643:607），模板只循环渲染。
const QUICK_ACTIONS = [
  { key: "diary", icon: "diary", badge: "warm", title: "写日记", subtitle: "得到支持性反馈" },
  { key: "assessment", icon: "check", badge: "soft", title: "测一测", subtitle: "了解此刻状态" },
  { key: "weekly", icon: "calendar", badge: "soft", title: "本周复盘", subtitle: "看看这一周" },
];

function heroLayout() {
  const nav = navMetrics();
  return {
    offset: Math.max(0, Math.round(nav.offset)),
    greetingTop: Math.round(nav.navBottom + 12),
    bellTop: Math.round(nav.capsuleCenter - 18),
  };
}

function thermometerCountText(loginRequired, ready, count) {
  if (loginRequired) return "登录后记录";
  if (!ready) return "记录次数待更新";
  return `今天已记 ${count} 次`;
}
const PROTECTION_URL = "/pages/settings-detail/index?type=protection";

function trackJourneyEvent(eventName, journey, status, extra = {}) {
  if (!journey || journey.type === "login_required") return;
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
  if (String(stored.narration || "").trim() || (Array.isArray(stored.strokes) && stored.strokes.length)) return true;
  if (Object.values(stored.answers || {}).some(value => String(value || "").trim())) return true;
  return Object.values(stored.reflectionAnswers || {}).some((value) => String(value || "").trim());
}

function findLocalDraftAction() {
  const ownerId = String((wx.getStorageSync("auth_user") || {}).id || "");
  if (!ownerId) return null;
  const ownerSuffix = `:user:${encodeURIComponent(ownerId)}`;
  let keys = [];
  try {
    const storageInfo = wx.getStorageInfoSync();
    keys = Array.isArray(storageInfo.keys) ? storageInfo.keys.filter(key => key.endsWith(ownerSuffix)) : [];
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
    ...buildGreeting(new Date()),
    hero: { offset: 0, greetingTop: 100, bellTop: 48 },
    quickActions: QUICK_ACTIONS,
    homeLoginRequired: false,
    privacyNoticeVisible: true,
    tourVisible: false,
    tourIndex: 0,
    tourTotal: 0,
    tourRect: null,
    tourStep: {},
    tourPosition: { top: 80 },
    todayRecordCount: 0,
    todayRecordCountReady: false,
    thermometerRecordCount: 0,
    thermometerRecordReady: false,
    thermometerLatest: 0,
    thermometerCountText: "记录次数待更新",
    unreadMessageCount: 0,
    homeOverviewError: "",
    latestRecord: null,
    latestRecordReady: false,
    latestRecordError: "",
    todayJourney: null,
    todayJourneyLoading: true,
    todayJourneyError: "",
  },

  onLoad() {
    this.setData({ hero: heroLayout() });
  },

  onShow() {
    this._homeHidden = false;
    this.setData(buildGreeting(new Date()));
    if (!this._homeSession || !isCurrentAuthSession(this._homeSession)) {
      this.setData({
        todayRecordCount: 0, todayRecordCountReady: false,
        thermometerRecordCount: 0, thermometerRecordReady: false, thermometerLatest: 0,
        thermometerCountText: thermometerCountText(false, false, 0), unreadMessageCount: 0,
        homeOverviewError: "", latestRecord: null, latestRecordReady: false, latestRecordError: "",
        todayJourney: null, todayJourneyLoading: false, todayJourneyError: "",
      });
    }
    this._homeSession = captureAuthSession();
    const privacyNoticeVisible = wx.getStorageSync(PRIVACY_NOTICE_KEY) !== PRIVACY_NOTICE_VERSION;
    this.setData({ privacyNoticeVisible });
    this.refreshHomeData();
    if (!privacyNoticeVisible && !this.data.tourVisible && wx.getStorageSync(HOME_TOUR_KEY) !== HOME_TOUR_VERSION) this.startGuide();
  },

  onHide() {
    this._homeHidden = true;
    // Leaving mid-tour closes it without marking it seen, so it resumes next time.
    if (this.data.tourVisible) { this.setData({ tourVisible: false }); if (wx.showTabBar) wx.showTabBar({ animation: false }); }
  },
  onUnload() { this._homeDisposed = true; },

  openPrivacyNotice() { wx.navigateTo({ url: "/pages/settings-detail/index?type=privacy" }); },

  acknowledgePrivacyNotice() {
    // Reading this reminder is not agreement to any data purpose.
    wx.setStorageSync(PRIVACY_NOTICE_KEY, PRIVACY_NOTICE_VERSION);
    this.setData({ privacyNoticeVisible: false });
    if (wx.getStorageSync(HOME_TOUR_KEY) !== HOME_TOUR_VERSION) this.startGuide();
  },

  startGuide() {
    this.setData({ tourVisible: true });
    this.positionGuide(0);
  },

  positionGuide(index) {
    const step = HOME_TOUR_STEPS[index];
    if (!step) return;
    this.setData({ tourStep: step, tourIndex: index, tourTotal: HOME_TOUR_STEPS.length, tourRect: null, tourPosition: { top: 80 } });
    const current = () => !this._homeHidden && this.data.tourVisible && this.data.tourIndex === index;
    if (step.tabBarIndex !== undefined) {
      // 训练入口在原生底部标签栏：这一步把标签栏露出来，提示框贴底并指向对应标签。
      if (wx.showTabBar) wx.showTabBar({ animation: false });
      const info = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync();
      const width = info.windowWidth;
      this.setData({
        tourPosition: {
          top: Math.max(16, info.windowHeight - 330),
          arrow: "down",
          arrowLeft: Math.round((width / TAB_COUNT) * (step.tabBarIndex + 0.5) - 24),
        },
      });
      return;
    }
    if (wx.hideTabBar) wx.hideTabBar({ animation: false });
    const measure = () => {
      if (!current() || !wx.createSelectorQuery) return;
      wx.createSelectorQuery().select(step.selector).boundingClientRect((rect) => {
        if (!current()) return;
        const info = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync();
        const height = info.windowHeight;
        const width = info.windowWidth;
        const valid = rect && rect.height > 0 && rect.top >= 0 && rect.bottom <= height;
        const below = valid && rect.bottom + 310 < height;
        const above = valid && rect.top > 310;
        const top = below ? rect.bottom + 18 : above ? rect.top - 300 : Math.max(16, (height - 300) / 2);
        const arrowLeft = valid ? Math.max(20, Math.min(width - 68, rect.left + rect.width / 2 - 24)) : 20;
        this.setData({ tourRect: valid ? rect : null, tourPosition: { top, arrow: below ? "up" : above ? "down" : "", arrowLeft } });
      }).exec();
    };
    if (wx.pageScrollTo) wx.pageScrollTo({ selector: step.selector, offsetTop: -90, duration: 0, complete: measure });
    else measure();
  },

  nextGuide() {
    if (this.data.tourIndex + 1 >= HOME_TOUR_STEPS.length) this.endGuide();
    else this.positionGuide(this.data.tourIndex + 1);
  },

  previousGuide() {
    if (this.data.tourIndex > 0) this.positionGuide(this.data.tourIndex - 1);
  },

  endGuide() {
    wx.setStorageSync(HOME_TOUR_KEY, HOME_TOUR_VERSION);
    this.setData({ tourVisible: false });
    if (wx.showTabBar) wx.showTabBar({ animation: false });
  },

  showLoginRequired() {
    this._overviewRequestId = (this._overviewRequestId || 0) + 1;
    this._journeyRequestId = (this._journeyRequestId || 0) + 1;
    this.setData({
      homeLoginRequired: true,
      todayRecordCount: 0, todayRecordCountReady: false,
      thermometerRecordCount: 0, thermometerRecordReady: false, thermometerLatest: 0,
      thermometerCountText: thermometerCountText(true, false, 0), unreadMessageCount: 0,
      homeOverviewError: "", latestRecord: null, latestRecordReady: true, latestRecordError: "",
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
      todayJourneyLoading: false, todayJourneyError: "",
    });
  },

  async refreshHomeData() {
    if (this._homeHidden || this._homeDisposed) return;
    if (!isLoggedIn()) { this.showLoginRequired(); return; }
    this.setData({ homeLoginRequired: false });
    const session = captureAuthSession();
    const requestId = this._overviewRequestId = (this._overviewRequestId || 0) + 1;
    const current = () => {
      if (this._homeHidden || this._homeDisposed || this._overviewRequestId !== requestId) return false;
      if (!isLoggedIn()) { this.showLoginRequired(); return false; }
      return isCurrentAuthSession(session);
    };
    this.loadTodayJourney();
    try {
      const todayKey = formatLocalDate(new Date());
      const [todayResult, latestResult, stats, thermometerDay] = await Promise.all([
        api.listDiaries({ date: todayKey, limit: 100 }).catch((error) => ({ __error: error })),
        api.listDiaries({ limit: 1 }).catch((error) => ({ items: [], __error: error })),
        api.getProfileStats().catch((error) => ({ __error: error })),
        api.getEmotionThermometerDay({ date: todayKey }).catch((error) => ({ __error: error })),
      ]);
      if (!current()) return;
      const todayError = todayResult && todayResult.__error ? todayResult.__error : null;
      const statsError = stats && stats.__error ? stats.__error : null;
      const thermometerError = thermometerDay && thermometerDay.__error ? thermometerDay.__error : null;
      const overviewErrors = [todayError, statsError, thermometerError].filter(Boolean);
      const todayItems = !todayError && todayResult && Array.isArray(todayResult.items) ? todayResult.items : [];
      const latestItems = latestResult && Array.isArray(latestResult.items) ? latestResult.items : [];
      const latestError = latestResult && latestResult.__error ? latestResult.__error : null;
      const thermometerRecordCount = !thermometerError && thermometerDay && thermometerDay.summary ? thermometerDay.summary.count || 0 : 0;
      const thermometerItems = !thermometerError && thermometerDay && Array.isArray(thermometerDay.items) ? thermometerDay.items : [];
      const lastReading = thermometerItems.length ? Number(thermometerItems[thermometerItems.length - 1].intensity_level) || 0 : 0;
      const latest = latestItems[0] || null;
      this.setData({
        todayRecordCount: todayItems.length,
        todayRecordCountReady: !todayError,
        thermometerRecordCount,
        thermometerRecordReady: !thermometerError,
        thermometerLatest: Math.max(0, Math.min(10, lastReading)),
        thermometerCountText: thermometerCountText(false, !thermometerError, thermometerRecordCount),
        unreadMessageCount: !statsError && stats ? stats.unread_message_count || 0 : 0,
        homeOverviewError: overviewErrors.length ? "首页摘要暂时没有加载成功，请重新加载。" : "",
        latestRecordReady: !latestError,
        latestRecordError: latestError ? latestError.message || "暂时无法读取最近记录。" : "",
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
      if (!current()) return;
      this.setData({
        todayRecordCount: 0,
        todayRecordCountReady: false,
        thermometerRecordCount: 0,
        thermometerRecordReady: false,
        thermometerLatest: 0,
        thermometerCountText: thermometerCountText(false, false, 0),
        homeOverviewError: "首页摘要暂时没有加载成功，请重新加载。",
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
  pickThermometer(event) {
    const value = Number(event.detail && event.detail.value);
    const intensity = value >= 1 && value <= 10 ? Math.round(value) : 0;
    // 只带入初始强度；温度计页确认“记录一次”后才保存。
    wx.navigateTo({ url: intensity ? `/pages/thermometer/index?intensity=${intensity}` : "/pages/thermometer/index" });
  },
  openLogin() { wx.navigateTo({ url: "/pages/login/index" }); },
  openEmergencyGuide() { wx.navigateTo({ url: "/pages/emergency-guide/index" }); },
  openWeeklyReport() { wx.navigateTo({ url: "/pages/weekly-report/index" }); },
  retryHomeData() { this.refreshHomeData(); },

  async loadTodayJourney() {
    if (this._homeHidden || this._homeDisposed) return;
    if (!isLoggedIn()) { this.showLoginRequired(); return; }
    this.setData({ homeLoginRequired: false });
    const session = captureAuthSession();
    const requestId = this._journeyRequestId = (this._journeyRequestId || 0) + 1;
    const current = () => {
      if (this._homeHidden || this._homeDisposed || this._journeyRequestId !== requestId) return false;
      if (!isLoggedIn()) { this.showLoginRequired(); return false; }
      return isCurrentAuthSession(session);
    };
    this.setData({ todayJourneyLoading: true, todayJourneyError: "" });
    try {
      const payload = await api.getTodayJourney();
      if (!current()) return;
      const protectedTypes = new Set(["read_feedback", "read_message", "training_paused", "training_stage_completed", "today_completed"]);
      const localDraft = findLocalDraftAction();
      const serverType = payload && payload.primary_action ? payload.primary_action.type : "";
      const selectedPayload = localDraft && !protectedTypes.has(serverType) ? localDraft : payload;
      const todayJourney = formatTodayJourney(selectedPayload);
      this.setData({ todayJourney, todayJourneyLoading: false, todayJourneyError: "" });
      trackJourneyEvent("journey_action_impression", todayJourney, "shown");
    } catch (error) {
      if (!current()) return;
      if (error && error.code === "auth_required") {
        this.showLoginRequired();
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
            boundary_notice: "年龄信息只用于未成年人保护，不用于诊断或能力判断。",
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
    if (key === "weekly") { this.openWeeklyReport(); return; }
    if (key === "assessment") wx.navigateTo({ url: "/pages/assessment/index" });
  },

});
