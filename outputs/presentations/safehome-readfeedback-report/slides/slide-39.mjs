import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide39(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "38 | 周度报告", "周度报告：阶段性总结高频场景和下周建议", "从单次反馈走向周期性陪伴。", "39");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["汇总高频场景和情绪","整理常见互动模式","汇总已完成训练卡","给出下周建议"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "周报是安心家的阶段性反馈形式。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/home_reports.png", 486, 216, 660, 372, { alt: "周度报告：阶段性总结高频场景和下周建议" });
  footer(slide);
  return slide;
}
