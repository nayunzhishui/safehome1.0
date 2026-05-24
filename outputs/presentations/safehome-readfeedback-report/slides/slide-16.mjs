import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide16(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "15 | 文本关键词", "文本关键词：从访谈/日记中观察压力词和资源词", "结构化文本用于辅助判断改善程度，不直接决定诊断。", "16");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["提取压力词、资源词和改善词","用于访谈线索和研究编码","和量表分数一起观察变化","不把自然语言处理作为硬性判定"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "文本分析服务于理解，不服务于贴标签。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_student_report_followup.png", 486, 216, 660, 372, { alt: "文本关键词：从访谈/日记中观察压力词和资源词" });
  footer(slide);
  return slide;
}
