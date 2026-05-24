import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide10(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "09 | 学生测评", "学生画像测评页：多维度收集考试焦虑相关信息", "量表和结构化文本共同支持画像分类与后续访谈。", "10");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["考试焦虑：识别考试情境中的紧张和回避","IU：识别对不确定结果的放大反应","ERF：识别情绪调节灵活性","自我关怀：识别自我支持与自责倾向"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "学生画像依赖多维度，而不是单一焦虑总分。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_student_assessment.png", 486, 216, 660, 372, { alt: "学生画像测评页：多维度收集考试焦虑相关信息" });
  footer(slide);
  return slide;
}
