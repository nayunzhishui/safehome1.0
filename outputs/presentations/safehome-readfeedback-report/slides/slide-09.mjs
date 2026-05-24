import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide09(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "08 | 学生入口", "学生画像入口：考试焦虑支持性测评", "学生端入口明确说明边界：用于理解状态和获得建议，不用于贴标签。", "09");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["入口文案面向学生，降低测评压力","强调考试焦虑画像和阶段性建议","把学生端与家长端在同一站点分开","后续可独立进入安心家的学生测评路径"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "学生入口决定了系统不是单纯家长端工具。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_student_entry.png", 486, 216, 660, 372, { alt: "学生画像入口：考试焦虑支持性测评" });
  footer(slide);
  return slide;
}
