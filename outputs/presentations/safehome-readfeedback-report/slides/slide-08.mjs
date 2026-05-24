import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide08(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "07 | 双量表报告", "双量表报告页：非诊断反馈与研究说明", "报告将量表得分转化为可理解的解释和支持性提示。", "08");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["展示维度得分与解释","强调非诊断、非医疗判断","保留研究反馈和后续使用说明","可作为安心家家长端测评模块来源"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "报告页是从“得分”走向“反馈”的关键。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_parent_report.png", 486, 216, 660, 372, { alt: "双量表报告页：非诊断反馈与研究说明" });
  footer(slide);
  return slide;
}
