const OPTIONS = [
  { value: "matches", label: "符合" },
  { value: "partly_matches", label: "部分符合" },
  { value: "does_not_match", label: "不符合" },
  { value: "uncomfortable", label: "让我不舒服" },
];

Component({
  options: { styleIsolation: "apply-shared" },
  properties: {
    value: { type: String, value: "" },
    disabled: { type: Boolean, value: false },
    prompt: { type: String, value: "这段内容与你的实际情况相符吗？" },
    compact: { type: Boolean, value: false },
  },
  data: { options: OPTIONS },
  methods: {
    select(event) {
      if (this.data.disabled) return;
      this.triggerEvent("select", { evaluation: event.currentTarget.dataset.value });
    },
  },
});
