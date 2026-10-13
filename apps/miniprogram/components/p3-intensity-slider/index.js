// IntensitySlider（Figma 646:973）：米白细轨 + 从 intensity/1 渐变到当前强度色的液柱 + 青瓷描边圆点。
// 透明的原生 slider 盖在轨道上，负责拖动、步进与读屏；视觉全部由 view 绘制。
Component({
  options: { styleIsolation: "apply-shared" },
  properties: {
    value: { type: Number, value: 0 },
    min: { type: Number, value: 0 },
    max: { type: Number, value: 10 },
    ariaLabel: { type: String, value: "" },
  },
  data: { percent: 0, level: 0 },
  lifetimes: {
    attached() { this.refresh(); },
  },
  observers: {
    "value, min, max"() { this.refresh(); },
  },
  methods: {
    refresh() {
      const { min, max } = this.data;
      const span = Math.max(1, max - min);
      const value = Math.max(min, Math.min(max, Math.round(Number(this.data.value) || 0)));
      // 液柱颜色用 0–10 的强度色；1–10 量尺同样对应 intensity/1…10。
      const level = Math.max(0, Math.min(10, Math.round(value)));
      this.setData({ percent: ((value - min) / span) * 100, level });
    },
    onChanging(event) {
      this.triggerEvent("change", { value: Number(event.detail.value) });
    },
  },
});
