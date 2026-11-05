// B2 温度计刻度说明：滑块下面的三档文字，当前分数所在的那一档高亮。见 docs/11_商业化开发/开发框架.md 第 4 节。
// 默认文字每档都不到 18 个字，接口没回来或没登录时用它；登录后用 GET /api/thermometer-anchors 的结果。
const DEFAULT_BANDS = [
  { min: 1, max: 3, label: "有点不舒服，还能好好说话" },
  { min: 4, max: 7, label: "明显着急，声音开始变大" },
  { min: 8, max: 10, label: "快控制不住了" },
];

Component({
  properties: {
    bands: { type: Array, value: DEFAULT_BANDS },
    mine: { type: Array, value: [] }, // [{ level, text }]
    value: { type: Number, value: 0 },
    // 量表最低分：温度计页是 1，接口返回的 0 分“平静”只在 0–10 的滑块上显示。
    scaleMin: { type: Number, value: 1 },
    // “写下我自己的 8 分”要等 PUT /api/thermometer-anchors/me 做好（B2-后端）再打开。
    editable: { type: Boolean, value: false },
  },
  data: { shownBands: DEFAULT_BANDS, activeIndex: -1 },
  observers: {
    "bands, value, scaleMin"(bands, value, scaleMin) {
      const list = (Array.isArray(bands) ? bands : []).filter((band) => band.max >= scaleMin);
      this.setData({ shownBands: list, activeIndex: list.findIndex((band) => value >= band.min && value <= band.max) });
    },
  },
  methods: {
    onEditMine() {
      // TODO(B2-前端): 打开“写下我自己的 8 分”小表单，保存时调用 PUT /api/thermometer-anchors/me
      this.triggerEvent("editmine");
    },
  },
});
