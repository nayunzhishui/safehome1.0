import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide03(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "02 | 总体结论", "0版网页是评估反馈原型，安心家是长期陪伴平台", "两者不是两个互相竞争的网站，而是同一项目的两个层级。", "03");
  rect(slide, 82, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "0版网页", 102, 274, 90, C.teal);
  text(slide, "测评画像", 102, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 258, 306, 42);
  rect(slide, 310, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "报告页", 330, 274, 90, C.blue);
  text(slide, "解释反馈", 330, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 486, 306, 42);
  rect(slide, 538, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "轮次任务", 558, 274, 90, C.green);
  text(slide, "追踪变化", 558, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 714, 306, 42);
  rect(slide, 766, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "研究后台", 786, 274, 90, C.amber);
  text(slide, "导出分析", 786, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 942, 306, 42);
  rect(slide, 994, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "安心家", 1014, 274, 90, C.lavender);
  text(slide, "长期陪伴", 1014, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  
  rect(slide, 128, 470, 1024, 94, { fill: "#FFFFFF", lineFill: "#D9E2EF", label: "建议定位：0版网页沉淀为安心家的“治疗性评估与反馈报告模块”。", size: 22, bold: true, color: C.blue, align: "center", pad: 18 });
  footer(slide);
  return slide;
}
