// 训练库（Figma 643:720）：三个阶段由浅入深，类别按训练卡 type（个别按 tag）归组。
// 只用开放清单（/api/cards）里实际返回的卡；没有卡的类别不显示。
// 新卡的 type 还没列进来时归到最后的“更多练习”，不会从训练库里消失。
const TRAINING_STAGES = [
  {
    level: 1,
    title: "阶段一 · 认识和稳定情绪",
    subtitle: "先看见情绪，再让身体慢下来",
    categories: [
      { key: "awareness", label: "情绪觉察", types: ["emotion_awareness", "emotion_regulation", "mindfulness"] },
      { key: "body", label: "身体调节", types: ["body_awareness", "stress_management"], tags: ["body_awareness"] },
      { key: "pause", label: "暂停训练", tags: ["pause_before_response"] },
      { key: "expression", label: "情绪表达", types: ["emotion_expression", "expressive_task"] },
      { key: "self-support", label: "自我支持", types: ["self_support", "student_self_support", "parent_self_care", "resilience", "social_support"] },
    ],
  },
  {
    level: 2,
    title: "阶段二 · 改变想法和行为",
    subtitle: "从自动反应转向更有帮助的回应",
    categories: [
      { key: "reframe", label: "认知调整", types: ["cognitive_flexibility", "attribution_retraining", "psychological_flexibility", "worry_management"] },
      { key: "thought-record", label: "替代想法", types: ["cbt", "student_cbt"] },
      { key: "communication", label: "沟通表达", types: ["behavior_substitution"] },
      { key: "small-steps", label: "小步行动", types: ["behavior_activation", "health_behavior", "values_action", "motivation", "positive_cognition", "strengths_use", "curiosity"] },
    ],
  },
  {
    level: 3,
    title: "阶段三 · 改善亲子关系",
    subtitle: "先连接，再讨论问题",
    categories: [
      { key: "nonjudgmental", label: "非评判陪伴", types: ["nonjudgmental_response", "parent_reflection", "mentalizing"] },
      { key: "repair", label: "关系修复", types: ["relationship_repair", "parent_support", "parent_up"] },
      { key: "positive", label: "积极互动", types: ["parent_child_communication"] },
      { key: "relationship", label: "关系探索练习", types: ["relationship_growth"] },
    ],
  },
];

const OTHER_CATEGORY = { key: "other", label: "更多练习" };

function matches(category, card) {
  if ((category.types || []).includes(card.type)) return true;
  const tags = Array.isArray(card.tags) ? card.tags : [];
  return (category.tags || []).some((tag) => tags.includes(tag));
}

// 按阶段顺序逐个类别认领卡片，一张卡只出现在第一个匹配的类别里（例如身体信号检查先归“身体调节”）。
function groupTrainingLibrary(cards) {
  const available = (cards || []).filter((card) => card && card.id);
  const claimed = new Set();
  const stages = TRAINING_STAGES.map((stage) => ({
    level: stage.level,
    title: stage.title,
    subtitle: stage.subtitle,
    categories: stage.categories.map((category) => {
      const ids = available.filter((card) => !claimed.has(card.id) && matches(category, card)).map((card) => card.id);
      ids.forEach((id) => claimed.add(id));
      return { key: category.key, label: category.label, cardIds: ids };
    }),
  }));
  const others = available.filter((card) => !claimed.has(card.id)).map((card) => card.id);
  if (others.length) stages[stages.length - 1].categories.push({ ...OTHER_CATEGORY, cardIds: others });
  return stages
    .map((stage) => ({
      ...stage,
      categories: stage.categories
        .filter((category) => category.cardIds.length)
        .map((category) => ({
          ...category,
          count: category.cardIds.length,
          cardIdsText: category.cardIds.join(","),
        })),
    }))
    .filter((stage) => stage.categories.length);
}

module.exports = { TRAINING_STAGES, groupTrainingLibrary };
