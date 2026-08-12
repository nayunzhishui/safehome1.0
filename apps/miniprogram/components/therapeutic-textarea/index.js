Component({
  options: { styleIsolation: "apply-shared" },
  properties: {
    value: { type: String, value: "" },
    placeholder: { type: String, value: "只写你愿意记录的部分，可以稍后修改。" },
    maxlength: { type: Number, value: 4000 },
    disabled: { type: Boolean, value: false },
    error: { type: Boolean, value: false },
    ariaLabel: { type: String, value: "记录内容" },
  },
  methods: {
    handleInput(event) {
      this.triggerEvent("input", { value: event.detail.value });
    },
  },
});
