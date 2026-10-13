const { createSafeHomeApi } = require("../../services/api");
const { requireLogin, captureAuthSession, isCurrentAuthSession } = require("../../utils/authGuard");

const api = createSafeHomeApi();
const PAGE_SIZE = 50;

// “10月10日 20:40”；读不到时间时显示占位。
function formatDate(value) {
  const matched = String(value || "").match(/^(\d{4})-(\d{2})-(\d{2})(?:[T\s](\d{2}):(\d{2}))?/);
  if (!matched) return "时间待补充";
  const day = `${Number(matched[2])}月${Number(matched[3])}日`;
  return matched[4] ? `${day} ${matched[4]}:${matched[5]}` : day;
}

function formatResult(item) {
  const scores = item.scores || {};
  const dimensions = Array.isArray(scores.dimensions) ? scores.dimensions : [];
  const worksheetTitle = item.worksheet_title || "支持性测评";
  const createdAtText = formatDate(item.created_at);
  const summaryText = item.result_summary || "已保存本次测评记录。";
  const dimensionText = dimensions.length ? `${dimensions.length} 个维度` : "";
  return {
    ...item,
    worksheetTitle,
    createdAtText,
    summaryText,
    dimensionCount: dimensions.length,
    dimensionText,
    rowMeta: `${createdAtText} · 查看结果`,
    cardItem: {
      id: item.id,
      display_title: worksheetTitle,
      topic_label: createdAtText,
      meta_text: dimensionText ? `${createdAtText} · ${dimensionText}` : createdAtText,
      question_count: dimensions.length,
      estimated_minutes: 0,
      instructions: summaryText,
      action_text: "查看",
      is_enabled_for_user: true,
    },
  };
}

Page({
  onShow() {
    this._hidden = false;
    if (this._readSession && !isCurrentAuthSession(this._readSession)) {
      this.setData({ items: [], total: 0, hasMore: false });
      this.loadPage(1);
    } else if ((this.data.loading || this.data.loadingMore) && this._readSession) { this.loadPage(1); }
  },
  onHide() { this._hidden = true; },
  onUnload() { this._consentDisposed = true; this._hidden = true; },
  data: {
    loading: true,
    loadingMore: false,
    errorMessage: "",
    items: [],
    page: 1,
    total: 0,
    hasMore: false,
  },

  onLoad() {
    if (!requireLogin({
      redirectUrl: "/pages/assessment-history/index",
      message: "请先登录后再查看测评记录。",
    })) {
      this.setData({ loading: false });
      return;
    }
    this.loadPage(1);
  },

  async loadPage(page) {
    const session = captureAuthSession();
    this._readSession = session;
    const requestId = this._historyRequestId = (this._historyRequestId || 0) + 1;
    const isCurrent = () => !this._hidden && !this._consentDisposed && requestId === this._historyRequestId && isCurrentAuthSession(session);
    const append = page > 1;
    this.setData({
      loading: !append,
      loadingMore: append,
      errorMessage: append ? this.data.errorMessage : "",
    });
    try {
      const result = await api.listAssessmentResults({ page, page_size: PAGE_SIZE });
      if (!isCurrent()) return;
      const nextItems = (result.items || []).map(formatResult);
      this.setData({
        loading: false,
        loadingMore: false,
        errorMessage: "",
        items: append ? this.data.items.concat(nextItems) : nextItems,
        page: result.page || page,
        total: Number(result.total || 0),
        hasMore: Boolean(result.has_more),
      });
    } catch (error) {
      if (!isCurrent()) return;
      this.setData({
        loading: false,
        loadingMore: false,
        errorMessage: error.message || "测评记录暂时没能加载，请检查网络后再试一次。",
      });
    }
  },

  loadMore() {
    if (!this.data.hasMore || this.data.loadingMore) return;
    this.loadPage(this.data.page + 1);
  },

  retry() {
    this.loadPage(this.data.items.length ? this.data.page + 1 : 1);
  },

  openResult(event) {
    const id = (event.detail && event.detail.id) || (event.currentTarget && event.currentTarget.dataset.id) || "";
    const selected = this.data.items.find((item) => item.id === id) || {};
    const worksheetId = selected.worksheet_id || "";
    if (!id) return;
    wx.navigateTo({
      url: `/pages/assessment-result/index?id=${encodeURIComponent(id)}&worksheet_id=${encodeURIComponent(worksheetId)}`,
    });
  },

  goAssessment() {
    wx.navigateTo({ url: "/pages/assessment/index" });
  },
});
