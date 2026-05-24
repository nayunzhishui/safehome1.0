import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide36(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "35 | 非诊断反馈", "反馈结果：从记录中识别互动模式", "系统输出支持性解释和替代回应，而不是评价家长。", "36");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["识别触发点和常见模式","输出支持性反馈","给出替代回应句","推荐训练卡"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "安心家的语言风格必须保持非评判。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/home_feedback.png", 486, 216, 660, 372, { alt: "反馈结果：从记录中识别互动模式" });
  footer(slide);
  return slide;
}
