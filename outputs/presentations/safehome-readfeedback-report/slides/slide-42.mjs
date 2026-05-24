import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide42(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "41 | 数据导出", "数据导出：服务论文与用户研究", "安心家后台需要能导出家长端闭环数据。", "42");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["支持后台导出","可整理目标、记录、反馈、打卡、周报、督导","后续接入学生画像和沙盘记录","导出必须受授权和伦理边界控制"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "导出能力连接产品和科研。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/home_export.png", 486, 216, 660, 372, { alt: "数据导出：服务论文与用户研究" });
  footer(slide);
  return slide;
}
