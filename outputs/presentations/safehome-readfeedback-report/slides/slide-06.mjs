import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide06(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "05 | 0版网页工作流", "工作流程：测评进入，报告反馈，轮次收束", "学生端与研究者端围绕同一条数据链路运转。", "06");
  rect(slide, 82, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "填写", 102, 274, 90, C.blue);
  text(slide, "量表/文本", 102, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 258, 306, 42);
  rect(slide, 310, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "分类", 330, 274, 90, C.teal);
  text(slide, "机器学习", 330, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 486, 306, 42);
  rect(slide, 538, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "报告", 558, 274, 90, C.green);
  text(slide, "可视化", 558, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 714, 306, 42);
  rect(slide, 766, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "任务", 786, 274, 90, C.amber);
  text(slide, "小步干预", 786, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 942, 306, 42);
  rect(slide, 994, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "复测", 1014, 274, 90, C.lavender);
  text(slide, "收束画像", 1014, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  
  rect(slide, 128, 470, 1024, 94, { fill: "#FFFFFF", lineFill: "#D9E2EF", label: "每一次填写都不只生成分数，还进入后续任务、复测、文本关键词和研究导出。", size: 22, bold: true, color: C.blue, align: "center", pad: 18 });
  footer(slide);
  return slide;
}
