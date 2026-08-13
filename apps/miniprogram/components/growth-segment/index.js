Component({
  options: { styleIsolation: "apply-shared" },
  properties: {
    label: { type: String, value: "" },
    count: { type: Number, value: 0 },
    active: { type: Boolean, value: false },
    segmentKey: { type: String, value: "" },
  },
  methods: { handleTap() { this.triggerEvent("change", { key: this.properties.segmentKey }); } },
});
