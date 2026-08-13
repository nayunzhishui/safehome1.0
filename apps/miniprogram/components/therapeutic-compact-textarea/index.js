Component({
  options: { styleIsolation: "apply-shared" },
  properties: {
    value: { type: String, value: "" },
    placeholder: { type: String, value: "" },
    maxlength: { type: Number, value: 500 },
    field: { type: String, value: "" },
    ariaLabel: { type: String, value: "记录内容" },
  },
  methods: {
    handleInput(event) {
      this.triggerEvent("input", { field: this.properties.field, value: event.detail.value });
    },
  },
});
