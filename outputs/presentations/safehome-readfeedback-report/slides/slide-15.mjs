import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide15(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "14 | 轮次变化", "轮次状态变化：从一次测评走向持续追踪", "复测后显示状态分数变化，帮助判断画像是否收束。", "15");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["保存第1/2/3轮反馈","记录任务完成和当前状态评分","趋势图体现小步干预后的变化","误差不降时建议调整路径或人工复核"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "轮次设计让评估成为过程，而不是一次性标签。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_student_report_followup.png", 486, 216, 660, 372, { alt: "轮次状态变化：从一次测评走向持续追踪" });
  footer(slide);
  return slide;
}
