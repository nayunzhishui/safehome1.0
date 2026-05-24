import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide38(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "37 | 打卡记录", "打卡记录：把练习转成可追踪变化", "家长完成训练卡后记录情绪前后变化和反思。", "38");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["记录是否完成训练","记录情绪前后变化","保存练习反思","为周报和研究导出提供数据"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "打卡让“练习有没有用”可以被观察。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/home_checkins.png", 486, 216, 660, 372, { alt: "打卡记录：把练习转成可追踪变化" });
  footer(slide);
  return slide;
}
