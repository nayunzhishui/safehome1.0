import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide04(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "03 | 0版网页定位", "0版网页是治疗性评估与反馈报告原型", "不是普通问卷网页，而是把测评结果转化为解释、任务和追踪。", "04");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["面向学生、家长/研究参与者、研究者和咨询/督导者","保留安心家视觉入口，同时加入学生画像模块","输出非诊断反馈、可视化图表和研究数据","所有功能围绕“评估-反馈-追踪”组织"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "先把可演示原型讲清楚，再谈并入安心家。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_home.png", 486, 216, 660, 372, { alt: "0版网页是治疗性评估与反馈报告原型" });
  footer(slide);
  return slide;
}
