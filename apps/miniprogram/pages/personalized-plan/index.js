const { createSafeHomeApi } = require("../../services/api");

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
    savingAssignment: false,
    requestingReminder: false,
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
      .then((notification) => this.setData({
        notification: {
          ...notification,
          preference: notification.preference || { consent_status: "unknown" },
        },
      }))
      .catch(() => this.setData({ "notification.available": false }));
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
          assignment,
          planItems: (
            plan.assignment
              ? (plan.assignment.is_due_today ? plan.today_plan_items || [] : [])
              : plan.plan_items || []
          ).map((item) => ({
            ...item,
            sourceLabel: item.source_type === "profile_cluster" ? "画像推荐" : "测评推荐",
            cardIdsText: Array.isArray(item.card_ids) ? item.card_ids.join(",") : "",
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
    this.setData({ "assignment.start_date": event.detail.value });
  },

  onGoalInput(event) {
    this.setData({ "assignment.goal_text": event.detail.value });
  },

  saveAssignment() {
    if (this.data.savingAssignment) return;
    this.setData({ savingAssignment: true });
    api
      .saveTrainingPlanAssignment(this.data.assignment)
      .then((assignment) => {
        this.setData({ assignment, savingAssignment: false });
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
            this.setData({ "notification.preference": preference, requestingReminder: false });
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
