// 测一测列表每行第二行的一句话场景（Figma 651:1365 问卷行）。
// 设计稿给出的 8 条原样采用；其余按各量表自己的指导语缩写成同样长度，不添加指导语之外的说法。
const ASSESSMENT_SCENES = {
  gad7_anxiety: "回想过去两周，下列感受困扰你的频率",
  phq9_cesd10_depression: "回想过去两周，下列情况困扰你的频率",
  who5_wellbeing: "过去两周的身心状态",
  ghq12_general_health: "最近的健康体验",
  mindful_attention_awareness_maas: "日常生活中对当下的注意与觉知",
  fmi_12_mindfulness: "最近一周对当下体验的觉察与接纳",
  cd_risc10_brief_resilience: "遇到困难、变化或压力时的真实感受",
  perceived_social_support_psss: "身边的支持是否与你的情况相符",

  student_profile_v1: "最近的学习压力、支持资源和自我支持",
  emotion_regulation_erq: "通常怎样调节与表达情绪",
  parent_reflective_functioning_prfq: "理解孩子想法、感受和行为的方式",
  self_compassion_scs_cn: "困难时通常怎样对待自己",
  emotional_resilience_11: "日常生活中的心理和行为特点",
  study_engagement_uwes_s_17: "通常的学习体验和感受",
  parental_burnout_pba: "近期承担养育责任时的体验",
  acceptance_action_aaq2: "难受的感受和想法对生活的影响",
  rsca_adolescent_resilience: "面对学习、家庭和同伴压力时的情况",
  academic_buoyancy_4: "最近半年学习中的实际表现",
  afq_y8_avoidance_fusion: "回避难受感受、被想法卷入的程度",
  cfi2_cognitive_flexibility: "遇到难处时换角度、想办法的灵活程度",
  regulatory_focus_general_18: "追求目标、争取进步和避免损失时的倾向",
  hplp_c_health_promoting_lifestyle: "最近一段时间的日常健康习惯",
  swls_life_satisfaction: "对生活的整体感受",
  rfq8_reflective_functioning: "凭第一感觉选出最贴近的描述",
  big_five_bfi_60: "这些句子与你的符合程度",
  attribution_style_student_36: "想象 12 个情境，写下你认为的主要原因",
  epq_emotional_stability_24: "通常的情绪反应和行为情况",
  emotional_intelligence_eis_33: "通常的情绪体验及相关反应",
  regulatory_focus_relationship_18: "亲密关系中靠近目标、表达需要的倾向",
  micro_ysq_relationship_18: "这些描述与近期关系体验的符合程度",
  relationship_initiation_intention_action: "关系中表达、靠近和行动时的真实想法",
  cognitive_curiosity_student: "平时对新知识的好奇程度",
  big_five_tipi_10: "成对特征与你整体的符合程度",
};

const SCENE_MAX_LENGTH = 18;

// 新上线、还没收录的问卷：取指导语第一句，去掉括注和“请根据……作答”的套话；仍过长时只留第一个分句。
function assessmentScene(item) {
  if (!item) return "";
  if (ASSESSMENT_SCENES[item.id]) return ASSESSMENT_SCENES[item.id];
  let text = String(item.instructions || "").split(/[。；]/)[0].replace(/（[^）]*）|\([^)]*\)/g, "").trim();
  const comma = text.indexOf("，");
  if (text.length > SCENE_MAX_LENGTH && comma >= 6) text = text.slice(0, comma);
  text = text.replace(/^请(根据|按照|按)?(自己)?/, "").replace(/(作答|填写)$/, "").trim();
  return text.length > SCENE_MAX_LENGTH ? `${text.slice(0, SCENE_MAX_LENGTH - 1)}…` : text;
}

module.exports = {
  ASSESSMENT_SCENES,
  assessmentScene,
};
