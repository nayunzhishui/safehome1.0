const { createSafeHomeApi } = require("../../services/api");
const { requireLogin } = require("../../utils/authGuard");

const api = createSafeHomeApi();

function formatPairs(items = []) {
  return items.map((item) => ({
    name: item[0],
    count: item[1],
  }));
}

function formatDimensionSummaries(items = []) {
  const groups = [];
  const groupMap = {};
  items.forEach((item) => {
    const worksheetId = item.worksheet_id || "unknown";
    if (!groupMap[worksheetId]) {
      groupMap[worksheetId] = {
        worksheetId,
        worksheetTitle: item.worksheet_title || "支持性测评",
        dimensions: [],
      };
      groups.push(groupMap[worksheetId]);
    }
    groupMap[worksheetId].dimensions.push({
      key: item.key || item.label,
      label: item.label || item.key,
      direction: item.direction || "暂无变化",
      deltaText: item.score_delta === null || item.score_delta === undefined ? "暂无复测" : `${item.score_delta > 0 ? "+" : ""}${item.score_delta}`,
    });
  });
  return groups;
}

Page({
  data: {
    loading: true,
    errorMessage: "",
    report: null,
    frequentScenes: [],
    frequentEmotions: [],
    commonPatterns: [],
    completedCardsText: "",
    profileTrendNamesText: "",
    assessmentNamesText: "",
    dimensionGroups: [],
    recommendedCardsText: "",
    thermometerDetailText: "",
    trainingEffectivenessText: "",
  },

  onLoad() {
    if (!requireLogin({
      redirectUrl: "/pages/weekly-report/index",
      message: "请先登录后再查看周度复盘。",
    })) {
      this.setData({ loading: false });
      return;
    }
    this.loadReport();
  },

  async loadReport() {
    this.setData({ loading: true, errorMessage: "" });

    try {
      const report = await api.getWeeklyReport();
      this.setData({
        report,
        frequentScenes: formatPairs(report.frequent_scenes || []),
        frequentEmotions: formatPairs(report.frequent_emotions || []),
        commonPatterns: formatPairs(report.common_patterns || []),
        completedCardsText: (report.completed_cards || []).join("、"),
        profileTrendNamesText: ((report.profile_trend && report.profile_trend.profile_names) || [])
          .map((item) => `${item[0]} ${item[1]} 次`)
          .join("、"),
        assessmentNamesText: ((report.assessment_summary && report.assessment_summary.worksheet_names) || (report.assessment_trend && report.assessment_trend.worksheet_names) || [])
          .map((item) => `${item[0]} ${item[1]} 次`)
          .join("、"),
        dimensionGroups: formatDimensionSummaries((report.assessment_summary && report.assessment_summary.dimension_summaries) || []),
        recommendedCardsText: ((report.assessment_summary && report.assessment_summary.recommended_card_ids) || []).join("、"),
        thermometerDetailText: this.formatThermometerDetail(report.thermometer_summary || report.thermometer_trend),
        trainingEffectivenessText: this.formatTrainingEffectiveness(report.training_effectiveness_summary),
        loading: false,
      });
    } catch (error) {
      this.setData({
        loading: false,
        errorMessage: error.message || "周度复盘暂时没能加载，请检查网络后再试一次。",
      });
    }
  },

  refreshReport() {
    this.loadReport();
  },

  formatThermometerDetail(summary) {
    if (!summary || !summary.count) {
      return "本周还没有情绪温度记录。";
    }
    const parts = [`平均强度 ${summary.avg_intensity || "-"}`];
    if (summary.avg_valence) parts.push(`愉悦 ${summary.avg_valence}`);
    if (summary.avg_arousal) parts.push(`唤起 ${summary.avg_arousal}`);
    if (summary.avg_control) parts.push(`可控 ${summary.avg_control}`);
    return parts.join(" · ");
  },

  formatTrainingEffectiveness(summary) {
    const perCard = summary && summary.per_card_effectiveness ? summary.per_card_effectiveness : [];
    if (!perCard.length) {
      return "本周训练效用样本还不够，先记录一次练习前后感受。";
    }
    const first = perCard[0];
    const delta = first.average_intensity_delta;
    const deltaText = delta < 0 ? `平均下降 ${Math.abs(delta)} 分` : delta > 0 ? `平均上升 ${delta} 分` : "平均变化不大";
    return `${first.card_id}：${deltaText}，${first.sample_note}`;
  },

  goHome() {
    wx.reLaunch({ url: "/pages/home/index" });
  },
});
