const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

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
        taskRows: narrative.draft.online_task_materials || [],
      });
    } catch (error) {
      this.setData({ loading: false, errorMessage: error.message || "手记尚未确认或无法读取。" });
    }
  },
  retryLoad() {
    this.loadNarrative(this.data.narrativeId);
  },
});
