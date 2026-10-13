const { createSafeHomeApi } = require("../../services/api");
const { formatTime } = require("../../utils/chart");
const { curveLayout } = require("../../utils/thermometer-curve");
const { requireLogin } = require("../../utils/authGuard");

const api = createSafeHomeApi();

// 曲线盒子与页面同宽（左右各留 40rpx 页边距）。
function curveBoxWidth() {
  let windowWidth = 375;
  try {
    const info = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync();
    windowWidth = Number(info.windowWidth) || windowWidth;
  } catch (error) {
    // 读不到窗口宽度时按 375 计算。
  }
  return windowWidth - (80 * windowWidth) / 750;
}

function recordMeta(item) {
  const parts = [];
  if (item.emotion_label) parts.push(item.emotion_label);
  if (item.valence_level) parts.push(`愉悦 ${item.valence_level}`);
  if (item.arousal_level) parts.push(`唤起 ${item.arousal_level}`);
  if (item.control_level) parts.push(`可控 ${item.control_level}`);
  return parts.join(" · ");
}

function todayKey() {
  const now = new Date();
  const year = now.getFullYear();
  const month = `${now.getMonth() + 1}`.padStart(2, "0");
  const day = `${now.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

Page({
  data: {
    date: todayKey(),
    intensityLevel: 5,
    intensityPercent: 50,
    valenceLevel: 5,
    arousalLevel: 5,
    controlLevel: 5,
    emotionLabel: "",
    briefText: "",
    records: [],
    recentRecords: [],
    curve: null,
    summary: { count: 0, min: null, max: null, avg: null },
    selectedPoint: null,
    loading: false,
    saving: false,
    errorMessage: "",
    saveError: "",
    receipt: null,
    boundaryNotice: "情绪温度计只用于自我观察和练习提示，不构成诊断或筛查。",
  },

  onLoad(options = {}) {
    // 首页点刻度会带上初始强度；只作为默认值，确认“记录一次”后才保存。
    const initial = Number(options.intensity);
    const startLevel = initial >= 1 && initial <= 10 ? initial : this.data.intensityLevel;
    if (!requireLogin({
      redirectUrl: initial >= 1 && initial <= 10 ? `/pages/thermometer/index?intensity=${Math.round(initial)}` : "/pages/thermometer/index",
      message: "请先登录后再记录情绪温度。",
    })) {
      return;
    }
    this.syncIntensityVisual(startLevel);
    this.loadDay();
  },

  clampIntensity(value) {
    return Math.max(1, Math.min(10, Math.round(Number(value) || 1)));
  },

  syncIntensityVisual(value) {
    const level = this.clampIntensity(value);
    this.setData({
      intensityLevel: level,
      intensityPercent: Math.round((level / 10) * 100),
    });
  },

  onIntensityChange(event) {
    this.syncIntensityVisual(event.detail.value);
  },

  decreaseIntensity() {
    this.syncIntensityVisual(this.data.intensityLevel - 1);
  },

  increaseIntensity() {
    this.syncIntensityVisual(this.data.intensityLevel + 1);
  },

  onValenceChange(event) {
    this.setData({ valenceLevel: this.clampIntensity(event.detail.value) });
  },

  onArousalChange(event) {
    this.setData({ arousalLevel: this.clampIntensity(event.detail.value) });
  },

  onControlChange(event) {
    this.setData({ controlLevel: this.clampIntensity(event.detail.value) });
  },

  onEmotionLabelInput(event) {
    this.setData({ emotionLabel: event.detail.value });
  },

  onBriefInput(event) {
    this.setData({ briefText: event.detail.value });
  },

  loadDay() {
    this.setData({ loading: true, errorMessage: "" });
    api
      .getEmotionThermometerDay({ date: this.data.date })
      .then((data) => {
        const records = (data.items || []).map((item) => ({ ...item, timeLabel: formatTime(item.created_at), metaText: recordMeta(item) }));
        this.setData({
          records,
          recentRecords: records.slice().reverse(),
          curve: curveLayout(records, curveBoxWidth()),
          selectedPoint: null,
          summary: data.summary || { count: 0, min: null, max: null, avg: null },
          boundaryNotice: data.boundary_notice || this.data.boundaryNotice,
          loading: false,
        });
      })
      .catch((error) => {
        this.setData({
          loading: false,
          errorMessage: error.message || "今日温度记录暂时没能读取，请检查网络后再试一次。",
        });
        wx.showToast({ title: error.message || "读取失败", icon: "none" });
      });
  },

  saveRecord() {
    if (this.data.saving) {
      return;
    }
    this.setData({ saving: true, saveError: "" });
    api
      .createEmotionThermometer({
        intensity_level: this.data.intensityLevel,
        valence_level: this.data.valenceLevel,
        arousal_level: this.data.arousalLevel,
        control_level: this.data.controlLevel,
        emotion_label: this.data.emotionLabel,
        brief_text: this.data.briefText,
      })
      .then((record) => {
        wx.showToast({ title: "已记录", icon: "success" });
        this.setData({
          briefText: "",
          emotionLabel: "",
          saving: false,
          receipt: record.receipt || null,
        });
        this.loadDay();
      })
      .catch((error) => {
        this.setData({
          saving: false,
          saveError: error.message || "这次记录暂时没能保存，请检查网络后再试一次。",
        });
        wx.showToast({ title: error.message || "保存失败", icon: "none" });
      });
  },

  openPractice() {
    wx.navigateTo({ url: "/pages/training-card/index" });
  },

  dismissReceipt() {
    this.setData({ receipt: null });
  },

  selectPoint(event) {
    const index = Number(event.currentTarget.dataset.index);
    const point = this.data.curve && this.data.curve.points[index];
    if (point) this.setData({ selectedPoint: point });
  },
});
