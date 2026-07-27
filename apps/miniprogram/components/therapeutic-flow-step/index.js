Component({
  options: { styleIsolation: "apply-shared" },
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
      this.triggerEvent("optionchange", { value: event.currentTarget.dataset.value });
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
