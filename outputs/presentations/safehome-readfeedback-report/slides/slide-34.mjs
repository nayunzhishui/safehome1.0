import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide34(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "33 | 目标管理", "目标管理：先确定家长要练习的具体场景", "安心家的干预不是泛泛建议，而是围绕一个小目标持续练习。", "34");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["目标围绕具体亲子互动场景","SMART目标帮助降低模糊性","和后续情绪记录、训练卡关联","适合形成个案追踪材料"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "目标管理是家长端闭环起点。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/home_goals.png", 486, 216, 660, 372, { alt: "目标管理：先确定家长要练习的具体场景" });
  footer(slide);
  return slide;
}
