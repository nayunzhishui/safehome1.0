// 今日曲线（Figma 647:1055）：画在 350×150 的盒子里，强度 v 的点在 y = 130 − 10v，
// 点沿 x 60–290 平均分布（只有一个点时居中）。按实际盒宽等比缩放，线段用旋转的细条绘制。
const { formatTime } = require("./chart");

const BOX_WIDTH = 350;
const BOX_HEIGHT = 150;
const GRID_LEVELS = [10, 6, 2];

function clampLevel(value) {
  return Math.max(1, Math.min(10, Math.round(Number(value) || 1)));
}

function round(value) {
  return Math.round(value * 100) / 100;
}

function curveLayout(records = [], boxWidth = BOX_WIDTH) {
  const scale = boxWidth / BOX_WIDTH;
  const count = records.length;
  const labelEvery = count <= 5 ? 1 : Math.ceil(count / 4);
  const points = records.map((record, index) => {
    const level = clampLevel(record.intensity_level);
    const fx = count <= 1 ? BOX_WIDTH / 2 : 60 + (230 * index) / (count - 1);
    const showLabel = index === 0 || index === count - 1 || index % labelEvery === 0;
    return {
      id: record.id || `point-${index}`,
      level,
      x: round(fx * scale),
      y: round((130 - 10 * level) * scale),
      label: formatTime(record.created_at),
      showLabel,
      brief: record.brief_text || "",
    };
  });
  const segments = points.slice(1).map((point, index) => {
    const from = points[index];
    const dx = point.x - from.x;
    const dy = point.y - from.y;
    return {
      key: `${from.id}-${point.id}`,
      left: from.x,
      top: from.y,
      width: round(Math.sqrt(dx * dx + dy * dy)),
      angle: round((Math.atan2(dy, dx) * 180) / Math.PI),
    };
  });
  return {
    width: round(boxWidth),
    height: round(BOX_HEIGHT * scale),
    grid: GRID_LEVELS.map((level) => round((130 - 10 * level) * scale)),
    labelTop: round(126 * scale),
    points,
    segments,
  };
}

module.exports = { curveLayout, clampLevel };
