import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide32(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "31 | 网页首页", "网页首页设计：支持性、清晰、低压", "页面视觉以绿色支持感为主，不做营销式大页面。", "32");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["突出安心陪伴和家长支持","入口连接研究后台和功能模块","文案强调非评判和小步练习","适合后续承接0版网页评估入口"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "首页负责解释项目定位。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/home_landing.png", 486, 216, 660, 372, { alt: "网页首页设计：支持性、清晰、低压" });
  footer(slide);
  return slide;
}
