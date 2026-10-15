// 账号资格：总管理给用微信登录过的人开、收研究员或督导资格（研究者工作台“管理”页）。
const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();
const PAGE_SIZE = 20;
const ROLE_LABELS = { parent: "普通账号", researcher: "研究员", supervisor: "督导", admin: "总管理" };
const ROLE_FILTERS = [
  { id: "", label: "全部" },
  { id: "researcher", label: "研究员" },
  { id: "supervisor", label: "督导" },
  { id: "parent", label: "普通账号" },
];
// 每种资格下能做的改动；改完对方会被退出登录，重新登录后生效。
const ACTIONS = {
  parent: [{ role: "researcher", label: "开研究员" }, { role: "supervisor", label: "开督导" }],
  researcher: [{ role: "supervisor", label: "改为督导" }, { role: "parent", label: "收回资格" }],
  supervisor: [{ role: "researcher", label: "改为研究员" }, { role: "parent", label: "收回资格" }],
};

function decorate(item) {
  const lastSeen = String(item.last_login_at || item.created_at || "").slice(0, 10);
  return {
    ...item,
    displayName: item.nickname || "没有昵称",
    meta: [ROLE_LABELS[item.role] || item.role, `尾号 ${String(item.id || "").slice(-6)}`, lastSeen ? `最近 ${lastSeen}` : ""]
      .filter(Boolean)
      .join(" · "),
    actions: item.grantable ? ACTIONS[item.role] || [] : [],
    note: !item.grantable && item.role !== "admin" ? "不是微信登录的账号，这里改不了。" : "",
  };
}

function confirmText(item, role) {
  if (role === "parent") return `收回「${item.displayName}」的${ROLE_LABELS[item.role]}资格？`;
  return `让「${item.displayName}」成为${ROLE_LABELS[role]}？`;
}

Component({
  data: {
    filters: ROLE_FILTERS,
    roleFilter: "",
    query: "",
    items: [],
    total: 0,
    loading: false,
    error: "",
    busyId: "",
  },

  lifetimes: {
    attached() {
      this.load(true);
    },
    detached() {
      if (this.searchTimer) clearTimeout(this.searchTimer);
    },
  },

  methods: {
    async load(reset) {
      const offset = reset ? 0 : this.data.items.length;
      const requestId = this.requestId = (this.requestId || 0) + 1;
      this.setData({ loading: true, error: "" });
      try {
        const params = { limit: PAGE_SIZE, offset };
        if (this.data.query) params.q = this.data.query;
        if (this.data.roleFilter) params.role = this.data.roleFilter;
        const result = await api.listAccounts(params);
        if (requestId !== this.requestId) return;
        const items = (result.items || []).map(decorate);
        this.setData({
          items: reset ? items : this.data.items.concat(items),
          total: Number(result.total || 0),
          loading: false,
        });
      } catch (error) {
        if (requestId !== this.requestId) return;
        this.setData({ loading: false, error: error.message || "账号列表暂时读不出来，请稍后再试。" });
      }
    },

    onQueryInput(event) {
      this.setData({ query: String(event.detail.value || "").trim() });
      if (this.searchTimer) clearTimeout(this.searchTimer);
      this.searchTimer = setTimeout(() => this.load(true), 400);
    },

    pickFilter(event) {
      const id = event.currentTarget.dataset.id || "";
      if (id === this.data.roleFilter) return;
      this.setData({ roleFilter: id });
      this.load(true);
    },

    loadMore() {
      if (!this.data.loading && this.data.items.length < this.data.total) this.load(false);
    },

    changeRole(event) {
      const { id, role } = event.currentTarget.dataset;
      const item = this.data.items.find((entry) => entry.id === id);
      if (!item || this.data.busyId || !item.actions.some((action) => action.role === role)) return;
      wx.showModal({
        title: "改账号资格",
        content: `${confirmText(item, role)}对方会被退出登录，重新登录后生效。`,
        confirmText: "确定",
        success: (result) => {
          if (result.confirm) this.applyRole(item, role);
        },
      });
    },

    async applyRole(item, role) {
      this.setData({ busyId: item.id });
      try {
        const result = await api.changeAccountRole(item.id, role);
        const updated = decorate(result.account);
        this.setData({
          busyId: "",
          items: this.data.items.map((entry) => (entry.id === item.id ? updated : entry)),
        });
        wx.showToast({ title: "已改好", icon: "success" });
      } catch (error) {
        this.setData({ busyId: "" });
        wx.showToast({ title: error.message || "没有改成功，请稍后再试", icon: "none" });
      }
    },
  },
});
