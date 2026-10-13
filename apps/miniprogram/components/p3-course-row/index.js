// CourseRow（Figma 639:441）：课程行，标题、适用场景、主题·小节·时长，右侧淡箭头，行间细线。
Component({
  options: { styleIsolation: "apply-shared" },
  properties: {
    title: { type: String, value: "" },
    scene: { type: String, value: "" },
    meta: { type: String, value: "" },
    showDivider: { type: Boolean, value: true },
  },
});
