import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide29(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "28 | 安心家理念", "安心家：面向家长的情绪管理与亲子支持系统", "基于UP跨诊断情绪调节框架，强调记录、识别、反馈、练习、追踪、支持。", "29");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["服务对象：亲子冲突中的家长","目标：形成更支持性的回应方式","方法：非诊断反馈与训练卡练习","边界：不替代咨询、诊断或医疗服务"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "安心家是长期陪伴主平台。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/home_landing.png", 486, 216, 660, 372, { alt: "安心家：面向家长的情绪管理与亲子支持系统" });
  footer(slide);
  return slide;
}
