const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();
const TASK_TYPE_LABELS = {
  relationship_drawing: "关系感受绘画",
  sentence_completion: "情境句子补全",
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
      this.setData({
        loading: false,
        narrative,
        isConfirmed: narrative.status === "confirmed",
        isResearcherView: narrative.audience === "researcher",
        noteRows: narrative.draft.researcher_notes || [],
        taskRows: (narrative.draft.online_task_materials || []).map((item) => ({ ...item, taskTypeLabel: taskTypeLabel(item.task_type) })),
      });
    } catch (error) {
      this.setData({ loading: false, errorMessage: error.message || "手记尚未确认或无法读取。" });
    }
  },
  retryLoad() {
    this.loadNarrative(this.data.narrativeId);
  },
});
