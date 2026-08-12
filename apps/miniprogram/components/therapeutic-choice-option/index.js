Component({
  options: { styleIsolation: "apply-shared" },
  properties: {
    value: { type: String, value: "" },
    label: { type: String, value: "" },
    description: { type: String, value: "" },
    selected: { type: Boolean, value: false },
  },
  methods: {
    handleTap() {
      this.triggerEvent("change", { value: this.properties.value });
    },
  },
});
