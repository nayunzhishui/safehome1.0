import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide07(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "06 | 双量表测评", "双量表测评页：自我关怀与不确定性不耐受", "旧版研究模块仍然保留，为家长/研究参与者提供基础测评。", "07");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["自我关怀量表用于理解自我支持资源","不确定性不耐受用于理解焦虑相关认知倾向","页面保留知情同意和研究授权","提交后进入非诊断反馈报告"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "这是0版网页最早的测评研究基础。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_parent_assessment.png", 486, 216, 660, 372, { alt: "双量表测评页：自我关怀与不确定性不耐受" });
  footer(slide);
  return slide;
}
