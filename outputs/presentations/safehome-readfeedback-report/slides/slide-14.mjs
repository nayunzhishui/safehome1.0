import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide14(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "13 | 可视化图表", "雷达图与PCA分类图：解释“为什么是这一类”", "量表维度和训练样本分布共同帮助研究者和学生理解分类。", "14");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["雷达图显示IU、ERF、自我关怀和考试焦虑","PCA图展示个体点与训练样本群落","可视化降低机器学习黑箱感","后续可用于和导师讨论模型合理性"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "这是机器学习结果进入网页的核心展示。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_student_report_visuals.png", 486, 216, 660, 372, { alt: "雷达图与PCA分类图：解释“为什么是这一类”" });
  footer(slide);
  return slide;
}
