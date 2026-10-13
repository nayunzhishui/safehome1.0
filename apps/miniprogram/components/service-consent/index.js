Component({
  options: { styleIsolation: "apply-shared" },
  properties: { notice: { type: Object, value: null } },
  data: { checked: false },
  observers: { notice() { this.setData({ checked: false }); } },
  methods: {
    stop() {},
    check(event) { this.setData({ checked: event.detail.value.includes("agree") }); },
    toggle() { this.setData({ checked: !this.data.checked }); },
    agree() { if (this.data.checked) this.triggerEvent("decision", { agreed: true }); },
    refuse() { this.triggerEvent("decision", { agreed: false }); },
    privacy() { wx.navigateTo({ url: "/pages/settings-detail/index?type=privacy" }); },
  },
});
