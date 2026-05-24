import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide21(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "20 | 0版网页小结", "0版网页已经形成“评估-反馈-追踪-导出”闭环", "每个功能都有明确的研究和用户价值。", "21");
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_student_report_visuals.png", 80, 220, 520, 320, { alt: "学生报告" });
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_admin.png", 680, 220, 520, 320, { alt: "研究后台" });
  tag(slide, "学生报告", 104, 560, 210, C.blue);
  tag(slide, "研究后台", 704, 560, 210, C.teal);
  text(slide, "前台帮助学生理解自己，后台帮助研究者整理数据。", 160, 612, 960, 42, { size: 20, bold: true, color: C.ink, lineSpacing: 1.2, align: "center" });
  footer(slide);
  return slide;
}
