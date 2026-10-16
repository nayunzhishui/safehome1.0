// 研究方法（研究者工作台“分析”页）：看方法登记的状态，运行机器自检；同步登记版本只有总管理能做。
// 自检只查结构，不读真实结局数据，也不代表正式冻结或签字。
const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi({ defaultHeaders: { "X-SafeHome-Researcher-Workspace": "1" } });
const STATUS_LABELS = {
  draft_before_freeze: "冻结前草稿",
  machine_structure_complete_human_freeze_pending: "机器检查已完成，等人工确认冻结",
};
const BLOCKER_LABELS = { unique_primary_outcome: "还没定唯一的主要结局指标" };

Component({
  properties: {
    owner: { type: Boolean, value: false },
  },

  data: {
    config: null,
    versionId: "",
    result: null,
    busy: "",
    error: "",
  },

  lifetimes: {
    attached() {
      this.load();
    },
  },

  methods: {
    async load() {
      this.setData({ error: "" });
      try {
        const [config, versions] = await Promise.all([api.getResearchMethodologyConfig(), api.listResearchMethodologyVersions()]);
        const latest = (versions.items || [])[0];
        this.setData({
          config: { ...config, statusText: STATUS_LABELS[config.status] || config.status },
          versionId: latest ? latest.id : "",
        });
      } catch (error) {
        this.setData({ error: error.message || "研究方法暂时读不出来。服务器可能没打开研究方法开关。" });
      }
    },

    async sync() {
      if (this.data.busy) return;
      this.setData({ busy: "sync" });
      try {
        const version = await api.syncResearchMethodologyVersion();
        this.setData({ versionId: version.id });
        wx.showToast({ title: "已同步", icon: "success" });
      } catch (error) {
        wx.showToast({ title: error.message || "没有同步成功", icon: "none" });
      } finally {
        this.setData({ busy: "" });
      }
    },

    async runChecks() {
      if (this.data.busy || !this.data.versionId) return;
      this.setData({ busy: "checks" });
      try {
        const result = await api.runResearchMethodologyChecks(this.data.versionId);
        const checks = Object.entries(result.hard_checks || {});
        this.setData({
          result: {
            statusText: STATUS_LABELS[result.status] || result.status,
            passedText: `机器检查 ${checks.filter(([, passed]) => passed).length}/${checks.length} 项通过`,
            failed: checks.filter(([, passed]) => !passed).map(([key]) => key),
            blockers: (result.unresolved_blockers || []).map((key) => BLOCKER_LABELS[key] || key),
          },
        });
      } catch (error) {
        wx.showToast({ title: error.message || "自检没有运行成功", icon: "none" });
      } finally {
        this.setData({ busy: "" });
      }
    },
  },
});
