import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide12(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "11 | 学生报告总览", "学生报告顶部：先回答“我属于哪一类”", "报告顶部呈现画像名称、置信度、关键分数和初步解释。", "12");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["显示画像名称和一句话解释","展示画像置信度和关键维度","给出不是诊断的边界说明","为下方图表和任务做铺垫"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "报告第一屏要让学生快速理解结果。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_student_report_top.png", 486, 216, 660, 372, { alt: "学生报告顶部：先回答“我属于哪一类”" });
  footer(slide);
  return slide;
}
