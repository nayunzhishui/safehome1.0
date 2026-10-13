// Horizontal emotion thermometer (Figma 631:463), shared by the home card and the thermometer page.
// value 0 = nothing recorded today; 1–10 fills the mercury from intensity/1 to intensity/value.
// Every tick column is a tap target; taps emit "pick" with { value }.

function fraction(step) {
  return Math.round((step / 9) * 10000) / 10000;
}

const TICKS = Array.from({ length: 10 }, (_, index) => ({
  value: index + 1,
  position: `calc(80rpx + (100% - 108rpx) * ${fraction(index)})`,
}));

Component({
  properties: {
    value: { type: Number, value: 0 },
    interactive: { type: Boolean, value: true },
    ariaLabel: { type: String, value: "情绪温度计" },
  },
  data: { ticks: TICKS, mercuryWidth: "", markerLeft: "" },
  lifetimes: {
    attached() { this.refresh(); },
  },
  observers: {
    value() { this.refresh(); },
  },
  methods: {
    refresh() {
      const value = Math.max(0, Math.min(10, Math.round(Number(this.data.value) || 0)));
      if (!value) {
        this.setData({ mercuryWidth: "", markerLeft: "" });
        return;
      }
      this.setData({
        mercuryWidth: `calc(32rpx + (100% - 108rpx) * ${fraction(value - 1)})`,
        markerLeft: `calc(58rpx + (100% - 108rpx) * ${fraction(value - 1)})`,
      });
    },
    pick(event) {
      if (!this.data.interactive) return;
      this.triggerEvent("pick", { value: Number(event.currentTarget.dataset.value) });
    },
  },
});
