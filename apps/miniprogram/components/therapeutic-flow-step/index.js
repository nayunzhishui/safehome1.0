Component({
  options: { styleIsolation: "apply-shared" },
  data: {
    reminderOptions: ["不提醒", "仅站内提醒", "微信订阅提醒"],
  },
  properties: {
    stepNumber: { type: Number, value: 1 },
    stepTotal: { type: Number, value: 8 },
    eyebrow: { type: String, value: "协作式阶段性评估" },
    title: { type: String, value: "" },
    description: { type: String, value: "" },
    prompt: { type: String, value: "" },
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
