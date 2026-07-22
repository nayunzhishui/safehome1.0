const { createSafeHomeApi } = require("../../services/api");
const { requireLogin } = require("../../utils/authGuard");
const { buildErrorDiagnostic, copyErrorDiagnostic } = require("../../utils/errorDiagnostics");

const api = createSafeHomeApi();
const PAGE_SIZE = 50;

function formatDate(value) {
  if (!value) return "时间待补充";
  return String(value).slice(0, 16).replace("T", " ");
}

function formatCheckin(item) {
  const hasBefore = item.emotion_before !== null && item.emotion_before !== undefined && item.emotion_before !== "";
  const hasAfter = item.emotion_after !== null && item.emotion_after !== undefined && item.emotion_after !== "";
  const before = hasBefore ? Number(item.emotion_before) : null;
  const after = hasAfter ? Number(item.emotion_after) : null;
  const hasChange = hasBefore && hasAfter && Number.isFinite(before) && Number.isFinite(after);
  return {
    ...item,
    cardTitle: item.card_title || item.card_id || "训练卡",
    createdAtText: formatDate(item.created_at),
    statusText: item.completed ? "已完成" : "已记录",
    changeText: hasChange ? `练习前 ${before} · 练习后 ${after}` : "本次未记录前后强度",
    helpfulnessText: item.helpfulness_rating ? `帮助程度 ${item.helpfulness_rating}` : "",
  };
}

Page({
  data: {
    loading: true,
    loadingMore: false,
    errorMessage: "",
    errorDiagnostic: null,
    items: [],
    page: 1,
    total: 0,
    hasMore: false,
  },

  onLoad() {
    if (!requireLogin({
      redirectUrl: "/pages/training-history/index",
      message: "请先登录后再查看训练记录。",
    })) {
      this.setData({ loading: false });
      return;
    }
    this.loadPage(1);
  },

  async loadPage(page) {
    const append = page > 1;
    this.setData({ loading: !append, loadingMore: append, errorMessage: append ? this.data.errorMessage : "", errorDiagnostic: append ? this.data.errorDiagnostic : null });
    try {
      const result = await api.listCheckins({ page, page_size: PAGE_SIZE, completed: true });
      const nextItems = (result.items || []).map(formatCheckin);
      this.setData({
        loading: false,
        loadingMore: false,
        errorMessage: "",
        errorDiagnostic: null,
        items: append ? this.data.items.concat(nextItems) : nextItems,
        page: result.page || page,
        total: Number(result.total || 0),
        hasMore: Boolean(result.has_more),
      });
    } catch (error) {
      this.setData({
        loading: false,
        loadingMore: false,
        errorMessage: error.message || "训练记录暂时没能加载，请检查网络后再试一次。",
        errorDiagnostic: buildErrorDiagnostic(error),
      });
    }
  },

  async copyDiagnostic() {
    try {
      await copyErrorDiagnostic(this.data.errorDiagnostic || {});
      wx.showToast({ title: "诊断信息已复制", icon: "success" });
    } catch (error) {
      wx.showToast({ title: "复制失败", icon: "none" });
    }
  },

  loadMore() {
    if (!this.data.hasMore || this.data.loadingMore) return;
    this.loadPage(this.data.page + 1);
  },

  retry() {
    this.loadPage(this.data.items.length ? this.data.page + 1 : 1);
  },

  openCard(event) {
    const cardId = event.currentTarget.dataset.cardId || "";
    if (!cardId) return;
    wx.navigateTo({ url: `/pages/training-card/index?card_ids=${encodeURIComponent(cardId)}&mode=repeat` });
  },

  goTraining() {
    wx.switchTab({ url: "/pages/training/index" });
  },
});
