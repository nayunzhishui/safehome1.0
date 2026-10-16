// 删除申请审核（研究者工作台“管理”页，督导和总管理可用）：
// 受理时选删除范围 → 预览会影响多少条 → 批准 → 试运行 → 正式执行。
// 正式执行要服务器打开执行开关、负责人确认数据保存期限；生产还要两人批准，其中一人是总管理。
const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();
const STATUS_FILTERS = [
  { id: "pending", label: "待受理" },
  { id: "processing", label: "处理中" },
  { id: "completed", label: "已完成" },
  { id: "rejected", label: "已退回" },
  { id: "", label: "全部" },
];
const STATUS_LABELS = { pending: "待受理", processing: "处理中", completed: "已完成", rejected: "已退回", cancelled: "本人已撤回" };
// 与 content/privacy_retention_policy.json 的 scope_labels 一致。
const SCOPE_LABELS = {
  account_identity: "账号与身份标识",
  participant_records: "参与者记录与支持性测评",
  feedback_and_training: "反馈、训练与成长记录",
  messages_and_notifications: "站内消息与通知记录",
  relationship_pilot: "关系探索试点资料",
  research_outputs: "研究视图与可导出衍生记录",
  therapeutic_assessment: "治疗性评估协作问题、反馈版本与行动记录",
};
const ACTION_LABELS = {
  start_processing: "受理",
  reject: "退回",
  return_to_pending: "放回待受理",
  participant_appeal: "本人补充说明后重新提交",
  participant_cancel: "本人撤回",
};

