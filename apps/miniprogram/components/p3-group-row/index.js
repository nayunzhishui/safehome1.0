// GroupRow（Figma 639:418）：图标底圆 + 标题 + 可选说明 + 箭头；分隔线从文字起始处开始。
// tone="warm" 用于“紧急时先找现实帮助”暖色分组：纸白底圆、暖棕文字与细线。
Component({
  options: { styleIsolation: "apply-shared" },
  properties: {
    icon: { type: String, value: "" },
    iconTone: { type: String, value: "primary" },
    title: { type: String, value: "" },
    subtitle: { type: String, value: "" },
    tone: { type: String, value: "default" },
    showDivider: { type: Boolean, value: true },
  },
});
