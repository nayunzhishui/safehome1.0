import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide33(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "32 | 研究看板", "研究看板：把分散记录汇总到后台", "研究者可从这里了解目标、记录、反馈、训练、周报和督导。", "33");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["展示核心数据概览","连接各管理页面","适合导师快速了解项目进度","后续可加入0版网页学生画像统计"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "看板是安心家的研究者视角。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/home_dashboard.png", 486, 216, 660, 372, { alt: "研究看板：把分散记录汇总到后台" });
  footer(slide);
  return slide;
}
