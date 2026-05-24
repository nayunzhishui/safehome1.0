import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide13(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "12 | 画像卡片", "画像卡片：把机器学习分类转成心理学语言", "系统不只显示组别编号，而是解释画像含义和主要依据。", "13");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["画像名称避免病理化","置信度体现模型判断的不确定性","维度分数帮助学生理解原因","最近两类距离可用于人工复核"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "模型结果必须被翻译成可理解的反馈。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_student_report_top.png", 486, 216, 660, 372, { alt: "画像卡片：把机器学习分类转成心理学语言" });
  footer(slide);
  return slide;
}
