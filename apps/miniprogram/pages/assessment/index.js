const { createSafeHomeApi } = require("../../services/api");
const { isLoggedIn, requireLogin } = require("../../utils/authGuard");

const api = createSafeHomeApi();

const AUDIENCE_TABS = [
  { key: "all", label: "全部", description: "查看当前可填写内容" },
  { key: "student", label: "学生自助", description: "学习、压力和支持画像" },
  { key: "parent", label: "家长自助", description: "亲子理解和陪伴练习" },
  { key: "adult", label: "成人自助", description: "情绪、觉察和自我支持" },
];

const NODE_LABELS = {
  integrated_profile: "阶段性画像",
  awareness: "觉察",
  reaction: "反应",
  acceptance: "接纳",
  fusion: "融合",
  transformation: "转化",
  behavior: "行为",
  resource: "资源",
  outcome: "结果",
  reflection: "理解",
  motivation: "动机",
};

function cleanDisplayText(value) {
  return String(value || "")
    .replace(/请按照原工作表内容填写。当前电子版保留原文标题和来源，完整题项将按原 PDF 逐页补录。/g, "当前页面是电子版简化记录，先保留最小填写项。你可以按当前问题填写，完整内容后续再补充。")
    .replace(/请按照原工作表内容填写。/g, "请按当前问题填写。")
    .replace(/原工作表/g, "测评内容")
    .replace(/原表/g, "当前内容")
    .replace(/\.pdf/gi, "")
    .replace(/PDF/g, "内容");
}

function cleanDisplayTitle(value) {
  return cleanDisplayText(value).replace(/^工作表\d+(?:\.\d+)?[：:\s]*/, "");
}

function formatRequestError(error, fallback) {
  const code = String(error && error.code ? error.code : "");
  const message = error && error.message ? error.message : "";
  if (code === "102002" || message.includes("102002")) {
    console.warn("[safehome assessment] 云托管 102002", api.getDebugConfig());
    return "现在没能连上，请检查网络后再试一次。如果多次失败，可以稍后再来。";
  }
  return message || fallback;
}

function getReviewLabel(item) {
  if (item.enabled_for_user !== false) return "可填写";
  if (item.review_status === "needs_ethics_review") return "需伦理复核";
  if (item.review_status === "draft_only") return "草稿待审核";
  if (item.review_status === "pilot_review_required") return "试点前复核";
  return "待人工审核";
}

function getAudienceLabel(audienceClass) {
  const matched = AUDIENCE_TABS.find((item) => item.key === audienceClass);
  return matched ? matched.label : "支持性测评";
}

function normalizeAssessment(item) {
  const isStudentProfile = item.id === "student_profile_v1" || item.category === "学生画像";
  const isReference = !!item.is_reference || item.category === "示例参考";
  const audienceClass = item.audience_class || (isStudentProfile ? "student" : "adult");
  const reflexNode = item.reflex_node || "reflection";
  const sensitiveCategory = item.sensitive_category || "none";
  return {
    ...item,
    audience_class: audienceClass,
    reflex_node: reflexNode,
    sensitive_category: sensitiveCategory,
    display_title: isStudentProfile ? item.display_title : cleanDisplayTitle(item.display_title || item.source_title),
    instructions: cleanDisplayText(item.instructions),
    is_student_profile: isStudentProfile,
    is_reference: isReference,
    is_enabled_for_user: item.enabled_for_user !== false,
    source_label: getAudienceLabel(audienceClass),
    review_label: getReviewLabel(item),
    topic_label: NODE_LABELS[reflexNode] || item.category || "综合支持",
    sensitive_label: sensitiveCategory !== "none" ? "需边界提示" : "非诊断",
    action_text: item.enabled_for_user === false ? "暂不开放" : isStudentProfile ? "开始测一测" : "填写",
    estimated_minutes: Math.max(1, Math.ceil((item.question_count || 0) / 5)),
  };
}

function matchesQuery(item, query) {
  if (!query) return true;
  const text = [
    item.id,
    item.display_title,
    item.source_title,
    item.category,
    item.topic_label,
    item.source_label,
    item.review_label,
    (item.search_keywords || []).join(" "),
  ]
    .join(" ")
    .toLowerCase();
  return text.includes(query.toLowerCase());
}

