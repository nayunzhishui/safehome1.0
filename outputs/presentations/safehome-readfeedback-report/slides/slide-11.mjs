import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide11(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "10 | 模型文件", "模型与规则文件：保证可复现和可迭代", "0版网页把机器学习模型、画像规则和任务脚本保存为轻量文件。", "11");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["ml_model.json 保存聚类中心、标准化参数和PCA参数","profile_rules.json 保存画像解释和首轮建议","sandplay_tasks.json 保存沙盘式任务脚本","SQLite 保存提交、轮次和沙盘记录"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "轻量文件结构便于之后迁移到安心家。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_files_model.png", 486, 216, 660, 372, { alt: "模型与规则文件：保证可复现和可迭代" });
  footer(slide);
  return slide;
}
