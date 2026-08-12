Component({
  options: { styleIsolation: "apply-shared" },
  properties: {
    leftKey: { type: String, value: "" },
    leftIcon: { type: String, value: "" },
    leftTitle: { type: String, value: "" },
    leftSubtitle: { type: String, value: "" },
    rightKey: { type: String, value: "" },
    rightIcon: { type: String, value: "" },
    rightTitle: { type: String, value: "" },
    rightSubtitle: { type: String, value: "" },
  },
  methods: {
    forwardAction(event) {
      this.triggerEvent("action", event.detail);
    },
  },
});
