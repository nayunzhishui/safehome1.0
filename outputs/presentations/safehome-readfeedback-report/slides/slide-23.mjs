import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";

export default async function slide23(presentation) {
  const slide = presentation.slides.add();
  setBackground(slide);
  header(slide, "22 | 合并依据", "两个系统共享同一条支持性反馈逻辑", "0版网页强在评估报告，安心家强在长期训练和陪伴。", "23");
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/zero_home.png", 80, 220, 520, 320, { alt: "0版网页" });
  image(slide, "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots/home_landing.png", 680, 220, 520, 320, { alt: "安心家" });
  tag(slide, "0版网页", 104, 560, 210, C.blue);
  tag(slide, "安心家", 704, 560, 210, C.teal);
  text(slide, "共同边界是非诊断、支持性、可追踪。", 160, 612, 960, 42, { size: 20, bold: true, color: C.ink, lineSpacing: 1.2, align: "center" });
  footer(slide);
  return slide;
}
