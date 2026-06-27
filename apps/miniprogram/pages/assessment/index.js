const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

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
    const config = api.getDebugConfig();
    return `云托管请求失败（102002）。请先打开联调测试页运行 /healthz；如果 /healthz 也失败，请检查 CloudBase 环境和 ${config.containerService} 服务是否正在运行。`;
  }
  return message || fallback;
}

const GROUP_DEFINITIONS = [
  {
    key: "student",
    title: "学生支持性画像",
    subtitle: "当前可填写的项目版支持性测评",
    emptyText: "",
  },
  {
    key: "parent",
    title: "家长支持",
    subtitle: "家长量表和亲子支持内容，开放前需人工复核",
    emptyText: "家长量表目录已在本地准备中，正式开放前会先完成题项、计分和边界说明复核。",
  },
  {
    key: "adult",
    title: "成人自助",
    subtitle: "情绪觉察、认知灵活和练习记录类内容",
    emptyText: "成人自助内容会在家长优先任务之后逐步开放。",
  },
  {
    key: "pending",
    title: "待审核内容",
    subtitle: "示例、草稿或需伦理复核的内容，当前不可填写",
    emptyText: "",
  },
];

function includesAny(text, keywords) {
  return keywords.some((keyword) => text.includes(keyword));
}

function getThemeLabel(item) {
  const text = `${item.id || ""} ${item.display_title || ""} ${item.source_title || ""} ${item.category || ""}`;
  if (includesAny(text, ["亲子", "父母", "家长", "养育"])) return "家长支持";
  if (includesAny(text, ["目标", "进展", "计划"])) return "目标与进展";
  if (includesAny(text, ["正念", "觉察", "情绪", "三成分", "反射弧"])) return "情绪觉察";
  if (includesAny(text, ["认知", "箭头"])) return "认知灵活";
  if (includesAny(text, ["行为", "练习", "身体"])) return "练习记录";
  if (includesAny(text, ["焦虑", "抑郁", "暴露", "睡眠"])) return "需谨慎复核";
  return item.category || "综合支持";
}

function getGroupKey(item, normalizedItem) {
  const text = `${item.id || ""} ${item.display_title || ""} ${item.source_title || ""} ${item.category || ""}`;
  if (normalizedItem.is_student_profile) return "student";
  if (includesAny(text, ["亲子", "父母", "家长", "养育"])) return "parent";
  if (normalizedItem.is_reference || includesAny(text, ["焦虑", "抑郁", "暴露", "睡眠"])) return "pending";
  return "adult";
}

function getReviewLabel(item, isReference) {
  if (item.enabled_for_user !== false) return "可填写";
  if (isReference) return "示例未开放";
  if (item.review_status === "needs_ethics_review") return "需伦理复核";
  if (item.review_status === "draft_only") return "草稿待审核";
  if (item.review_status === "pilot_review_required") return "试点前复核";
  return "待人工审核";
}

function buildAssessmentSections(items) {
  const groups = GROUP_DEFINITIONS.map((definition) => ({ ...definition, items: [] }));
  (items || []).forEach((item) => {
    const isStudentProfile = item.id === "student_profile_v1" || item.category === "学生画像";
    const isReference = !!item.is_reference || item.category === "示例参考";
    const normalizedItem = {
      ...item,
      display_title: isStudentProfile ? item.display_title : cleanDisplayTitle(item.display_title || item.source_title),
      instructions: cleanDisplayText(item.instructions),
      is_student_profile: isStudentProfile,
      is_reference: isReference,
      is_enabled_for_user: item.enabled_for_user !== false,
      source_label: isStudentProfile ? "支持性测评" : isReference ? "示例参考" : "电子版简化记录",
      review_label: getReviewLabel(item, isReference),
      topic_label: getThemeLabel(item),
      action_text: item.enabled_for_user === false ? "暂不开放" : isStudentProfile ? "开始测一测" : isReference ? "查看示例" : "填写记录",
    };
    const group = groups.find((entry) => entry.key === getGroupKey(item, normalizedItem)) || groups[groups.length - 1];
    group.items.push(normalizedItem);
  });
  return groups.filter((group) => group.items.length || group.emptyText);
}

Page({
  data: {
    loading: true,
    errorMessage: "",
    boundaryNotice: "",
    categories: [],
    recentResults: [],
    infoItems: [
      {
        label: "内容来源",
        value: "项目内容库与已授权工作表",
      },
      {
        label: "结果用途",
        value: "用于自我观察、阶段性画像和练习记录",
      },
      {
        label: "数据保存",
        value: "提交后保存为本次测一测记录",
      },
      {
        label: "边界提示",
        value: "只作支持性参考，不替代专业帮助",
      },
    ],
  },

  onLoad() {
    this.loadAssessments();
  },

  onShow() {
    this.loadRecentResults();
  },

  async loadAssessments() {
    this.setData({ loading: true, errorMessage: "" });
    try {
      const result = await api.listAssessments();
      this.setData({
        loading: false,
        boundaryNotice: result.boundary_notice || "",
        categories: buildAssessmentSections(result.items || []),
      });
    } catch (error) {
      this.setData({
        loading: false,
        errorMessage: formatRequestError(error, "测一测内容获取失败，请确认 backend 是否已启动。"),
      });
    }
  },

  async loadRecentResults() {
    try {
      const result = await api.listAssessmentResults({ limit: 3 });
      this.setData({ recentResults: result.items || [] });
    } catch (error) {
      this.setData({ recentResults: [] });
    }
  },

  openAssessmentEntry(event) {
    const id = event.currentTarget.dataset.id;
    const enabled = event.currentTarget.dataset.enabled !== "false";
    if (!id) return;
    if (!enabled) {
      wx.showToast({
        title: "内容仍在审核中",
        icon: "none",
      });
      return;
    }
    wx.navigateTo({
      url: `/pages/assessment-detail/index?id=${encodeURIComponent(id)}`,
    });
  },

  openIntegrationTest() {
    wx.navigateTo({ url: "/pages/integration-test/index" });
  },
});
