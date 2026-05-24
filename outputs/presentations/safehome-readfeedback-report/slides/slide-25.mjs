import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide25(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "24 | 迁移路线", "迁移顺序：内容先行，API第二，前端最后", "降低风险，保留原型可回退。", "25");
  rect(slide, 82, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "第1步", 102, 274, 90, C.green);
  text(slide, "内容迁移", 102, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 258, 306, 42);
  rect(slide, 310, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "第2步", 330, 274, 90, C.teal);
  text(slide, "模型服务", 330, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 486, 306, 42);
  rect(slide, 538, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "第3步", 558, 274, 90, C.blue);
  text(slide, "数据表扩展", 558, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 714, 306, 42);
  rect(slide, 766, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "第4步", 786, 274, 90, C.amber);
  text(slide, "页面迁移", 786, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 942, 306, 42);
  rect(slide, 994, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "第5步", 1014, 274, 90, C.lavender);
  text(slide, "统一后台", 1014, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  
  rect(slide, 128, 470, 1024, 94, { fill: "#FFFFFF", lineFill: "#D9E2EF", label: "不直接覆盖原0版网页；先把可复用内容和模型逻辑搬入安心家。", size: 22, bold: true, color: C.blue, align: "center", pad: 18 });
  footer(slide);
  return slide;
}
