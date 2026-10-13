const { createSafeHomeApi } = require("../../services/api");
const { getAuthUser, requireLogin } = require("../../utils/authGuard");
const { reportStatusLabel } = require("../../utils/relationshipStatus.generated");

const api = createSafeHomeApi();
// lead 是当前步骤卡里的说明：在路径描述后补一句“现在可以怎么做”。
const STAGES = [
  { key: "assessment", number: 1, title: "起点测评", description: "看见本次关系体验的位置", lead: "先完成一份关系探索测一测，看见本次关系体验的位置。" },
  { key: "report", number: 2, title: "阶段性报告", description: "阅读维度、边界与待讨论问题", lead: "阅读维度、边界与待讨论问题。报告由研究者核对后发送给你。" },
  { key: "exploration", number: 3, title: "线上探索", description: "用绘画或句子留下愿意表达的部分", lead: "用绘画或句子留下愿意表达的部分。只写你愿意写的，随时可以停下。" },
  { key: "feedback", number: 4, title: "阶段性反馈", description: "线上探索后接收研究者的人工补充", lead: "线上探索后接收研究者的人工补充，送达后会出现在成长记录里。" },
  { key: "growth", number: 5, title: "连续记录", description: "用多次记录观察变化，不急于下结论", lead: "用多次记录观察变化，不急于下结论。每次只记一点也可以。" },
];
const SECONDARY_ACTIONS = [
  { key: "report", icon: "book", label: "阶段性报告", description: "查看状态与支持性解释" },
  { key: "drawing", icon: "pen", label: "关系隐喻绘画", description: "用线条记录此刻" },
  { key: "sentences", icon: "message", label: "情境句子补全", description: "只回答愿意回答的题" },
  { key: "growth", icon: "chart", label: "成长仪表盘", description: "查看曲线与时间轴" },
  { key: "assessment", icon: "compass", label: "再次测一测", description: "为后续变化保留新起点" },
];

function buildJourney(enrollment, growth) {
  if (!enrollment) return { currentIndex: 0, primaryAction: "assessment", primaryLabel: "先完成起点测评" };
  const reportStatus = enrollment.report_status || "";
  const hasReport = Boolean(enrollment.report_id);
  const tasksCount = Number(enrollment.tasks_count || 0);
  const hasResearcherFeedback = Boolean(
    growth && (growth.timeline || []).some((item) => item.type === "researcher_feedback"),
  );
  let currentIndex = 1;
  let primaryAction = "report";
  let primaryLabel = hasReport ? "查看阶段性报告" : "了解报告进度";

  if (["confirmed", "sent", "updated"].includes(reportStatus)) {
    currentIndex = tasksCount > 0 ? 3 : 2;
    primaryAction = tasksCount > 0 ? "report" : "drawing";
    primaryLabel = tasksCount > 0 ? "查看阶段性反馈进度" : "开始一次线上探索";
  }
  if (hasResearcherFeedback) {
    currentIndex = 4;
    primaryAction = "growth";
    primaryLabel = "继续记录变化";
  }

  return { currentIndex, primaryAction, primaryLabel };
}

function decorateStages(currentIndex) {
  return STAGES.map((stage, index) => ({
    ...stage,
    state: index < currentIndex ? "completed" : index === currentIndex ? "current" : "upcoming",
    timelineState: index < currentIndex ? "done" : index === currentIndex ? "current" : "upcoming",
    stateText: index < currentIndex ? "已完成" : index === currentIndex ? "当前步骤" : "稍后进行",
  }));
}

