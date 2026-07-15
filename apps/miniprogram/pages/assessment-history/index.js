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
  return {
    ...item,
    worksheetTitle: item.worksheet_title || "支持性测评",
    createdAtText: formatDate(item.created_at),
    summaryText: item.result_summary || "已保存本次测评记录。",
    dimensionCount: dimensions.length,
    dimensionText: dimensions.length ? `${dimensions.length} 个维度` : "查看完整结果",
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
    const id = event.currentTarget.dataset.id || "";
    const worksheetId = event.currentTarget.dataset.worksheetId || "";
    if (!id) return;
    wx.navigateTo({
      url: `/pages/assessment-result/index?id=${encodeURIComponent(id)}&worksheet_id=${encodeURIComponent(worksheetId)}`,
    });
  },

  goAssessment() {
    wx.navigateTo({ url: "/pages/assessment/index" });
  },
});
