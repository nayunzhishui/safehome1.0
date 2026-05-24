import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide35(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "34 | 情绪记录", "情绪事件记录：捕捉触发点、自动想法和行为反应", "数据结构服务于UP情绪调节框架。", "35");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["记录场景和事件描述","记录家长与孩子的情绪强度","记录自动想法和身体感受","记录行为与原始文本"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "这是生成反馈和训练建议的原始材料。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/home_diaries.png", 486, 216, 660, 372, { alt: "情绪事件记录：捕捉触发点、自动想法和行为反应" });
  footer(slide);
  return slide;
}
