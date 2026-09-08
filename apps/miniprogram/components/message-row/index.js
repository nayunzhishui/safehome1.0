Component({
  data: { displayTime: "" },
  properties: {
    message: {
      type: Object,
      value: {},
    },
  },

  observers: {
    "message.created_at"(value) {
      // Keep the source timestamp unchanged; format only its visible label.
      const source = String(value || "");
      const matched = source.match(/^(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})/);
      this.setData({
        displayTime: matched
          ? `${matched[1]}年${Number(matched[2])}月${Number(matched[3])}日 ${matched[4]}:${matched[5]}`
          : source,
      });
    },
  },

  methods: {
    handleTap() {
      this.triggerEvent("open", { id: this.properties.message.id });
    },
  },
});
