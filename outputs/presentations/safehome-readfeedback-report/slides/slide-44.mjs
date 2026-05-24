import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide44(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "43 | 小程序入口", "小程序端：面向家长的轻量入口", "小程序端适合日常记录和练习。", "44");
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/mini_home.png", 82, 220, 168, 338, { alt: "首页" });
  tag(slide, "首页", 82, 580, 150, C.blue);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/mini_training.png", 302, 220, 168, 338, { alt: "训练" });
  tag(slide, "训练", 302, 580, 150, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/mini_assessment.png", 522, 220, 168, 338, { alt: "测一测" });
  tag(slide, "测一测", 522, 580, 150, C.blue);
  text(slide, "小程序首页承接低负担使用，训练页承接干预内容，测评页承接工作表和未来0版网页能力。", 780, 272, 340, 170, { size: 24, bold: true, color: C.ink, lineSpacing: 1.35 });
  callout(slide, "小程序截图为基于现有 WXML/WXSS 内容生成的移动端预览，用于汇报页面逻辑。", 760, 490, 400, 80, C.amber);
  footer(slide);
  return slide;
}
