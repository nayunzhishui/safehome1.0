Component({
  options: { styleIsolation: "apply-shared" },
  properties: {
    icon: { type: String, value: "" },
    title: { type: String, value: "" },
    subtitle: { type: String, value: "" },
    actionLabel: { type: String, value: "" },
    actionKey: { type: String, value: "" },
    accent: { type: Boolean, value: false },
    compact: { type: Boolean, value: false },
    expanded: { type: Boolean, value: false },
    wrapTitle: { type: Boolean, value: false },
    showArrow: { type: Boolean, value: true },
  },
  methods: {
    handleTap() {
      this.triggerEvent("action", { key: this.properties.actionKey });
    },
  },
});
