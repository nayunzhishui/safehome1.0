function formatTime(isoText) {
  if (!isoText || typeof isoText !== "string") {
    return "";
  }
  const timePart = isoText.includes("T") ? isoText.split("T")[1] : isoText.split(" ")[1] || "";
  return timePart.slice(0, 5);
}

function prepareLinePoints(items = [], width = 320, height = 160, padding = 24) {
  const safeWidth = Math.max(width, 120);
  const safeHeight = Math.max(height, 100);
  const innerWidth = Math.max(safeWidth - padding * 2, 1);
  const innerHeight = Math.max(safeHeight - padding * 2, 1);
  const points = items.map((item, index) => {
    const x = items.length <= 1 ? padding + innerWidth / 2 : padding + (innerWidth * index) / (items.length - 1);
    const level = Number(item.intensity_level || 0);
    const y = padding + innerHeight - ((Math.max(1, Math.min(level, 10)) - 1) / 9) * innerHeight;
    return {
      ...item,
      x,
      y,
      label: formatTime(item.created_at),
    };
  });
  return {
    width: safeWidth,
    height: safeHeight,
    padding,
    points,
    yTicks: [1, 5, 10],
  };
}

function hitTestPoint(points = [], x, y, radius = 18) {
  let hit = null;
  let bestDistance = Infinity;
  points.forEach((point) => {
    const distance = Math.sqrt((point.x - x) ** 2 + (point.y - y) ** 2);
    if (distance <= radius && distance < bestDistance) {
      hit = point;
      bestDistance = distance;
    }
  });
  return hit;
}

module.exports = {
  formatTime,
  hitTestPoint,
  prepareLinePoints,
};
