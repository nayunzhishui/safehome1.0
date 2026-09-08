Component({
  properties: { notice: { type: Object, value: null } },
  data: { checked: false },
  observers: { notice() { this.setData({ checked: false }); } },
  methods: {
    stop() {},
    check(event) { this.setData({ checked: event.detail.value.includes("agree") }); },
    agree() { if (this.data.checked) this.triggerEvent("decision", { agreed: true }); },
    refuse() { this.triggerEvent("decision", { agreed: false }); },
    privacy() { wx.navigateTo({ url: "/pages/settings-detail/index?type=privacy" }); },
  },
});
