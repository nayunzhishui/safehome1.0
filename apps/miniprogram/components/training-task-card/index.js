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
    stage: {
      type: String,
      value: "",
    },
    duration: {
      type: String,
      value: "",
    },
    scenario: {
      type: String,
      value: "",
    },
    reason: {
      type: String,
      value: "",
    },
    tag: {
      type: String,
      value: "",
    },
    itemId: {
      type: String,
      value: "",
    },
    actionable: {
      type: Boolean,
      value: true,
    },
  },
  methods: {
    handleTap() {
      if (!this.properties.actionable) return;
      this.triggerEvent("tapcard", { id: this.properties.itemId, title: this.properties.title });
    },
  },
});
