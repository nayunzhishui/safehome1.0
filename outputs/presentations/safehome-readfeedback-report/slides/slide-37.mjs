import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide37(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "36 | 训练卡", "训练卡内容库：把建议变成可练习任务", "训练卡是安心家承接0版网页任务脚本的最佳位置。", "37");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["情绪命名、三秒暂停、替代回应等卡片","每张卡包含目的、步骤、示例和标签","适合后续加入CBT/ACT/沙盘式表达任务","内容库可版本化和研究化"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "训练卡让反馈进入行动。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/home_cards.png", 486, 216, 660, 372, { alt: "训练卡内容库：把建议变成可练习任务" });
  footer(slide);
  return slide;
}
