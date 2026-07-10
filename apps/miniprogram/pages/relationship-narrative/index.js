const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

Page({
  data: { loading: true, errorMessage: "", narrative: null, noteRows: [], taskRows: [] },
  onLoad(options) {
    this.loadNarrative(decodeURIComponent(options.id || ""));
  },
  async loadNarrative(id) {
    try {
      const narrative = await api.getRelationshipNarrative(id);
      this.setData({
        loading: false,
        narrative,
        noteRows: narrative.draft.researcher_notes || [],
        taskRows: narrative.draft.online_task_materials || [],
      });
    } catch (error) {
      this.setData({ loading: false, errorMessage: error.message || "手记尚未确认或无法读取。" });
    }
  },
});
