// B1 急救卡：分组、卡片内容和本地缓存。见 docs/11_商业化开发/开发框架.md 第 3 节。
// GET /api/cards/quick（B1-后端）做好以前，先用下面这份分组：只有卡片编号，正文从 GET /api/cards 取，
// 不写死在前端（test_rc0810_f20 会检查）。后端做好以后改成先读接口，接口失败再用这份。
const GROUPS = {
  heat: ["three_second_pause", "parent_body_signal_check", "parent_body_grounding", "emotion_naming"],
  after: ["parent_after_conflict_repair", "parent_repair_question"],
};
const CACHE_KEY = "safehome.quickCard.texts";
const CACHE_MS = 7 * 24 * 3600 * 1000; // 缓存 7 天：第二次打开不用等网络

function pick(card) {
  return {
    id: card.id,
    title: card.user_facing_title || card.title || "",
    duration_minutes: card.duration_minutes || 0,
    steps: Array.isArray(card.steps) ? card.steps : [],
    example: card.example_phrase || card.example || "",
    stopRule: Array.isArray(card.stop_rules) && card.stop_rules.length ? card.stop_rules[0] : "",
    audio_file_id: card.audio_file_id || "",
  };
}

function readCache() {
  try {
    const cached = wx.getStorageSync(CACHE_KEY);
    return cached && cached.savedAt && Date.now() - cached.savedAt < CACHE_MS ? cached.cards : null;
  } catch (error) {
    return null;
  }
}

function writeCache(cards) {
  try {
    wx.setStorageSync(CACHE_KEY, { savedAt: Date.now(), cards });
  } catch (error) {
    // 存不进去就每次都等网络
  }
}

function cardsFor(group, byId) {
  return (GROUPS[group] || GROUPS.heat).map((id) => byId[id]).filter(Boolean);
}

// 有缓存先用缓存马上显示，再去接口拿最新的；onUpdate 可能被调用两次。
function loadQuickCards(api, group, onUpdate) {
  const cached = readCache();
  if (cached) onUpdate(cardsFor(group, cached));
  const wanted = new Set([].concat(GROUPS.heat, GROUPS.after));
  return api.listCards()
    .then((data) => {
      const byId = {};
      ((data && data.items) || []).forEach((card) => {
        if (wanted.has(card.id)) byId[card.id] = pick(card);
      });
      writeCache(byId);
      onUpdate(cardsFor(group, byId));
    })
    .catch(() => {
      if (!cached) onUpdate([]);
    });
}

module.exports = { GROUPS, loadQuickCards };
