Component({
  properties: {
    message: {
      type: Object,
      value: {},
    },
  },

  methods: {
    handleTap() {
      this.triggerEvent("open", { id: this.properties.message.id });
    },
  },
});
