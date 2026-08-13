Component({
  properties: {
    title: {
      type: String,
      value: "",
    },
    subtitle: {
      type: String,
      value: "",
    },
    iconText: {
      type: String,
      value: "记",
    },
    iconType: {
      type: String,
      value: "",
    },
    accentColor: {
      type: String,
      value: "#4CAF7D",
    },
    accentBg: {
      type: String,
      value: "#EEF8E9",
    },
    actionKey: {
      type: String,
      value: "",
    },
  },
  methods: {
    handleTap() {
      this.triggerEvent("tapcard", { key: this.properties.actionKey });
    },
  },
});
