import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide18(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "17 | 沙盘式表达", "沙盘式表达任务：把考试压力转成可讨论材料", "学生用象征物、空间位置和文字反思表达内在场景。", "18");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["象征物：山、门、桥、时钟、书本、眼睛、家等","沙盘板：拖放位置和空间关系","反思问题：学生用自己的语言解释场景","摘要指标只作为访谈线索，不自动诊断"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "这是0版网页最有研究特色的表达任务。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_student_report_sandplay.png", 486, 216, 660, 372, { alt: "沙盘式表达任务：把考试压力转成可讨论材料" });
  footer(slide);
  return slide;
}
