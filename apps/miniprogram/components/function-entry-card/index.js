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
    accentColor: {
      type: String,
      value: "#4CAF7D",
    },
    accentBg: {
      type: String,
      value: "#EEF8E9",
    },
  },
  methods: {
    handleTap() {
      this.triggerEvent("tapcard");
    },
  },
});