function timeText(value) {
  const parsed = Date.parse(String(value || "").replace(/(\.\d{3})\d+/, "$1"));
  if (!Number.isFinite(parsed)) return String(value || "").slice(0, 16).replace("T", " ");
  const date = new Date(parsed);
  const pad = (number) => String(number).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function decorateDetail(detail) {
  const request = detail.request || {};
  return {
    ...detail,
    request,
    statusText: STATUS_LABELS[request.status] || request.status,
    createdText: timeText(request.created_at),
    scopeText: (request.handling_scope || []).map((key) => SCOPE_LABELS[key] || key).join("、"),
    trail: (detail.actions || []).map((item) => `${timeText(item.created_at)} · ${ACTION_LABELS[item.action] || "其他处理"}${item.note ? `：${item.note}` : ""}`),
    approvalCount: (detail.approvals || []).filter((item) => item.decision === "approved").length,
    executionRows: (detail.executions || []).map((item) => `${timeText(item.started_at)} · ${item.mode === "dry_run" ? "试运行" : "正式执行"} · ${item.status}`),
  };
}

Component({
  data: {
    filters: STATUS_FILTERS,
    status: "pending",
    items: [],
    total: 0,
    loading: false,
    error: "",
    detail: null,
    scopes: [],
    note: "",
    preview: null,
    busy: "",
    resultText: "",
  },

  lifetimes: {
    attached() {
      this.load(true);
    },
  },

  methods: {
    async load(reset) {
      const page = reset ? 1 : Math.floor(this.data.items.length / 20) + 1;
      this.setData({ loading: true, error: "" });
      try {
        const params = { page, page_size: 20 };
        if (this.data.status) params.status = this.data.status;
        const result = await api.listPrivacyRequestsForReview(params);
        const items = (result.items || []).map((item) => ({
          ...item,
          statusText: STATUS_LABELS[item.status] || item.status,
          createdText: timeText(item.created_at),
          shortId: String(item.user_id || "").slice(-6),
        }));
        this.setData({ items: reset ? items : this.data.items.concat(items), total: Number(result.total || 0), loading: false });
      } catch (error) {
        this.setData({ loading: false, error: error.message || "删除申请暂时读不出来。" });
      }
    },

    pickFilter(event) {
      const id = event.currentTarget.dataset.id || "";
      if (id === this.data.status) return;
      this.setData({ status: id, detail: null });
      this.load(true);
    },

    loadMore() {
      if (!this.data.loading && this.data.items.length < this.data.total) this.load(false);
    },

    async openRequest(event) {
      const id = event.currentTarget.dataset.id;
      if (!id || this.data.busy) return;
      this.setData({ busy: "open", preview: null, resultText: "", note: "" });
      try {
        const detail = decorateDetail(await api.getPrivacyRequestForReview(id));
        const scopes = (detail.request.handling_scope || []).length ? detail.request.handling_scope : Object.keys(SCOPE_LABELS);
        this.setData({ detail, scopes: this.scopeChips(scopes) });
      } catch (error) {
        wx.showToast({ title: error.message || "申请详情读不出来", icon: "none" });
      } finally {
        this.setData({ busy: "" });
      }
    },

    closeDetail() {
      this.setData({ detail: null, preview: null, resultText: "" });
    },

    scopeChips(selected) {
      return Object.keys(SCOPE_LABELS).map((key) => ({ key, label: SCOPE_LABELS[key], selected: selected.includes(key) }));
    },

    toggleScope(event) {
      const key = event.currentTarget.dataset.key;
      this.setData({ scopes: this.data.scopes.map((item) => (item.key === key ? { ...item, selected: !item.selected } : item)) });
    },

    onNoteInput(event) {
      this.setData({ note: event.detail.value || "" });
    },

    async refreshDetail() {
      const detail = decorateDetail(await api.getPrivacyRequestForReview(this.data.detail.request.id));
      this.setData({ detail });
      this.load(true);
    },

    async transition(event) {
      const action = event.currentTarget.dataset.action;
      const detail = this.data.detail;
      if (!detail || this.data.busy) return;
      const note = this.data.note.trim();
      const scope = this.data.scopes.filter((item) => item.selected).map((item) => item.key);
      if (action === "start_processing" && !scope.length) {
        wx.showToast({ title: "请至少选一个删除范围", icon: "none" });
        return;
      }
      if (action !== "start_processing" && !note) {
        wx.showToast({ title: "请先写下原因，参与者会看到退回提示", icon: "none" });
        return;
      }
      this.setData({ busy: action });
      try {
        await api.transitionPrivacyRequest(detail.request.id, { action, scope, note }, `privacy-${action}-${detail.request.id}-${Date.now()}`);
        this.setData({ note: "", preview: null, resultText: "" });
        await this.refreshDetail();
        wx.showToast({ title: "已更新", icon: "success" });
      } catch (error) {
        wx.showToast({ title: error.message || "没有更新成功", icon: "none" });
      } finally {
        this.setData({ busy: "" });
      }
    },

    async loadPreview() {
      const detail = this.data.detail;
      if (!detail || this.data.busy) return;
      this.setData({ busy: "preview", resultText: "" });
      try {
        const preview = await api.previewPrivacyRequest(detail.request.id);
        this.setData({ preview: { ...preview, rows: (preview.modules || []).map((item) => `${item.label} · ${item.count} 条`) } });
      } catch (error) {
        wx.showToast({ title: error.message || "预览没有生成", icon: "none" });
      } finally {
        this.setData({ busy: "" });
      }
    },

    async approve() {
      const { detail, preview } = this.data;
      if (!detail || !preview || this.data.busy) return;
      this.setData({ busy: "approve" });
      try {
        await api.approvePrivacyRequest(
          detail.request.id,
          { scope_hash: preview.scope_hash, policy_version: preview.policy_version },
          `privacy-approve-${detail.request.id}-${preview.scope_hash}`,
        );
        await this.refreshDetail();
        wx.showToast({ title: "已批准", icon: "success" });
      } catch (error) {
        wx.showToast({ title: error.message || "批准没有成功", icon: "none" });
      } finally {
        this.setData({ busy: "" });
      }
    },

    async execute(event) {
      const dryRun = event.currentTarget.dataset.mode !== "execute";
      const { detail, preview } = this.data;
      if (!detail || !preview || this.data.busy) return;
      if (!dryRun) {
        const confirmed = await new Promise((resolve) => {
          wx.showModal({
            title: "正式删除",
            content: `会删除或匿名化 ${preview.total_affected} 条数据，执行后不能撤销。确定执行吗？`,
            confirmText: "执行",
            success: (result) => resolve(Boolean(result.confirm)),
            fail: () => resolve(false),
          });
        });
        if (!confirmed) return;
      }
      this.setData({ busy: dryRun ? "dry_run" : "execute", resultText: "" });
      try {
        const result = await api.executePrivacyRequest(
          detail.request.id,
          { dry_run: dryRun, expected_version: preview.request_version },
          `privacy-${dryRun ? "dry-run" : "execute"}-${detail.request.id}-${Date.now()}`,
        );
        const status = result.execution && result.execution.status;
        this.setData({ resultText: `${dryRun ? "试运行" : "正式执行"}：${status || "已完成"}` });
        await this.refreshDetail();
      } catch (error) {
        this.setData({ resultText: error.message || "没有执行成功" });
      } finally {
        this.setData({ busy: "" });
      }
    },
  },
});
