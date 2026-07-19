const STATE_TONES = {
  ready: "success",
  completed: "success",
  paused: "warning",
  not_due: "warning",
};

Component({
  options: { styleIsolation: "apply-shared" },
  properties: {
    loading: { type: Boolean, value: false },
    errorMessage: { type: String, value: "" },
    eyebrow: { type: String, value: "今天的一小步" },
    marker: { type: Number, value: 1 },
    regionAriaLabel: { type: String, value: "今天的一小步" },
    state: { type: String, value: "not_due" },
    stateLabel: { type: String, value: "按节奏进行" },
    title: { type: String, value: "继续今天的一小步" },
    description: { type: String, value: "" },
    metaText: { type: String, value: "" },
    buttonLabel: { type: String, value: "继续" },
    actionAriaLabel: { type: String, value: "继续今天的一小步" },
    boundaryNotice: { type: String, value: "" },
  },
  data: { statusTone: "warning" },
  observers: {
    state(value) {
      this.setData({ statusTone: STATE_TONES[value] || "info" });
    },
  },
  methods: {
    handleAction() {
      this.triggerEvent("action");
    },
    handleRetry() {
      this.triggerEvent("retry");
    },
  },
});
