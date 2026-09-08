Component({
  properties: { welcome: Boolean, visible: Boolean, step: Object, rect: Object, position: Object, index: Number, total: Number },
  data: { checked: false, privacyError: "" },
  observers: { welcome(value) { if (value) this.setData({ checked: false, privacyError: "" }); } },
  methods: {
    stop() {},
    check(event) { this.setData({ checked: event.detail.value.includes("agree") }); },
    privacy() {
      if (!wx.openPrivacyContract) { this.setData({ privacyError: "当前微信版本不支持隐私指引，请更新微信后重试。" }); return; }
      wx.openPrivacyContract({ fail: () => this.setData({ privacyError: "隐私指引暂时打不开，请稍后重试。" }) });
    },
    policy() { wx.navigateTo({ url: "/pages/settings-detail/index?type=privacy" }); },
    agree() { if (this.data.checked) this.triggerEvent("agree"); },
    decline() { this.triggerEvent("decline"); },
    next() { this.triggerEvent("next"); },
    previous() { this.triggerEvent("previous"); },
    skip() { this.triggerEvent("skip"); },
  },
});
