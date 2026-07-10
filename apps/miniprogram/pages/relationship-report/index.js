const { createSafeHomeApi } = require("../../services/api");
const { reportStatusLabel } = require("../../utils/relationshipStatus.generated");

const api = createSafeHomeApi();
const FEEDBACK_LABELS = {
  matches: "符合",
  does_not_match: "不符合",
  uncertain: "不确定",
};

function radarRows(report) {
  const dimensionLabels = Object.fromEntries((report.dimensions || []).map((row) => [row.code || row.key, row.label || row.code || row.key]));
  return (report.radar_features || []).map((row) => ({
    ...row,
    label: dimensionLabels[row.code] || row.code,
    valueText: Number(row.z_score).toFixed(2),
    style: `width:${Math.max(8, Math.min(100, (Number(row.z_score) + 2) * 25))}%;`,
  }));
}

function statusSteps(status) {
  const confirmed = ["confirmed", "sent", "updated"].includes(status);
  const sent = ["sent", "updated"].includes(status);
  return [
    { key: "generated", label: "已生成", state: "complete" },
    { key: "review", label: status === "pending_review" ? "待复核" : "已复核", state: status === "pending_review" ? "current" : "complete" },
    { key: "confirmed", label: "已确认", state: confirmed ? "complete" : "upcoming" },
    { key: "sent", label: "已发送", state: sent ? "complete" : "upcoming" },
  ];
}

function mechanismCards(report, feedbackRows) {
  const feedbackMap = Object.fromEntries((feedbackRows || []).map((row) => [Number(row.hypothesis_index), row.response]));
  const hypotheses = (((report.four_layer_profile || {}).mechanism || {}).hypotheses || []);
  return hypotheses.map((text, index) => ({
    index,
    text,
    response: feedbackMap[index] || "",
    responseText: FEEDBACK_LABELS[feedbackMap[index]] || "尚未核对",
  }));
}

function wrapText(text, maxChars = 28) {
  const value = String(text || "").trim();
  if (!value) return [];
  const lines = [];
  value.split("\n").forEach((paragraph) => {
    for (let index = 0; index < paragraph.length; index += maxChars) lines.push(paragraph.slice(index, index + maxChars));
  });
  return lines;
}

