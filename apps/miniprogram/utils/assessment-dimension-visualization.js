const MIN_RADAR_DIMENSIONS = 3;
const MAX_RADAR_DIMENSIONS = 8;

function toFiniteNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function formatNumber(value) {
  if (!Number.isFinite(value)) return "";
  return Number.isInteger(value) ? `${value}` : `${Math.round(value * 100) / 100}`;
}

function compactAxisLabel(label) {
  const text = String(label || "").trim();
  return text.length > 7 ? `${text.slice(0, 7)}…` : text;
}

function getQuestionBounds(question) {
  const optionScores = Array.isArray(question && question.options)
    ? question.options.map((option) => toFiniteNumber(option && option.score)).filter((score) => score !== null)
    : [];
  if (!optionScores.length) return null;
  return { min: Math.min(...optionScores), max: Math.max(...optionScores) };
}

function deriveDimensionRange(dimension, worksheet) {
  if (!dimension || !worksheet) return null;
  const definitions = Array.isArray(worksheet.dimensions) ? worksheet.dimensions : [];
  const questions = Array.isArray(worksheet.questions) ? worksheet.questions : [];
  const definition = definitions.find((item) => item && (item.code === dimension.key || item.key === dimension.key));
  const configuredIds = definition && Array.isArray(definition.item_ids) ? definition.item_ids : [];
  const matchedQuestions = questions.filter((question) => {
    if (!question) return false;
    if (configuredIds.length) return configuredIds.includes(question.id || question.code);
    return question.dimension === dimension.key;
  });
  const bounds = matchedQuestions.map(getQuestionBounds).filter(Boolean);
  if (!bounds.length || bounds.length !== matchedQuestions.length) return null;

  const divisor = dimension.scoreMethod === "mean" ? bounds.length : 1;
  const min = bounds.reduce((total, item) => total + item.min, 0) / divisor;
  const max = bounds.reduce((total, item) => total + item.max, 0) / divisor;
  if (!Number.isFinite(min) || !Number.isFinite(max) || max <= min) return null;
  return { min, max };
}

function buildDimensionVisualization(dimensions, worksheet) {
  const rows = (Array.isArray(dimensions) ? dimensions : []).map((dimension) => {
    const score = toFiniteNumber(dimension && dimension.score);
    const range = deriveDimensionRange(dimension, worksheet);
    if (score === null || !range) {
      return {
        ...dimension,
        hasComparableRange: false,
        rangeText: "量尺范围暂未核定",
        positionText: "保留原始得分",
        positionPercent: 0,
        progressStyle: "width:0%;",
      };
    }

    const positionPercent = Math.round(clamp((score - range.min) / (range.max - range.min), 0, 1) * 100);
    return {
      ...dimension,
      hasComparableRange: true,
      minScore: range.min,
      maxScore: range.max,
      rangeText: `本维度量尺 ${formatNumber(range.min)}–${formatNumber(range.max)}`,
      positionText: `量尺位置 ${positionPercent}%`,
      positionPercent,
      progressStyle: `width:${positionPercent}%;`,
      axisLabel: compactAxisLabel(dimension.label),
      value: positionPercent / 100,
      referenceValue: 0.5,
    };
  });

  const comparableRows = rows.filter((item) => item.hasComparableRange);
  const showRadar = rows.length >= MIN_RADAR_DIMENSIONS
    && rows.length <= MAX_RADAR_DIMENSIONS
    && comparableRows.length === rows.length;
  return {
    dimensions: rows,
    radarFeatures: showRadar ? comparableRows : [],
    showRadar,
    currentLabel: "本次填写",
    referenceLabel: "量尺中点",
    chartNote: showRadar
      ? "图形展示各维度在自身量尺中的相对位置；量尺中点不是常模、目标值或好坏标准。"
      : rows.length > MAX_RADAR_DIMENSIONS
        ? `本量表包含 ${rows.length} 个维度，为避免标签拥挤，改用维度卡片展示。`
        : "部分维度的可比量尺范围尚未核定，暂以原始得分卡片展示。",
  };
}

module.exports = {
  buildDimensionVisualization,
  compactAxisLabel,
  deriveDimensionRange,
};
