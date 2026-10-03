const { createSafeHomeApi } = require("../../services/api");
const { requireLogin, captureAuthSession, isCurrentAuthSession } = require("../../utils/authGuard");

const api = createSafeHomeApi();
const PAGE_LIMIT = 50;
const NETWORK_CODES = new Set(["network_error", "local_http_error", "ERR_NETWORK"]);

function formatDateTime(value) {
  const source = String(value || "");
  const matched = source.match(/^(\d{4})-(\d{2})-(\d{2})(?:[T\s](\d{2}):(\d{2}))?/);
  if (!matched) {
    return { dateText: "日期待补充", timeText: "时间待补充" };
  }
  return {
    dateText: `${Number(matched[2])}月${Number(matched[3])}日`,
    timeText: matched[4] && matched[5] ? `${matched[4]}:${matched[5]}` : "时间待补充",
  };
}

function normalizeIntensity(value) {
  if (value === null || value === undefined || value === "") return null;
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return null;
  return Math.min(10, Math.max(0, Math.round(numeric)));
}

function formatRecord(item) {
  const timestamp = item.event_time || item.created_at || "";
  const { dateText, timeText } = formatDateTime(timestamp);
  const intensity = normalizeIntensity(item.parent_emotion_intensity);
  return {
    id: item.id || `${timestamp}-${item.scene || "record"}`,
    dateText,
    timeText,
    sceneText: item.scene || "未填写场景",
    descriptionText: item.event_description || item.raw_text || "这次记录暂未填写事件描述。",
    emotionText: item.parent_emotion || "情绪待补充",
    intensityText: intensity !== null ? `强度 ${intensity}/10` : "强度待补充",
    intensityMarks: Array.from({ length: 10 }, (_, index) => ({
      key: index,
      active: intensity !== null ? index < intensity : false,
    })),
  };
}

function isNetworkError(error) {
  return Boolean(error && (NETWORK_CODES.has(error.code) || error.status === 0));
}

Page({
  data: {
    loading: true,
    records: [],
    errorMessage: "",
    errorTitle: "",
    errorKind: "error",
  },

  onLoad() {
    if (!requireLogin({
      redirectUrl: "/pages/diary-history/index",
      message: "请先登录后再查看情绪记录。",
    })) {
      this.setData({ loading: false });
      return;
    }
    this._authorized = true;
    this.loadRecords();
  },

  onShow() {
    this._hidden = false;
    if (this._readSession && !isCurrentAuthSession(this._readSession)) {
      this.setData({ records: [], loading: false });
      return this.onLoad();
    }
    if (this._authorized && (this._loadedOnce || (this.data.loading && this._readSession))) {
      this.loadRecords();
    }
  },

  onHide() { this._hidden = true; },
  onUnload() { this._consentDisposed = true; this._hidden = true; },

  async loadRecords() {
    const session = captureAuthSession();
    this._readSession = session;
    const requestId = this._historyRequestId = (this._historyRequestId || 0) + 1;
    const isCurrent = () => !this._hidden && !this._consentDisposed && requestId === this._historyRequestId && isCurrentAuthSession(session);
    this.setData({ loading: true, errorMessage: "", errorTitle: "", errorKind: "error" });
    try {
      const result = await api.listDiaries({ limit: PAGE_LIMIT });
      if (!isCurrent()) return;
      const items = result && Array.isArray(result.items) ? result.items : [];
      this._loadedOnce = true;
      this.setData({ loading: false, records: items.map(formatRecord) });
    } catch (error) {
      if (!isCurrent()) return;
      const networkFailure = isNetworkError(error);
      this._loadedOnce = true;
      this.setData({
        loading: false,
        records: [],
        errorKind: networkFailure ? "network" : "error",
        errorTitle: networkFailure ? "网络连接不稳定" : "暂时无法读取记录",
        errorMessage: networkFailure
          ? "请检查网络后再试，已经保存的记录仍会保留。"
          : (error && error.message) || "数据没有成功加载，已经保存的记录不会因此丢失。",
      });
    }
  },

  retry() {
    this.loadRecords();
  },

  startDiary() {
    wx.navigateTo({ url: "/pages/diary-form/index" });
  },
});
