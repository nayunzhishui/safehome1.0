import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide46(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "45 | 下一阶段", "下一步：先完善0版网页，再并入安心家", "以可汇报、可演示、可研究为优先。", "46");
  rect(slide, 82, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "第1周", 102, 274, 90, C.green);
  text(slide, "0版网页完善", 102, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 258, 306, 42);
  rect(slide, 310, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "第2周", 330, 274, 90, C.teal);
  text(slide, "研究验证", 330, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 486, 306, 42);
  rect(slide, 538, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "第3周", 558, 274, 90, C.blue);
  text(slide, "合并准备", 558, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 714, 306, 42);
  rect(slide, 766, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "第4周", 786, 274, 90, C.amber);
  text(slide, "合并演示", 786, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 942, 306, 42);
  rect(slide, 994, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "导师确认", 1014, 274, 90, C.red);
  text(slide, "论文主线", 1014, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  
  rect(slide, 128, 470, 1024, 94, { fill: "#FFFFFF", lineFill: "#D9E2EF", label: "需要导师确认：论文主线更偏治疗性评估流程、机器学习画像验证，还是安心家产品化平台建设。", size: 22, bold: true, color: C.blue, align: "center", pad: 18 });
  footer(slide);
  return slide;
}
