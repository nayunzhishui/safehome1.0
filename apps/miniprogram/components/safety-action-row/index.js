Component({
  options: { styleIsolation: "apply-shared" },
  properties: {
    marker: { type: String, value: "" },
    text: { type: String, value: "" },
    // 一组里最后一行不画细线。
    showDivider: { type: Boolean, value: true },
  },
});
