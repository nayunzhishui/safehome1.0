import fs from "node:fs";

export const C = {
  ink: "#102033",
  muted: "#5B677A",
  soft: "#F4F7FB",
  panel: "#FFFFFF",
  line: "#D9E2EF",
  blue: "#1D4E89",
  teal: "#168A86",
  green: "#4D8B31",
  amber: "#C17A22",
  red: "#B45454",
  lavender: "#7A5AA8",
};

export function setBackground(slide, fill = C.soft) {
  slide.background.fill = fill;
}

export function text(slide, value, x, y, w, h, opt = {}) {
  const box = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width: w, height: h },
  });
  box.text.set(value);
  box.text.style = {
    typeface: "Microsoft YaHei",
    fontSize: opt.size ?? 24,
    bold: opt.bold ?? false,
    color: opt.color ?? C.ink,
    lineSpacing: opt.lineSpacing ?? 1.22,
    alignment: opt.align ?? "left",
    autoFit: "shrinkText",
  };
  if (opt.valign) box.text.verticalAlignment = opt.valign;
  return box;
}

export function rect(slide, x, y, w, h, opt = {}) {
  const shape = slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width: w, height: h },
    fill: opt.fill ?? C.panel,
    line: opt.line === false ? { style: "solid", width: 0, fill: opt.fill ?? C.panel } : {
      style: "solid",
      width: opt.lineWidth ?? 1,
      fill: opt.lineFill ?? C.line,
    },
    borderRadius: opt.radius ?? "rounded-lg",
  });
  if (opt.label) {
    shape.text.set(opt.label);
    shape.text.style = {
      typeface: "Microsoft YaHei",
      fontSize: opt.size ?? 22,
      bold: opt.bold ?? false,
      color: opt.color ?? C.ink,
      lineSpacing: opt.lineSpacing ?? 1.18,
      alignment: opt.align ?? "left",
      autoFit: "shrinkText",
      insets: { top: opt.pad ?? 18, right: opt.pad ?? 18, bottom: opt.pad ?? 18, left: opt.pad ?? 18 },
    };
    shape.text.verticalAlignment = opt.valign ?? "middle";
  }
  return shape;
}

export function line(slide, x, y, w, h = 2, fill = C.line) {
  return rect(slide, x, y, w, h, { fill, line: false, radius: "rounded-sm" });
}

export function header(slide, kicker, title, subtitle = "", page = "") {
  text(slide, kicker, 72, 34, 420, 30, { size: 15, bold: true, color: C.teal });
  text(slide, title, 72, 66, 1010, 48, { size: 32, bold: true, color: C.ink, lineSpacing: 1.05 });
  if (subtitle) text(slide, subtitle, 74, 130, 1030, 34, { size: 17, color: C.muted });
  line(slide, 72, 180, 1136, 2, "#D8E5F4");
  if (page) text(slide, page, 1145, 36, 70, 24, { size: 13, color: C.muted, align: "right" });
}

export function footer(slide) {
  text(slide, "安心家 x 0版网页 | 导师阶段汇报 | 2026-05-23", 72, 684, 820, 22, { size: 12, color: "#7C8797" });
}

export function metric(slide, x, y, w, value, label, color = C.blue) {
  rect(slide, x, y, w, 94, { fill: "#FFFFFF", lineFill: "#D7E1EF", radius: "rounded-lg" });
  text(slide, value, x + 20, y + 18, w - 40, 34, { size: 30, bold: true, color });
  text(slide, label, x + 20, y + 56, w - 40, 24, { size: 15, color: C.muted });
}

export function callout(slide, value, x, y, w, h, color = C.blue) {
  rect(slide, x, y, w, h, { fill: "#FFFFFF", lineFill: "#D9E2EF", radius: "rounded-lg" });
  rect(slide, x, y, 8, h, { fill: color, line: false, radius: "rounded-sm" });
  text(slide, value, x + 26, y + 22, w - 42, h - 44, { size: 20, bold: true, color: C.ink });
}

export function bullets(slide, items, x, y, w, h, opt = {}) {
  const content = items.map((item) => `• ${item}`).join("\n");
  return text(slide, content, x, y, w, h, {
    size: opt.size ?? 20,
    color: opt.color ?? C.ink,
    lineSpacing: opt.lineSpacing ?? 1.38,
  });
}

export function tag(slide, label, x, y, w, color = C.blue) {
  rect(slide, x, y, w, 34, { fill: color, line: false, radius: "rounded-lg", label, color: "#FFFFFF", size: 15, bold: true, align: "center", pad: 5 });
}

export function arrow(slide, x, y, w, label = "→") {
  text(slide, label, x, y, w, 36, { size: 26, bold: true, color: C.muted, align: "center", valign: "middle" });
}

export function image(slide, file, x, y, w, h, opt = {}) {
  const frame = rect(slide, x - 6, y - 6, w + 12, h + 12, {
    fill: opt.frameFill ?? "#FFFFFF",
    lineFill: opt.lineFill ?? C.line,
    radius: opt.radius ?? "rounded-lg",
  });
  slide.images.add({
    data: fs.readFileSync(file),
    mimeType: "image/png",
    position: { left: x, top: y, width: w, height: h },
    alt: opt.alt ?? "",
    fit: opt.fit ?? "contain",
  });
  return frame;
}

export function sectionPill(slide, label, color = C.teal) {
  tag(slide, label, 72, 196, 150, color);
}
