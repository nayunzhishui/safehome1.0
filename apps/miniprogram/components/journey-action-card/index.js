const STATE_TONES = {
  ready: "success",
  completed: "success",
  paused: "warning",
  not_due: "neutral",
};

Component({
  options: { styleIsolation: "apply-shared" },
  properties: {
    // default：首页“今天的一小步”；stage：关系探索“当前步骤”（大序号圆、宋体标题）。
    variant: { type: String, value: "default" },
    loading: { type: Boolean, value: false },
    errorMessage: { type: String, value: "" },
    eyebrow: { type: String, value: "今天的一小步" },
    marker: { type: Number, value: 1 },
    showMarker: { type: Boolean, value: false },
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
  data: { statusTone: "neutral" },
  observers: {
    state(value) {
      this.setData({ statusTone: STATE_TONES[value] || "success" });
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
