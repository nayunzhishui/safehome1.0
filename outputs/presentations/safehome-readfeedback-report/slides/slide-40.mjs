import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide40(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "39 | 人工督导", "人工督导：从自动反馈升级到人工支持", "当系统反馈不足以回应复杂情况时，需要人工支持入口。", "40");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["提交督导请求和联系方式","保留风险提示字段","支持人工回复和状态管理","与伦理边界直接相关"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "督导入口是平台安全性的一部分。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/home_supervision.png", 486, 216, 660, 372, { alt: "人工督导：从自动反馈升级到人工支持" });
  footer(slide);
  return slide;
}
