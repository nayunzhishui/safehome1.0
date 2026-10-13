const { createSafeHomeApi } = require("../../services/api");
const { requireLogin } = require("../../utils/authGuard");

const api = createSafeHomeApi();

const DISPLAY_LABELS = {
  general_support: "一般支持线索",
  high_demand_language: "要求较密集",
  repeated_prompting: "重复提醒",
  one_open_question: "一次只问一个开放问题",
  validation_before_advice: "先回应感受，再讨论办法",
  emotion_naming: "给情绪起一个名字",
  nonjudgmental_response: "减少判断，先描述事实",
};

function userLabel(value, fallback = "可继续观察的线索") {
  const key = String(value || "").trim();
  if (!key) return fallback;
  if (DISPLAY_LABELS[key]) return DISPLAY_LABELS[key];
  if (/^[a-z0-9_:-]+$/i.test(key)) return fallback;
  return key;
}

function formatPairs(items = []) {
  return items.map((item) => ({
    name: userLabel(item[0]),
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
      deltaText: item.score_delta === null || item.score_delta === undefined ? (item.count > 1 ? "暂不比较" : "暂无复测") : `${item.score_delta > 0 ? "+" : ""}${item.score_delta}`,
    });
  });
  return groups;
}

// “10月4日 – 10月10日”；日期缺失时退回原始文字。
function formatRange(start, end) {
  const toText = (value) => {
    const matched = String(value || "").match(/^(\d{4})-(\d{2})-(\d{2})/);
    return matched ? `${Number(matched[2])}月${Number(matched[3])}日` : String(value || "");
  };
  return `${toText(start)} – ${toText(end)}`;
}

// 近 7 天阶段反馈（原首页“阶段性反馈”，随设计移到本周复盘）。
const PROGRESS_STATUS_TEXT = {
  insufficient: "记录还不够",
  fluctuating: "仍在观察",
  converging: "开始形成线索",
  stable: "较稳定",
  low_confidence: "暂不归纳",
};

function formatProgressSummary(summary) {
  if (!summary || typeof summary !== "object") return null;
  return {
    status: summary.stability_status || "",
    statusText: PROGRESS_STATUS_TEXT[summary.stability_status] || "阶段复盘",
    summaryText: summary.summary_text || "记录还不够，先继续完成测评和练习。",
    nextAction: summary.next_action || "先完成一次测一测或一张训练卡。",
  };
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
    rangeText: "",
    statCells: [],
    commonRows: [],
    progressSummary: null,
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
      const [report, progress] = await Promise.all([
        api.getWeeklyReport(),
        api.getProgressSummary({ range: "7d" }).catch(() => null),
      ]);
      const frequentScenes = formatPairs(report.frequent_scenes || []);
      const frequentEmotions = formatPairs(report.frequent_emotions || []);
      const commonPatterns = formatPairs(report.common_patterns || []);
      const completedCards = report.completed_cards || [];
      this.setData({
        report,
        frequentScenes,
        frequentEmotions,
        commonPatterns,
        rangeText: formatRange(report.week_start, report.week_end),
        // 数字格直接展示接口计数，不做加总。
        statCells: [
          { label: "温度记录", value: String(report.thermometer_trend ? report.thermometer_trend.record_count || 0 : 0) },
          { label: "测评记录", value: String(report.assessment_trend ? report.assessment_trend.assessment_count || 0 : 0) },
          { label: "练习尝试", value: completedCards.length ? "已记" : "待记" },
          { label: "常见场景", value: `${frequentScenes.length} 类` },
          { label: "常见情绪", value: `${frequentEmotions.length} 类` },
          { label: "互动线索", value: `${commonPatterns.length} 条` },
        ],
        commonRows: [
          ...frequentScenes.map((item, index) => ({ ...item, kind: "场景", key: `scene-${index}` })),
          ...frequentEmotions.map((item, index) => ({ ...item, kind: "情绪", key: `emotion-${index}` })),
          ...commonPatterns.map((item, index) => ({ ...item, kind: "线索", key: `pattern-${index}` })),
        ],
        progressSummary: formatProgressSummary(progress),
        completedCardsText: (report.completed_cards || []).map((item) => userLabel(item, "已完成一项练习")).join("、"),
        profileTrendNamesText: ((report.profile_trend && report.profile_trend.profile_names) || [])
          .map((item) => `${item[0]} ${item[1]} 次`)
          .join("、"),
        assessmentNamesText: ((report.assessment_summary && report.assessment_summary.worksheet_names) || (report.assessment_trend && report.assessment_trend.worksheet_names) || [])
          .map((item) => `${item[0]} ${item[1]} 次`)
          .join("、"),
        dimensionGroups: formatDimensionSummaries((report.assessment_summary && report.assessment_summary.dimension_summaries) || []),
        recommendedCardsText: ((report.assessment_summary && report.assessment_summary.recommended_card_ids) || [])
          .map((item) => userLabel(item, "适合当前阶段的小练习"))
          .join("、"),
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
    const parts = [`平均强度 ${summary.avg_intensity ?? "-"}`];
    if (summary.avg_valence != null) parts.push(`愉悦 ${summary.avg_valence}`);
    if (summary.avg_arousal != null) parts.push(`唤起 ${summary.avg_arousal}`);
    if (summary.avg_control != null) parts.push(`可控 ${summary.avg_control}`);
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
    return `${userLabel(first.card_id, "本次练习")}：${deltaText}，${first.sample_note}`;
  },

  goHome() {
    wx.reLaunch({ url: "/pages/home/index" });
  },
});
