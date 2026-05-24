import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide27(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "26 | 数据合并", "研究数据进入统一后台，但保留模块字段", "避免强行合成一张表，减少数据含义混乱。", "27");
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_admin.png", 80, 220, 520, 320, { alt: "0版导出" });
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/home_export.png", 680, 220, 520, 320, { alt: "安心家导出" });
  tag(slide, "0版导出", 104, 560, 210, C.blue);
  tag(slide, "安心家导出", 704, 560, 210, C.teal);
  text(slide, "建议按模块导出：家长端、学生画像、轮次追踪、沙盘记录。", 160, 612, 960, 42, { size: 20, bold: true, color: C.ink, lineSpacing: 1.2, align: "center" });
  footer(slide);
  return slide;
}
