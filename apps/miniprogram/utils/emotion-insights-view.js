// Turns the self-only emotion analysis payload into display rows.
// Shared by the scale result page and the growth dashboard so both read the same way.

function percentText(value) {
  return `${Math.round(Number(value) * 100)}%`;
}

function describeSceneEmotion(item) {
  let text = `${item.scene} × ${item.emotion} · ${item.support} 次`;
  if (item.share_in_scene !== undefined && item.share_in_scene !== null) {
    text += `，占该场景 ${percentText(item.share_in_scene)}`;
    if (item.share_overall !== undefined && item.share_overall !== null) text += `（全部记录中 ${percentText(item.share_overall)}）`;
  }
  if (item.average_intensity !== undefined && item.average_intensity !== null) text += `，平均强度 ${item.average_intensity}`;
  return text;
}

const ACTION_LABELS = { insufficient: "记录一件小事", withheld: "查看紧急求助资源" };

function buildEmotionInsightsView(payload) {
  if (!payload) return null;
  const statusText = {
    available: "已生成近期线索",
    insufficient: "记录还不够",
    withheld: "已转人工关注",
    ineligible: "当前阶段未开放",
  }[payload.availability] || "暂不可用";
  const parentChild = payload.parent_child || {};
  const trend = (payload.affect && payload.affect.trend) || {};
  const affectItems = (payload.affect && payload.affect.items) || [];
  const maxCount = Math.max(1, ...affectItems.map((item) => Number(item.count) || 0));
  return {
    ...payload,
    statusText,
    available: payload.availability === "available",
    actionLabel: ACTION_LABELS[payload.availability] || "",
    affectItems: affectItems.map((item) => ({
      ...item,
      summary: `${item.count} 次 · 平均强度 ${item.average_intensity}`,
      width: `${Math.max(8, Math.round((Number(item.count) || 0) / maxCount * 100))}%`,
    })),
    interactionEdges: ((payload.interaction_network && payload.interaction_network.edges) || []).map((item) => ({
      ...item,
      key: `${item.source}:${item.target}`,
      summary: describeSceneEmotion(item),
    })),
    trendText: trend.available ? trend.summary_text : "",
    trendNote: trend.available ? trend.next_check_text : "",
    parentChildPairs: (parentChild.pairs || []).map((item) => ({
      ...item,
      key: `${item.parent_emotion}:${item.child_emotion}`,
      summary: `你“${item.parent_emotion}”时孩子“${item.child_emotion}” · ${item.support} 次`,
    })),
    parentChildSummary: parentChild.paired_record_count ? parentChild.summary_text : "",
    parentChildNote: parentChild.next_check_text || "",
  };
}

module.exports = {
  buildEmotionInsightsView,
  describeSceneEmotion,
  percentText,
};
