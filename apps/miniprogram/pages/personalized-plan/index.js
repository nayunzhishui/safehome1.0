const { createSafeHomeApi } = require("../../services/api");
const { firstSentence } = require("../../utils/card-text");

const api = createSafeHomeApi();

function todayKey() {
  const now = new Date();
  const month = `${now.getMonth() + 1}`.padStart(2, "0");
  const day = `${now.getDate()}`.padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

const PHASE_OPTIONS = [
  { value: "start", label: "起步" },
  { value: "practice", label: "练习" },
  { value: "consolidate", label: "巩固" },
];

const CADENCE_OPTIONS = [
  { value: "daily", label: "每日" },
  { value: "every_other_day", label: "隔日" },
  { value: "three_per_week", label: "每周 3 次" },
  { value: "weekly", label: "每周 1 次" },
];

// “2026年10月10日”（Figma 655:1676 开始日期）
function dateText(value) {
  const matched = String(value || "").match(/^(\d{4})-(\d{2})-(\d{2})/);
  return matched ? `${matched[1]}年${Number(matched[2])}月${Number(matched[3])}日` : "选择开始日期";
}

// 微信提醒状态（Figma 655:1751）：一行“状态 · 说明”，按钮随状态出现。
function reminderView(notification) {
  const status = notification && notification.preference ? notification.preference.consent_status : "unknown";
  if (!notification || !notification.available) {
    return { title: "暂未开放", text: "管理员完成微信模板审核后，这里可以开启。", showRequest: false, showSettings: false };
  }
  if (status === "accepted") {
    return { title: "已同意本次提醒", text: "到达下一次练习日期后发送；一次性授权使用后需要重新开启。", showRequest: false, showSettings: false };
  }
  if (status === "consumed") {
    return { title: "上次授权已使用", text: "如需下一次提醒，请再次主动开启。", showRequest: true, showSettings: false };
  }
  if (status === "banned") {
    return { title: "微信设置中已关闭", text: "如需恢复，请前往小程序设置调整订阅消息权限。", showRequest: false, showSettings: true };
  }
  return { title: "需要时再开启", text: "建议在保存好练习节奏后，开启一次微信提醒。", showRequest: true, showSettings: false };
}

function assignmentView(assignment) {
  return {
    assignment,
    startDateText: dateText(assignment.start_date),
    goalCount: String(assignment.goal_text || "").length,
  };
}

const STATUS_OPTIONS = [
  { value: "active", label: "进行中" },
  { value: "paused", label: "暂缓" },
  { value: "completed", label: "已完成" },
];

Page({
  data: {
    loading: true,
    plan: null,
    planItems: [],
    phaseOptions: PHASE_OPTIONS,
    cadenceOptions: CADENCE_OPTIONS,
    statusOptions: STATUS_OPTIONS,
    assignment: {
      phase: "start",
      cadence: "daily",
      status: "active",
      start_date: todayKey(),
      goal_text: "",
    },
    startDateText: dateText(todayKey()),
    goalCount: 0,
    savingAssignment: false,
    requestingReminder: false,
    reminder: reminderView(null),
    notification: {
      available: false,
      template_id: "",
      subscription_mode: "once",
      preference: { consent_status: "unknown" },
    },
    errorMessage: "",
    boundaryNotice: "个性化训练计划只用于阶段性练习建议，不构成诊断、筛查或治疗方案。",
  },

  onShow() {
    this.loadPlan();
    this.loadNotificationConfig();
  },

  loadNotificationConfig() {
    api
      .getNotificationConfig()
      .then((notification) => {
        const next = {
          ...notification,
          preference: notification.preference || { consent_status: "unknown" },
        };
        this.setData({ notification: next, reminder: reminderView(next) });
      })
      .catch(() => this.setData({ "notification.available": false, reminder: reminderView(null) }));
  },

  loadPlan() {
    this.setData({ loading: true, errorMessage: "" });
    api
      .getTrainingPlan()
      .then((plan) => {
        const assignment = plan.assignment || this.data.assignment;
        this.setData({
          loading: false,
          plan,
          ...assignmentView(assignment),
          planItems: (
            plan.assignment
              ? (plan.assignment.is_due_today ? plan.today_plan_items || [] : [])
              : plan.plan_items || []
          ).map((item) => ({
            ...item,
            sourceLabel: item.source_type === "profile_cluster" ? "画像推荐" : "测一测推荐",
            cardIdsText: Array.isArray(item.card_ids) ? item.card_ids.join(",") : "",
            cards: (item.cards || []).map((card) => ({
              ...card,
              sceneText: firstSentence(card.purpose),
              metaText: card.duration_minutes ? `${card.duration_minutes} 分钟` : "",
            })),
          })),
          boundaryNotice: plan.boundary_notice || this.data.boundaryNotice,
        });
      })
      .catch((error) => {
        this.setData({
          loading: false,
          errorMessage: error.message || "训练方案暂时没能读取，请检查网络后再试一次。",
        });
        wx.showToast({ title: error.message || "读取失败", icon: "none" });
      });
  },

  selectAssignmentOption(event) {
    const field = event.currentTarget.dataset.field;
    const value = event.currentTarget.dataset.value;
    if (!field || !value) return;
    this.setData({ [`assignment.${field}`]: value });
  },

  onStartDateChange(event) {
    this.setData({ "assignment.start_date": event.detail.value, startDateText: dateText(event.detail.value) });
  },

  onGoalInput(event) {
    this.setData({ "assignment.goal_text": event.detail.value, goalCount: String(event.detail.value || "").length });
  },

  saveAssignment() {
    if (this.data.savingAssignment) return;
    this.setData({ savingAssignment: true });
    api
      .saveTrainingPlanAssignment(this.data.assignment)
      .then((assignment) => {
        this.setData({ ...assignmentView(assignment), savingAssignment: false });
        wx.showToast({ title: "练习节奏已保存", icon: "success" });
        this.loadPlan();
        this.loadNotificationConfig();
      })
      .catch((error) => {
        this.setData({ savingAssignment: false });
        wx.showToast({ title: error.message || "保存失败", icon: "none" });
      });
  },

  requestTrainingReminder() {
    const notification = this.data.notification || {};
    if (!notification.available || !notification.template_id) {
      wx.showToast({ title: "微信提醒模板尚未配置", icon: "none" });
      return;
    }
    if (this.data.requestingReminder || typeof wx.requestSubscribeMessage !== "function") return;
    this.setData({ requestingReminder: true });
    wx.requestSubscribeMessage({
      tmplIds: [notification.template_id],
      success: (result) => {
        const decision = result[notification.template_id] || "reject";
        api
          .saveNotificationConsent({ template_id: notification.template_id, decision })
          .then(({ preference }) => {
            this.setData({
              "notification.preference": preference,
              reminder: reminderView({ ...this.data.notification, preference }),
              requestingReminder: false,
            });
            wx.showToast({
              title: decision === "accept" ? "已开启一次提醒" : "未开启提醒",
              icon: "none",
            });
          })
          .catch((error) => {
            this.setData({ requestingReminder: false });
            wx.showToast({ title: error.message || "授权状态保存失败", icon: "none" });
          });
      },
      fail: () => {
        this.setData({ requestingReminder: false });
        wx.showToast({ title: "未开启提醒，可稍后再试", icon: "none" });
      },
    });
  },

  openNotificationSettings() {
    if (typeof wx.openSetting === "function") wx.openSetting({ withSubscriptions: true });
  },

  openAssessment() {
    wx.navigateTo({ url: "/pages/assessment/index" });
  },

  openCard(event) {
    const ids = event.currentTarget.dataset.cardIds || "";
    if (!ids) {
      wx.showToast({ title: "暂无可打开的训练卡", icon: "none" });
      return;
    }
    wx.navigateTo({ url: `/pages/training-card/index?card_ids=${encodeURIComponent(ids)}` });
  },

  openSingleCard(event) {
    const cardId = (event.detail && event.detail.id) || event.currentTarget.dataset.cardId || "";
    if (!cardId) return;
    wx.navigateTo({ url: `/pages/training-card/index?card_ids=${encodeURIComponent(cardId)}` });
  },
});
