import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide26(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "25 | 内容合并", "0版网页任务脚本可进入安心家训练卡体系", "CBT、ACT、沙盘式表达任务可以变成安心家的训练内容。", "26");
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_files_model.png", 80, 220, 520, 320, { alt: "任务脚本" });
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/home_cards.png", 680, 220, 520, 320, { alt: "训练卡库" });
  tag(slide, "任务脚本", 104, 560, 210, C.blue);
  tag(slide, "训练卡库", 704, 560, 210, C.teal);
  text(slide, "这样既保留研究原型，又接入家长/学生的持续练习场景。", 160, 612, 960, 42, { size: 20, bold: true, color: C.ink, lineSpacing: 1.2, align: "center" });
  footer(slide);
  return slide;
}
