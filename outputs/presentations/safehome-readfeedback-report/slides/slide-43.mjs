import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide43(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "42 | 联调测试", "联调测试：验证后端、网页端和内容规则能跑通", "当前安心家已有最小联调入口。", "43");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["创建情绪事件记录","生成即时反馈","获取训练卡推荐","验证三步闭环"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "联调测试保证系统不是静态页面。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/home_integration.png", 486, 216, 660, 372, { alt: "联调测试：验证后端、网页端和内容规则能跑通" });
  footer(slide);
  return slide;
}
