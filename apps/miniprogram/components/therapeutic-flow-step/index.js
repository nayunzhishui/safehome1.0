// 8 步竹节进度（Figma 656:2010）：已完成半透明青瓷、当前实心、未到淡色。
function progressJoints(stepNumber, stepTotal) {
  const total = Math.max(1, Number(stepTotal) || 1);
  const current = Math.max(1, Math.min(total, Number(stepNumber) || 1));
  return Array.from({ length: total }, (_item, index) => (index + 1 < current ? "done" : index + 1 === current ? "current" : "upcoming"));
}

function dateText(value) {
  const matched = String(value || "").match(/^(\d{4})-(\d{2})-(\d{2})/);
  return matched ? `${Number(matched[2])}月${Number(matched[3])}日` : "";
}

Component({
  options: { styleIsolation: "apply-shared" },
  data: {
    reminderOptions: ["不提醒", "仅站内提醒", "微信订阅提醒"],
    joints: progressJoints(1, 8),
    plannedDateText: "",
  },
  observers: {
    "stepNumber, stepTotal"(stepNumber, stepTotal) {
      this.setData({ joints: progressJoints(stepNumber, stepTotal) });
    },
    "actionPlan.plannedDate"(plannedDate) {
      this.setData({ plannedDateText: dateText(plannedDate) });
    },
  },
  properties: {
    ui2: { type: Boolean, value: false },
    stepNumber: { type: Number, value: 1 },
    stepTotal: { type: Number, value: 8 },
    eyebrow: { type: String, value: "协作式阶段性评估" },
    title: { type: String, value: "" },
    description: { type: String, value: "" },
    prompt: { type: String, value: "" },
    placeholder: { type: String, value: "只写你愿意记录的部分，可以稍后修改。" },
    mode: { type: String, value: "text" },
    value: { type: String, value: "" },
    selected: { type: String, value: "" },
    options: { type: Array, value: [] },
    originalText: { type: String, value: "" },
    systemText: { type: String, value: "" },
    feedbackTitle: { type: String, value: "" },
    feedbackContent: { type: String, value: "" },
    feedbackLayerLabel: { type: String, value: "" },
    actionPlan: { type: Object, value: {} },
    nextLabel: { type: String, value: "保存并继续" },
    saveStatus: { type: String, value: "尚未填写" },
    loading: { type: Boolean, value: false },
    saving: { type: Boolean, value: false },
    offline: { type: Boolean, value: false },
    stateKind: { type: String, value: "" },
    stateTitle: { type: String, value: "" },
    stateDescription: { type: String, value: "" },
    canContinue: { type: Boolean, value: true },
    notice: { type: String, value: "" },
  },
  methods: {
    handleInput(event) {
      this.triggerEvent("valuechange", { value: event.detail.value });
    },
    handleOption(event) {
      this.triggerEvent("optionchange", { value: event.detail.value || event.currentTarget.dataset.value });
    },
    handleActionInput(event) {
      this.triggerEvent("actionchange", {
        field: event.detail.field || event.currentTarget.dataset.field,
        value: event.detail.value,
      });
    },
    handleReminderMode(event) {
      const modes = ["none", "in_app", "wechat_subscription"];
      this.triggerEvent("actionchange", {
        field: "reminderMode",
        value: modes[Number(event.detail.value)] || "none",
      });
    },
    handleActionConfirmation() {
      this.triggerEvent("actionchange", {
        field: "confirmed",
        value: !this.data.actionPlan.confirmed,
      });
    },
    handleContinue() {
      this.triggerEvent("continue");
    },
    handleRetry() {
      this.triggerEvent("retry");
    },
    handleBack() {
      this.triggerEvent("back");
    },
  },
});
