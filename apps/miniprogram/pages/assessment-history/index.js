const { createSafeHomeApi } = require("../../services/api");
const { requireLogin } = require("../../utils/authGuard");

const api = createSafeHomeApi();
const PAGE_SIZE = 50;

function formatDate(value) {
  if (!value) return "时间待补充";
  return String(value).slice(0, 16).replace("T", " ");
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
    const append = page > 1;
    this.setData({
      loading: !append,
      loadingMore: append,
      errorMessage: append ? this.data.errorMessage : "",
    });
    try {
      const result = await api.listAssessmentResults({ page, page_size: PAGE_SIZE });
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
    const id = event.detail && event.detail.id ? event.detail.id : "";
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
