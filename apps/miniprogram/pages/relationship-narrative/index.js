const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();
const TASK_TYPE_LABELS = {
  relationship_drawing: "关系隐喻绘画",
  sentence_completion: "情境句子补全",
};
// 句子补全没有画外音，原先会直接显示 pending_review；参与者两种复核都只看到“等待人工复核”，不暴露优先级。
const REVIEW_TEXT = {
  pending_review: "已提交，等待人工复核",
  priority_review: "已提交，等待人工复核",
  reviewed: "研究者已查看",
};
const RESEARCHER_REVIEW_TEXT = {
  pending_review: "待复核",
  priority_review: "优先复核",
  reviewed: "已复核",
};
function taskTypeLabel(value) { return TASK_TYPE_LABELS[value] || "项目任务"; }

Page({
  data: { loading: true, errorMessage: "", narrativeId: "", narrative: null, noteRows: [], taskRows: [] },
  onLoad(options) {
    const narrativeId = decodeURIComponent(options.id || "");
    this.setData({ narrativeId });
    this.loadNarrative(narrativeId);
  },
  async loadNarrative(id) {
    this.setData({ loading: true, errorMessage: "" });
    try {
      const narrative = await api.getRelationshipNarrative(id);
      const isResearcherView = narrative.audience === "researcher";
      const reviewText = isResearcherView ? RESEARCHER_REVIEW_TEXT : REVIEW_TEXT;
      this.setData({
        loading: false,
        narrative,
        isConfirmed: narrative.status === "confirmed",
        isResearcherView,
        noteRows: narrative.draft.researcher_notes || [],
        taskRows: (narrative.draft.online_task_materials || []).map((item, index) => ({
          ...item,
          rowKey: `${item.task_type}-${index}`,
          taskTypeLabel: taskTypeLabel(item.task_type),
          detailText: item.narration || reviewText[item.review_status] || "已提交",
        })),
      });
    } catch (error) {
      this.setData({ loading: false, errorMessage: error.message || "手记尚未确认或无法读取。" });
    }
  },
  retryLoad() {
    this.loadNarrative(this.data.narrativeId);
  },
});
