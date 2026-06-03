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
    return "云托管请求失败（102002）。请先打开联调测试页运行 /healthz；如果 /healthz 也失败，请检查 CloudBase 环境和 flask-gh3l 服务是否正在运行。";
  }
  return message || fallback;
}

function groupByCategory(items) {
  const groups = [];
  (items || []).forEach((item) => {
    const isStudentProfile = item.id === "student_profile_v1" || item.category === "学生画像";
    const isReference = !!item.is_reference || item.category === "示例参考";
    const normalizedItem = {
      ...item,
      display_title: isStudentProfile ? item.display_title : cleanDisplayTitle(item.display_title || item.source_title),
      instructions: cleanDisplayText(item.instructions),
      is_student_profile: isStudentProfile,
      is_reference: isReference,
      source_label: isStudentProfile ? "支持性测评" : isReference ? "示例参考" : "电子版简化记录",
      action_text: isStudentProfile ? "开始测一测" : isReference ? "查看示例" : "填写记录",
    };
    const category = item.category || "其他";
    let group = groups.find((entry) => entry.category === category);
    if (!group) {
      group = { category, items: [] };
      groups.push(group);
    }
    group.items.push(normalizedItem);
  });
  return groups;
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
        categories: groupByCategory(result.items || []),
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
    if (!id) return;
    wx.navigateTo({
      url: `/pages/assessment-detail/index?id=${encodeURIComponent(id)}`,
    });
  },

  openIntegrationTest() {
    wx.navigateTo({ url: "/pages/integration-test/index" });
  },
});
