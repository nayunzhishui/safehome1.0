Component({
  options: { styleIsolation: "apply-shared" },
  properties: { item: { type: Object, value: {} } },
  methods: {
    handleTap() {
      this.triggerEvent("open", { id: this.properties.item.id, enabled: this.properties.item.is_enabled_for_user });
    },
  },
});
