// Keep the source timestamp unchanged; format only its visible label.
// 今年的消息省去年份（“10月9日 20:15”，Figma 670:3086），往年的保留年份。
function formatTime(value) {
  const source = String(value || "");
  const matched = source.match(/^(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})/);
  if (!matched) return source;
  const sameYear = Number(matched[1]) === new Date().getFullYear();
  return `${sameYear ? "" : `${matched[1]}年`}${Number(matched[2])}月${Number(matched[3])}日 ${matched[4]}:${matched[5]}`;
}

Component({
  options: { styleIsolation: "apply-shared" },
  data: { displayTime: "" },
  properties: {
    message: {
      type: Object,
      value: {},
    },
    // 分组里最后一行不画分隔线（Figma 670:3124）。
    showDivider: { type: Boolean, value: true },
  },

  lifetimes: {
    attached() {
      this.setData({ displayTime: formatTime((this.data.message || {}).created_at) });
    },
  },

  observers: {
    "message.created_at"(value) {
      this.setData({ displayTime: formatTime(value) });
    },
  },

  methods: {
    handleTap() {
      this.triggerEvent("open", { id: this.properties.message.id });
    },
  },
});
