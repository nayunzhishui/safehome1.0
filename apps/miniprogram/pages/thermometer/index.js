const { createSafeHomeApi } = require("../../services/api");
const { formatTime, hitTestPoint, prepareLinePoints } = require("../../utils/chart");

const api = createSafeHomeApi();

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
    briefText: "",
    records: [],
    summary: { count: 0, min: null, max: null, avg: null },
    selectedPoint: null,
    loading: false,
    saving: false,
    errorMessage: "",
    boundaryNotice: "情绪温度计只用于自我观察和练习提示，不构成诊断或筛查。",
  },

  onLoad() {
    this.loadDay();
  },

  onReady() {
    this.drawCurve();
  },

  onIntensityChange(event) {
    this.setData({ intensityLevel: Number(event.detail.value) });
  },

  onBriefInput(event) {
    this.setData({ briefText: event.detail.value });
  },

  loadDay() {
    this.setData({ loading: true, errorMessage: "" });
    api
      .getEmotionThermometerDay({ date: this.data.date })
      .then((data) => {
        this.setData(
          {
            records: (data.items || []).map((item) => ({ ...item, timeLabel: formatTime(item.created_at) })),
            summary: data.summary || { count: 0, min: null, max: null, avg: null },
            boundaryNotice: data.boundary_notice || this.data.boundaryNotice,
            loading: false,
          },
          () => this.drawCurve(),
        );
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
    this.setData({ saving: true });
    api
      .createEmotionThermometer({
        intensity_level: this.data.intensityLevel,
        brief_text: this.data.briefText,
      })
      .then(() => {
        wx.showToast({ title: "已记录", icon: "success" });
        this.setData({ briefText: "", saving: false });
        this.loadDay();
      })
      .catch((error) => {
        this.setData({
          saving: false,
          errorMessage: error.message || "这次记录暂时没能保存，请检查网络后再试一次。",
        });
        wx.showToast({ title: error.message || "保存失败", icon: "none" });
      });
  },

  handleCanvasTap(event) {
    const touch = event.touches && event.touches[0];
    if (!touch || !this._chartPoints) {
      return;
    }
    const hit = hitTestPoint(this._chartPoints, touch.x, touch.y);
    if (hit) {
      this.setData({ selectedPoint: hit });
    }
  },

  drawCurve() {
    const records = this.data.records || [];
    wx.createSelectorQuery()
      .in(this)
      .select("#moodCurve")
      .fields({ node: true, size: true })
      .exec((res) => {
        const canvasInfo = res && res[0];
        if (canvasInfo && canvasInfo.node) {
          this.drawWithNodeCanvas(canvasInfo.node, canvasInfo.width || 320, canvasInfo.height || 180, records);
          return;
        }
        this.drawWithLegacyCanvas(records);
      });
  },

  drawWithNodeCanvas(canvas, width, height, records) {
    const dpr = wx.getSystemInfoSync().pixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    this.drawChartContext(ctx, width, height, records);
  },

  drawWithLegacyCanvas(records) {
    const ctx = wx.createCanvasContext("moodCurve", this);
    this.drawChartContext(ctx, 320, 180, records);
    ctx.draw();
  },

  drawChartContext(ctx, width, height, records) {
    const chart = prepareLinePoints(records, width, height, 26);
    this._chartPoints = chart.points;
    ctx.clearRect(0, 0, width, height);
    ctx.setFillStyle ? ctx.setFillStyle("#ffffff") : (ctx.fillStyle = "#ffffff");
    ctx.fillRect(0, 0, width, height);

    const stroke = ctx.setStrokeStyle ? ctx.setStrokeStyle.bind(ctx) : (value) => (ctx.strokeStyle = value);
    const fill = ctx.setFillStyle ? ctx.setFillStyle.bind(ctx) : (value) => (ctx.fillStyle = value);
    const lineWidth = ctx.setLineWidth ? ctx.setLineWidth.bind(ctx) : (value) => (ctx.lineWidth = value);

    stroke("#dfe5dc");
    lineWidth(1);
    chart.yTicks.forEach((tick) => {
      const y = chart.padding + (chart.height - chart.padding * 2) - ((tick - 1) / 9) * (chart.height - chart.padding * 2);
      ctx.beginPath();
      ctx.moveTo(chart.padding, y);
      ctx.lineTo(chart.width - chart.padding, y);
      ctx.stroke();
      fill("#78817b");
      ctx.setFontSize ? ctx.setFontSize(10) : (ctx.font = "10px sans-serif");
      ctx.fillText(String(tick), 6, y + 3);
    });

    if (!chart.points.length) {
      fill("#78817b");
      ctx.setFontSize ? ctx.setFontSize(13) : (ctx.font = "13px sans-serif");
      ctx.fillText("今天还没有温度记录", chart.padding, height / 2);
      return;
    }

    stroke("#4f7c6b");
    lineWidth(2);
    ctx.beginPath();
    chart.points.forEach((point, index) => {
      if (index === 0) {
        ctx.moveTo(point.x, point.y);
      } else {
        ctx.lineTo(point.x, point.y);
      }
    });
    ctx.stroke();

    chart.points.forEach((point) => {
      fill("#4f7c6b");
      ctx.beginPath();
      ctx.arc(point.x, point.y, 4, 0, Math.PI * 2);
      ctx.fill();
      fill("#78817b");
      ctx.setFontSize ? ctx.setFontSize(10) : (ctx.font = "10px sans-serif");
      ctx.fillText(point.label || "", point.x - 14, height - 8);
    });
  },
});
