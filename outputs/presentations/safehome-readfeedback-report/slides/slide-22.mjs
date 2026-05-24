import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide22(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "21 | 合并定位", "合并不是拼页面，而是明确层级", "0版网页成为安心家的评估反馈模块，安心家承接长期陪伴。", "22");
  rect(slide, 82, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "安心家", 102, 274, 90, C.blue);
  text(slide, "主平台", 102, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 258, 306, 42);
  rect(slide, 310, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "0版网页", 330, 274, 90, C.teal);
  text(slide, "评估模块", 330, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 486, 306, 42);
  rect(slide, 538, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "内容库", 558, 274, 90, C.green);
  text(slide, "训练任务", 558, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 714, 306, 42);
  rect(slide, 766, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "数据库", 786, 274, 90, C.amber);
  text(slide, "统一记录", 786, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  arrow(slide, 942, 306, 42);
  rect(slide, 994, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, "后台", 1014, 274, 90, C.lavender);
  text(slide, "研究导出", 1014, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  
  rect(slide, 128, 470, 1024, 94, { fill: "#FFFFFF", lineFill: "#D9E2EF", label: "合并后对外可统一叫安心家，内部保留0版网页作为评估反馈引擎。", size: 22, bold: true, color: C.blue, align: "center", pad: 18 });
  footer(slide);
  return slide;
}
