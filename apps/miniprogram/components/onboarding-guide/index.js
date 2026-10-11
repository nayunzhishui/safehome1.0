// Home page spotlight tour (ported from codex/cloudrun-login-onboarding 09cf5a0a).
// It only explains where entries are; it never records consent or submits anything.
Component({
  properties: { visible: Boolean, step: Object, rect: Object, position: Object, index: Number, total: Number },
  methods: {
    stop() {},
    next() { this.triggerEvent("next"); },
    previous() { this.triggerEvent("previous"); },
    skip() { this.triggerEvent("skip"); },
  },
});
