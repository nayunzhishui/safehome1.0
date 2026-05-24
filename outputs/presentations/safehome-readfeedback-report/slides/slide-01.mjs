import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide01(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  rect(slide, 0, 0, 1280, 720, { fill: "#F5F8FC", line: false, radius: "rounded-sm" });
  rect(slide, 820, 0, 460, 720, { fill: "#E8F3F2", line: false, radius: "rounded-sm" });
  rect(slide, 866, 100, 300, 320, { fill: "#FFFFFF", lineFill: "#D3E5E3", radius: "rounded-lg" });
  text(slide, "评估", 926, 150, 180, 44, { size: 34, bold: true, color: C.blue, align: "center" });
  line(slide, 960, 210, 112, 5, C.teal);
  text(slide, "画像\n反馈\n追踪\n合并", 927, 250, 180, 130, { size: 24, bold: true, color: C.ink, align: "center", lineSpacing: 1.35 });
  tag(slide, "导师阶段汇报", 86, 74, 150, C.teal);
  text(slide, "0版网页与安心家合并工作汇报", 84, 142, 680, 128, { size: 42, bold: true, color: C.ink, lineSpacing: 1.15 });
  text(slide, "先完整汇报0版网页的设计、理念、功能和截图，再说明与安心家的合并方式，最后汇报安心家项目的整体工作思路。", 88, 330, 710, 90, { size: 21, color: C.muted, lineSpacing: 1.3 });
  metric(slide, 88, 498, 190, "46页", "详细汇报", C.teal);
  metric(slide, 302, 498, 190, "0版网页", "功能截图", C.blue);
  metric(slide, 516, 498, 190, "安心家", "工作思路", C.amber);
  footer(slide);
  return slide;
}
