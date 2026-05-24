import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide41(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "40 | 规则库", "反馈规则库：保证非诊断反馈可解释、可维护", "规则库把“如何解释”从代码中分离出来。", "41");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["规则基于标签和场景触发","输出触发总结、模式总结和替代回应","便于研究者调整内容","后续可接入0版网页画像规则"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "规则库是安心家内容工程的核心。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/home_rules.png", 486, 216, 660, 372, { alt: "反馈规则库：保证非诊断反馈可解释、可维护" });
  footer(slide);
  return slide;
}
