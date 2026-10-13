// 训练卡文字的展示整理：训练卡、个性化方案、练习页共用。

// 多条停止规则合成一段：去掉每条末尾标点再用分号连接，避免出现“。；”。
function joinRules(rules) {
  const items = (rules || []).map((rule) => String(rule || "").trim().replace(/[。；;，,]+$/, "")).filter(Boolean);
  return items.length ? `${items.join("；")}。` : "";
}

// 列表行只放一句话场景（Figma CourseRow 第二行）。
function firstSentence(text) {
  const value = String(text || "").trim();
  const end = value.indexOf("。");
  return end >= 0 ? value.slice(0, end + 1) : value;
}

module.exports = {
  joinRules,
  firstSentence,
};