Page({
  data: {
    id: "",
    loading: true,
    errorMessage: "",
    record: null,
    report: null,
    radarRows: [],
    statusText: "",
    statusSteps: [],
    attentionNotice: "",
    mechanismCards: [],
    feedbackSavingIndex: -1,
    shareCanvasHeight: 1800,
    exporting: false,
  },

  onLoad(options) {
    const id = decodeURIComponent(options.id || "");
    this.setData({ id });
    this.loadReport();
  },

  async loadReport() {
    this.setData({ loading: true, errorMessage: "" });
    try {
      const record = await api.getRelationshipReport(this.data.id);
      const canShowProfile = ["confirmed", "sent", "updated"].includes(record.status);
      const report = {
        ...record.report,
        visible_profile_name: canShowProfile ? record.report.profile_name : "阶段性解释正在人工复核",
      };
      let attentionNotice = "";
      if (report.interpretation_status === "outlier") {
        attentionNotice = "本次位置与已有群体样本差异较大，暂不使用明确画像名，请优先结合你的真实经历人工核对。";
      } else if (report.interpretation_status === "low_confidence") {
        attentionNotice = "本次画像置信度较低，暂不把分数归纳成固定结论。";
      }
      this.setData({
        loading: false,
        record,
        report,
        radarRows: radarRows(report),
        statusText: reportStatusLabel(record.status),
        statusSteps: statusSteps(record.status),
        attentionNotice,
        mechanismCards: mechanismCards(report, record.hypothesis_feedback),
      });
    } catch (error) {
      this.setData({ loading: false, errorMessage: error.message || "报告暂时无法读取。" });
    }
  },

  async saveHypothesisFeedback(event) {
    const index = Number(event.currentTarget.dataset.index);
    const response = event.currentTarget.dataset.response;
    if (!Number.isInteger(index) || this.data.feedbackSavingIndex >= 0) return;
    this.setData({ feedbackSavingIndex: index });
    try {
      await api.saveRelationshipHypothesisFeedback(this.data.id, index, response);
      const mechanismCards = this.data.mechanismCards.map((item) => (
        item.index === index ? { ...item, response, responseText: FEEDBACK_LABELS[response] } : item
      ));
      this.setData({ mechanismCards });
      wx.showToast({ title: "已保存你的核对", icon: "success" });
    } catch (error) {
      wx.showToast({ title: error.message || "暂时没能保存", icon: "none" });
    } finally {
      this.setData({ feedbackSavingIndex: -1 });
    }
  },

  drawLongImage() {
    const report = this.data.report;
    const blocks = [
      { title: "阶段性位置", lines: wrapText(report.visible_profile_name, 24) },
      { title: "怎样理解", lines: wrapText(report.profile_description, 28).concat(wrapText(report.personalized_interpretation, 28)) },
      { title: "可以带去讨论的问题", lines: (report.suggested_assessment_questions || []).flatMap((item, index) => wrapText(`${index + 1}. ${item}`, 28)) },
      { title: "建议的探索任务", lines: (report.recommended_project_tasks || []).flatMap((item) => wrapText(`• ${item}`, 28)) },
      { title: "边界说明", lines: wrapText(report.boundary_notice, 28) },
    ];
    const totalLines = blocks.reduce((sum, block) => sum + block.lines.length + 2, 0);
    const height = Math.min(3900, Math.max(1500, 330 + totalLines * 48));
    this.setData({ shareCanvasHeight: height, exporting: true }, () => {
      const ctx = wx.createCanvasContext("reportShareCanvas", this);
      ctx.setFillStyle("#f7f4ee");
      ctx.fillRect(0, 0, 640, height);
      ctx.setFillStyle("#284b40");
      ctx.setFontSize(20);
      ctx.fillText("安心陪伴 · 关系探索", 42, 58);
      ctx.setFillStyle("#23312d");
      ctx.setFontSize(34);
      ctx.fillText(report.title || "阶段性关系探索报告", 42, 112);
      ctx.setFillStyle("#4f7c6b");
      ctx.setFontSize(22);
      ctx.fillText(this.data.statusText, 42, 154);
      ctx.setStrokeStyle("#d9e0dc");
      ctx.moveTo(42, 184);
      ctx.lineTo(598, 184);
      ctx.stroke();
      let y = 228;
      blocks.forEach((block) => {
        if (!block.lines.length || y > height - 120) return;
        ctx.setFillStyle("#284b40");
        ctx.setFontSize(23);
        ctx.fillText(block.title, 42, y);
        y += 42;
        ctx.setFillStyle("#344640");
        ctx.setFontSize(20);
        block.lines.forEach((line) => {
          if (y <= height - 90) ctx.fillText(line, 42, y);
          y += 38;
        });
        y += 26;
      });
      ctx.setFillStyle("#718078");
      ctx.setFontSize(17);
      ctx.fillText("本长图不含模型中心、内部字段或研究备注", 42, height - 42);
      ctx.draw(false, () => setTimeout(() => this.exportLongImage(height), 120));
    });
  },

  exportLongImage(height) {
    wx.canvasToTempFilePath({
      canvasId: "reportShareCanvas",
      width: 640,
      height,
      destWidth: 1280,
      destHeight: height * 2,
      fileType: "png",
      quality: 1,
      success: ({ tempFilePath }) => {
        this.setData({ exporting: false });
        api.trackProductEvent("relationship_report_downloaded", {
          action: "long_image",
          stage: "report",
          status: "success",
          source: "report",
        }).catch(() => {});
        wx.previewImage({ current: tempFilePath, urls: [tempFilePath] });
      },
      fail: () => {
        this.setData({ exporting: false });
        wx.showToast({ title: "长图生成失败，请稍后重试", icon: "none" });
      },
    }, this);
  },
});
