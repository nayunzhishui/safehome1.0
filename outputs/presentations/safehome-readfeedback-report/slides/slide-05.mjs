import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide05(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "04 | 首页/导航", "首页承担统一入口：旧版研究与学生画像并存", "一个站点内同时呈现双量表测评、学生画像测评、研究说明和后台入口。", "05");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["首页保留安心家视觉风格","导航区连接双量表、学生测评、研究说明和后台","用户一进入即可选择研究路径","后续可迁入安心家统一导航"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "首页是0版网页的信息入口和合并雏形。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_home.png", 486, 216, 660, 372, { alt: "首页承担统一入口：旧版研究与学生画像并存" });
  footer(slide);
  return slide;
}
