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
    moreText: {
      type: String,
      value: "",
    },
  },
  methods: {
    handleMore() {
      this.triggerEvent("more");
    },
  },
});