Page({
  data: {
    loading: true,
    submitting: false,
    consent: false,
    enrollment: null,
    errorMessage: "",
    roleBlocked: false,
    journeySteps: decorateStages(0),
    currentStepNumber: 1,
    currentActionState: "not_due",
    currentStageTitle: "起点测评",
    currentStageLead: STAGES[0].lead,
    primaryAction: "assessment",
    primaryLabel: "先完成起点测评",
    reportStatusText: "尚未生成",
    secondaryActions: [],
  },

  async onShow() {
    if (!requireLogin({ redirectUrl: "/pages/relationship-pilot/index" })) return;
    const user = getAuthUser();
    const showcase = await api.getShowcaseAccess().catch(() => ({ enabled: false }));
    if (!showcase.enabled && (!user || !["student", "admin"].includes(user.role))) {
      this.setData({ loading: false, roleBlocked: true, errorMessage: "" });
      return;
    }
    this.setData({ roleBlocked: false });
    this.loadEnrollment();
  },

  async loadEnrollment() {
    this.setData({ loading: true, errorMessage: "" });
    try {
      const payload = await api.listRelationshipEnrollments();
      const enrollment = (payload.items || [])[0] || null;
      let growth = null;
      if (enrollment) {
        try {
          growth = await api.getRelationshipGrowth();
        } catch (error) {
          growth = null;
        }
      }
      const journey = buildJourney(enrollment, growth);
      // 其它入口固定五项（Figma 665:2685），和当前步骤按钮重复的一项也保留，方便按习惯找到。
      const secondaryActions = enrollment ? SECONDARY_ACTIONS : [];
      this.setData({
        loading: false,
        enrollment,
        journeySteps: decorateStages(journey.currentIndex),
        currentStepNumber: journey.currentIndex + 1,
        currentActionState: enrollment && ["confirmed", "sent", "updated"].includes(enrollment.report_status) ? "ready" : "not_due",
        currentStageTitle: STAGES[journey.currentIndex].title,
        currentStageLead: STAGES[journey.currentIndex].lead,
        primaryAction: journey.primaryAction,
        primaryLabel: journey.primaryLabel,
        // “已发送 / 已更新”单独放在卡片角上不知道指什么，补上“报告”（设计稿：报告已发送）。
        reportStatusText: enrollment && enrollment.report_status
          ? `${["sent", "updated"].includes(enrollment.report_status) ? "报告" : ""}${reportStatusLabel(enrollment.report_status)}`
          : "尚未生成",
        secondaryActions,
      });
    } catch (error) {
      this.setData({ loading: false, errorMessage: error.message || "暂时没能读取试点记录。" });
    }
  },

  toggleConsent(event) {
    this.setData({ consent: (event.detail.value || []).includes("agree") });
  },

  // 点说明文字也能勾选，和登录页协议勾选一致。
  flipConsent() {
    this.setData({ consent: !this.data.consent });
  },

  async enroll() {
    if (!this.data.consent) {
      wx.showToast({ title: "请先阅读并勾选研究用途说明", icon: "none" });
      return;
    }
    this.setData({ submitting: true, errorMessage: "" });
    try {
      await api.createRelationshipEnrollment({ research_consent: true });
      wx.showToast({ title: "已进入试点", icon: "success" });
      await this.loadEnrollment();
    } catch (error) {
      this.setData({ errorMessage: error.code === "assessment_required" ? "请先完成一份关系探索测一测，再回来报名。" : error.message || "报名暂未完成。" });
    } finally {
      this.setData({ submitting: false });
    }
  },

  runPrimaryAction() {
    this.runActionByKey(this.data.primaryAction, "primary_action");
  },

  runSecondaryAction(event) {
    this.runActionByKey(event.currentTarget.dataset.action, "secondary_action");
  },

  runActionByKey(action, source) {
    const currentStage = (this.data.journeySteps || []).find((item) => item.state === "current");
    api.trackProductEvent("relationship_entry_clicked", {
      action,
      stage: currentStage ? currentStage.key : action,
      source,
    }).catch(() => {});
    const actions = {
      assessment: () => this.goAssessment(),
      report: () => this.openReport(),
      drawing: () => this.openDrawing(),
      sentences: () => this.openSentences(),
      growth: () => this.openGrowth(),
    };
    if (actions[action]) actions[action]();
  },

  goAssessment() {
    wx.navigateTo({ url: "/pages/assessment/index?audience_class=student&query=%E5%85%B3%E7%B3%BB" });
  },

  async openReport() {
    if (!this.data.enrollment) return;
    if (!this.data.enrollment.report_id) {
      wx.showToast({ title: "报告将由研究者生成并核对", icon: "none" });
      return;
    }
    wx.navigateTo({ url: `/pages/relationship-report/index?id=${encodeURIComponent(this.data.enrollment.report_id)}` });
  },

  openDrawing() {
    wx.navigateTo({ url: `/pages/relationship-task/index?type=relationship_drawing&enrollment_id=${encodeURIComponent(this.data.enrollment.id)}` });
  },

  openSentences() {
    wx.navigateTo({ url: `/pages/relationship-task/index?type=sentence_completion&enrollment_id=${encodeURIComponent(this.data.enrollment.id)}` });
  },

  openGrowth() {
    wx.navigateTo({
      url: `/pages/relationship-growth/index?detail=1&enrollment_id=${encodeURIComponent(this.data.enrollment.id)}`,
    });
  },
});
