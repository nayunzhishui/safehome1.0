import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide45(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "44 | 小程序闭环", "小程序端闭环：记录、反馈、打卡、周报、督导", "家长端的日常使用应尽量短、清楚、可持续。", "45");
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/mini_diary.png", 70, 214, 148, 300, { alt: "记录" });
  tag(slide, "记录", 70, 536, 138, C.blue);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/mini_feedback.png", 306, 214, 148, 300, { alt: "反馈" });
  tag(slide, "反馈", 306, 536, 138, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/mini_checkin.png", 542, 214, 148, 300, { alt: "打卡" });
  tag(slide, "打卡", 542, 536, 138, C.blue);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/mini_weekly_report.png", 778, 214, 148, 300, { alt: "周报" });
  tag(slide, "周报", 778, 536, 138, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/mini_supervision.png", 1014, 214, 148, 300, { alt: "督导" });
  tag(slide, "督导", 1014, 536, 138, C.blue);
  text(slide, "这些页面共同构成安心家的长期陪伴闭环，0版网页可作为其中的评估入口。", 110, 604, 820, 44, { size: 20, bold: true, color: C.ink, lineSpacing: 1.2 });
  callout(slide, "小程序截图为基于现有 WXML/WXSS 内容生成的移动端预览，用于汇报页面逻辑。", 955, 560, 240, 110, C.amber);
  footer(slide);
  return slide;
}
