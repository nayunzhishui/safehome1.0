import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide19(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "18 | 研究者后台", "研究者后台：双量表研究与学生画像研究合并管理", "后台支持查看概览、研究记录和分模块导出。", "19");
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ["同一个后台管理旧版和新版数据","双量表提交、学生提交、轮次和沙盘记录分区","导出字段便于论文和用户研究分析","管理员登录保护后台入口"], 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, "后台是从网页原型走向研究工具的基础。", 92, 466, 320, 136, C.teal);
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_admin.png", 486, 216, 660, 372, { alt: "研究者后台：双量表研究与学生画像研究合并管理" });
  footer(slide);
  return slide;
}
