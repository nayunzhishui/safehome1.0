import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide17(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "16 | 整合治疗任务", "报告任务：标本同治、整合治疗取向", "每个画像只给一个首轮任务，避免学生被报告压垮。", "17");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["CBT：自动想法和证据检验","ACT：接纳不确定性与价值行动","焦点解决：例外经验和资源追踪","人本/动力学：非评判理解与关系线索"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "任务设计体现心理学整合，而不是单一技术。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_student_report_full.png", 486, 216, 660, 372, { alt: "报告任务：标本同治、整合治疗取向" });
  footer(slide);
  return slide;
}