function buildAssessmentSections(items, activeAudience, query) {
  const filtered = (items || [])
    .map(normalizeAssessment)
    .filter((item) => activeAudience === "all" || item.audience_class === activeAudience)
    .filter((item) => matchesQuery(item, query));

  const nodeMap = {};
  filtered.forEach((item) => {
    const key = item.reflex_node || "reflection";
    if (!nodeMap[key]) {
      nodeMap[key] = {
        key,
        title: NODE_LABELS[key] || "综合支持",
        subtitle: "按量表功能节点分组",
        emptyText: "",
        items: [],
      };
    }
    nodeMap[key].items.push(item);
  });

  const sections = Object.values(nodeMap);
  if (!sections.length) {
    return [
      {
        key: "empty",
        title: "没有匹配内容",
        subtitle: "换一个分类或关键词再看",
        emptyText: "当前条件下没有可显示的测评内容。",
        items: [],
      },
    ];
  }
  return sections;
}

function formatRecentResult(item) {
  const isProfile = item && (item.worksheet_id === "student_profile_v1" || item.category === "学生画像");
  return {
    ...item,
    is_profile: isProfile,
    badge_text: isProfile ? "阶段性画像" : "测评记录",
    worksheet_title: cleanDisplayTitle(item.worksheet_title || "测一测记录"),
    result_summary: cleanDisplayText(item.result_summary || "已保存本次填写。"),
  };
}

Page({
  data: {
    loading: true,
    errorMessage: "",
    boundaryNotice: "",
    tabs: AUDIENCE_TABS,
    activeAudience: "parent",
    searchKeyword: "",
    allAssessments: [],
    categories: [],
    recentResults: [],
    recentLoginTip: "",
    infoItems: [
      { label: "内容来源", value: "项目内容库与已授权工作表" },
      { label: "结果用途", value: "用于自我观察、阶段性画像和练习记录" },
      { label: "数据保存", value: "提交后保存为本次测一测记录" },
      { label: "边界提示", value: "只作支持性参考，不替代专业帮助" },
    ],
  },

  onLoad() {
    this.loadAssessments();
  },

  onShow() {
    this.loadRecentResults();
  },

  refreshVisibleAssessments() {
    this.setData({
      categories: buildAssessmentSections(this.data.allAssessments, this.data.activeAudience, this.data.searchKeyword),
    });
  },

  async loadAssessments() {
    this.setData({ loading: true, errorMessage: "" });
    try {
      const result = await api.listAssessments();
      this.setData({
        loading: false,
        boundaryNotice: result.boundary_notice || "",
        allAssessments: result.items || [],
      });
      this.refreshVisibleAssessments();
    } catch (error) {
      this.setData({
        loading: false,
        errorMessage: formatRequestError(error, "测一测内容暂时没能加载出来，请检查网络后再试一次。"),
      });
    }
  },

  async loadRecentResults() {
    if (!isLoggedIn()) {
      this.setData({
        recentResults: [],
        recentLoginTip: "登录后会在这里显示最近的测一测记录。",
      });
      return;
    }
    try {
      const result = await api.listAssessmentResults({ limit: 3 });
      this.setData({
        recentResults: (result.items || []).map(formatRecentResult),
        recentLoginTip: "",
      });
    } catch (error) {
      this.setData({
        recentResults: [],
        recentLoginTip: "最近记录暂时没能读取，请稍后再试。",
      });
    }
  },

  switchAudience(event) {
    const key = event.currentTarget.dataset.key || "all";
    this.setData({ activeAudience: key });
    this.refreshVisibleAssessments();
  },

  onSearchInput(event) {
    this.setData({ searchKeyword: event.detail.value || "" });
    this.refreshVisibleAssessments();
  },

  clearSearch() {
    this.setData({ searchKeyword: "" });
    this.refreshVisibleAssessments();
  },

  openAssessmentEntry(event) {
    if (!requireLogin({
      redirectUrl: "/pages/assessment/index",
      message: "请先登录后再填写测评。",
    })) {
      return;
    }
    const id = event.currentTarget.dataset.id;
    const enabled = event.currentTarget.dataset.enabled !== "false";
    if (!id) return;
    if (!enabled) {
      wx.showToast({ title: "内容仍在审核中", icon: "none" });
      return;
    }
    wx.navigateTo({
      url: `/pages/assessment-detail/index?id=${encodeURIComponent(id)}`,
    });
  },

  openRecentResult(event) {
    const id = event.currentTarget.dataset.id || "";
    const worksheetId = event.currentTarget.dataset.worksheetId || "";
    if (!id) return;
    wx.navigateTo({
      url: `/pages/assessment-result/index?id=${encodeURIComponent(id)}&worksheet_id=${encodeURIComponent(worksheetId)}`,
    });
  },

  goLogin() {
    requireLogin({
      redirectUrl: "/pages/assessment/index",
      message: "登录后可以查看自己的测评记录。",
    });
  },

  openIntegrationTest() {
    wx.navigateTo({ url: "/pages/integration-test/index" });
  },
});
