import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide20(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "19 | 数据导出", "数据与导出：保留研究可用字段", "研究者可以分别导出量表、画像、轮次、关键词和沙盘记录。", "20");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["旧版：宽表、长表、计分表、数据字典","新版：画像分数、置信度、轮次追踪","沙盘：象征物坐标、反思文本、摘要指标","研究授权字段控制导出范围"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "导出能力决定后续论文数据整理效率。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_admin.png", 486, 216, 660, 372, { alt: "数据与导出：保留研究可用字段" });
  footer(slide);
  return slide;
}
