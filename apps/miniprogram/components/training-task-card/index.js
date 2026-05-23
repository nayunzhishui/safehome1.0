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
    tag: {
      type: String,
      value: "",
    },
  },
  methods: {
    handleTap() {
      this.triggerEvent("tapcard");
    },
  },
});
