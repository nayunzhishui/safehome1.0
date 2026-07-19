Component({
  options: { styleIsolation: "apply-shared" },
  properties: {
    kind: { type: String, value: "empty" },
    title: { type: String, value: "暂时没有内容" },
    description: { type: String, value: "" },
    actionLabel: { type: String, value: "" },
    actionAriaLabel: { type: String, value: "" },
  },
  methods: {
    handleAction() {
      this.triggerEvent("action");
    },
  },
});
