import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide31(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "30 | 板块架构", "安心家项目板块：后端、内容库、网页端、小程序端、共享类型", "当前项目路径为 D:\\codex\\workspace\\safehome1.0。", "31");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["backend：Flask + SQLite API","content：训练卡、反馈规则、评估工作表","apps/web：研究后台和网页端","apps/miniprogram：家长小程序端","shared：两端共用类型和常量"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "安心家比0版网页更像长期产品工程。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/home_dashboard.png", 486, 216, 660, 372, { alt: "安心家项目板块：后端、内容库、网页端、小程序端、共享类型" });
  footer(slide);
  return slide;
}
